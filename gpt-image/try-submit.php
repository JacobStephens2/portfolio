<?php
/**
 * Live try for gpt-image: Turnstile → newsletter subscribe → OpenAI generate → metrics log.
 *
 * Deep public module: one POST interface. Secrets from /private/.env (gitignored).
 * Trial log: /var/lib/gpt-image/trials.jsonl
 */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
// Image generation often exceeds PHP's default 30s max_execution_time.
@set_time_limit(200);
@ini_set('max_execution_time', '200');

const TRIALS_PATH = '/var/lib/gpt-image/trials.jsonl';
const MAX_PROMPT = 500;
const MIN_PROMPT = 3;
const MAX_EMAIL = 254;
const MAX_TURNSTILE = 2048;
const MAX_POST_FIELDS = 16;
const IP_LIMIT = 5;
const IP_WINDOW = 3600;
const EMAIL_LIMIT = 3;
const EMAIL_WINDOW = 86400;

function respond(bool $ok, string $message, array $extra = [], int $code = 200): void {
    http_response_code($code);
    // Never include raw user input in message; only fixed strings + server-built extras.
    echo json_encode(
        array_merge(['ok' => $ok, 'message' => $message], $extra),
        JSON_UNESCAPED_SLASHES | JSON_INVALID_UTF8_SUBSTITUTE
    );
    exit;
}

/**
 * Coerce a POST field to a clean string: scalar only, no null bytes, trim.
 */
function post_string(string $key, int $maxLen = 0): string {
    if (!array_key_exists($key, $_POST)) {
        return '';
    }
    $raw = $_POST[$key];
    if (is_array($raw) || is_object($raw)) {
        return '';
    }
    $s = (string) $raw;
    // Strip NULs and other C0 controls except tab/newline/CR (handled later per field).
    $s = str_replace("\0", '', $s);
    if (!mb_check_encoding($s, 'UTF-8')) {
        $s = mb_convert_encoding($s, 'UTF-8', 'UTF-8');
    }
    $s = trim($s);
    if ($maxLen > 0 && mb_strlen($s) > $maxLen) {
        $s = mb_substr($s, 0, $maxLen);
    }
    return $s;
}

/**
 * Email: lowercase, length-capped, no CR/LF (header injection), FILTER_VALIDATE_EMAIL.
 * Returns '' if invalid.
 */
function sanitize_email(string $email): string {
    $email = strtolower(trim($email));
    $email = str_replace(["\0", "\r", "\n", "\t", ' '], '', $email);
    if ($email === '' || mb_strlen($email) > MAX_EMAIL) {
        return '';
    }
    // Only allow a conservative character set (rejects quotes, angle brackets, etc.).
    if (!preg_match('/^[a-z0-9.!#$%&\'*+\/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i', $email)) {
        return '';
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return '';
    }
    return $email;
}

/**
 * Image prompt: printable text only, normalized whitespace, length bounds.
 * Returns [prompt, error_code|null].
 */
function sanitize_prompt(string $prompt): array {
    $prompt = str_replace("\0", '', $prompt);
    // Drop C0/C1 controls except tab/newline; map newlines/tabs to spaces.
    $prompt = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $prompt) ?? '';
    $prompt = str_replace(["\r", "\n", "\t"], ' ', $prompt);
    // Collapse runs of whitespace.
    $prompt = preg_replace('/\s+/u', ' ', $prompt) ?? '';
    $prompt = trim($prompt);
    if ($prompt === '') {
        return ['', 'empty'];
    }
    $len = mb_strlen($prompt);
    if ($len < MIN_PROMPT) {
        return ['', 'too_short'];
    }
    if ($len > MAX_PROMPT) {
        return ['', 'too_long'];
    }
    // Reject prompts that are almost entirely non-letter/number (noise/binary paste).
    $alnum = preg_match_all('/[\p{L}\p{N}]/u', $prompt);
    if ($alnum !== false && $alnum < 2) {
        return ['', 'invalid'];
    }
    return [$prompt, null];
}

/**
 * Turnstile tokens are opaque; allow a safe base64url-ish charset and length.
 */
function sanitize_turnstile(string $token): string {
    $token = trim(str_replace("\0", '', $token));
    if ($token === '' || strlen($token) > MAX_TURNSTILE) {
        return '';
    }
    // Cloudflare tokens are opaque; allow base64 / base64url / dotted segments.
    if (!preg_match('/^[A-Za-z0-9._\-+\/]+=*$/', $token)) {
        return '';
    }
    return $token;
}

function sanitize_ip(string $ip): string {
    $ip = trim($ip);
    if ($ip === '' || $ip === 'unknown') {
        return 'unknown';
    }
    // XFF may be IPv4/IPv6; only trust if it validates.
    if (filter_var($ip, FILTER_VALIDATE_IP)) {
        return $ip;
    }
    return 'unknown';
}

function load_env(string $path): array {
    $env = [];
    if (!is_readable($path)) {
        return $env;
    }
    foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
            continue;
        }
        [$k, $v] = explode('=', $line, 2);
        $k = trim($k);
        $v = trim($v);
        if (strlen($v) >= 2
            && (($v[0] === '"' && substr($v, -1) === '"') || ($v[0] === "'" && substr($v, -1) === "'"))) {
            $v = substr($v, 1, -1);
        }
        $env[$k] = $v;
    }
    return $env;
}

function client_ip(): string {
    $xff = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? '';
    if (is_string($xff) && $xff !== '') {
        $first = trim(explode(',', $xff)[0]);
        $first = sanitize_ip($first);
        if ($first !== 'unknown') {
            return $first;
        }
    }
    return sanitize_ip((string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
}

function log_trial(array $event): void {
    $event['ts'] = $event['ts'] ?? time();
    $dir = dirname(TRIALS_PATH);
    if (!is_dir($dir)) {
        @mkdir($dir, 0775, true);
    }
    $line = json_encode($event, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($line === false) {
        return;
    }
    @file_put_contents(TRIALS_PATH, $line . "\n", FILE_APPEND | LOCK_EX);
}

function rate_hits(string $key, int $window): array {
    $file = sys_get_temp_dir() . '/sp_gptimage_rl_' . md5($key) . '.json';
    $now = time();
    $hits = [];
    if (is_readable($file)) {
        $hits = json_decode((string) file_get_contents($file), true) ?: [];
    }
    $hits = array_values(array_filter($hits, static fn($t) => is_int($t) && $t > $now - $window));
    return [$file, $hits, $now];
}

function rate_record(string $file, array $hits, int $now): void {
    $hits[] = $now;
    @file_put_contents($file, json_encode($hits), LOCK_EX);
}

function turnstile_ok(string $secret, string $token, string $ip): bool {
    $params = [
        'secret'   => $secret,
        'response' => $token,
    ];
    if ($ip !== '') {
        $params['remoteip'] = $ip;
    }
    $raw = @file_get_contents(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        false,
        stream_context_create([
            'http' => [
                'method'  => 'POST',
                'header'  => "Content-Type: application/x-www-form-urlencoded\r\n",
                'content' => http_build_query($params),
                'timeout' => 10,
            ],
        ])
    );
    $j = json_decode((string) $raw, true);
    return is_array($j) && ($j['success'] ?? false) === true;
}

function newsletter_add(string $url, string $token, string $email): array {
    $url = rtrim($url, '/') . '/admin/add';
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . $token,
            'Content-Type: application/json',
        ],
        CURLOPT_POSTFIELDS     => json_encode(['email' => $email, 'list' => 'stephens']),
        CURLOPT_TIMEOUT        => 10,
    ]);
    $resp = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    $body = json_decode((string) $resp, true);
    if (!is_array($body)) {
        $body = [];
    }
    return [$status, $body, $err];
}

function openai_generate(string $apiKey, string $prompt): array {
    $payload = json_encode([
        'model'          => 'gpt-image-2',
        'prompt'         => $prompt,
        'quality'        => 'medium',
        'size'           => '1024x1024',
        'output_format'  => 'png',
    ]);
    $ch = curl_init('https://api.openai.com/v1/images/generations');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . $apiKey,
            'Content-Type: application/json',
        ],
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_TIMEOUT        => 180,
    ]);
    $resp = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    $body = json_decode((string) $resp, true);
    if (!is_array($body)) {
        $body = [];
    }
    return [$status, $body, $err];
}

/**
 * Estimate USD cost from Images API usage tokens.
 * Rates: OpenAI standard-tier gpt-image-2 per 1M tokens (text in $5, image in $8, image out $30).
 * The API does not return a dollar amount; this matches the gpt-image CLI.
 */
function estimate_cost_from_usage(?array $usage): array {
    $empty = [
        'cost_usd' => null,
        'input_tokens' => 0,
        'output_tokens' => 0,
        'text_input' => 0,
        'image_input' => 0,
        'image_output' => 0,
        'text_output' => 0,
        'cost_line' => '',
    ];
    if (!is_array($usage)) {
        return $empty;
    }
    $input = (int) ($usage['input_tokens'] ?? 0);
    $output = (int) ($usage['output_tokens'] ?? 0);
    $inDet = $usage['input_tokens_details'] ?? [];
    $outDet = $usage['output_tokens_details'] ?? [];
    $textIn = (int) ($inDet['text_tokens'] ?? $input);
    $imgIn = (int) ($inDet['image_tokens'] ?? 0);
    $imgOut = (int) ($outDet['image_tokens'] ?? $output);
    $textOut = (int) ($outDet['text_tokens'] ?? 0);

    // gpt-image-2 standard rates per 1M tokens
    $cost = (
        $textIn * 5.0
        + $imgIn * 8.0
        + $imgOut * 30.0
        + $textOut * 0.0
    ) / 1_000_000.0;

    $parts = [sprintf('~$%.4f est.', $cost)];
    if ($input || $output) {
        $parts[] = "tokens in={$input} out={$output}";
        $detail = [];
        if ($textIn) {
            $detail[] = "text_in={$textIn}";
        }
        if ($imgIn) {
            $detail[] = "img_in={$imgIn}";
        }
        if ($imgOut) {
            $detail[] = "img_out={$imgOut}";
        }
        if ($textOut) {
            $detail[] = "text_out={$textOut}";
        }
        if ($detail) {
            $parts[] = '(' . implode(', ', $detail) . ')';
        }
    }

    return [
        'cost_usd' => $cost,
        'input_tokens' => $input,
        'output_tokens' => $output,
        'text_input' => $textIn,
        'image_input' => $imgIn,
        'image_output' => $imgOut,
        'text_output' => $textOut,
        'cost_line' => implode(' · ', $parts),
    ];
}

// --- Entry -------------------------------------------------------------------

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    respond(false, 'Method not allowed.', [], 405);
}

// Reject oversized or non-form posts early (DoS / weird clients).
$contentLen = (int) ($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($contentLen > 64 * 1024) {
    respond(false, 'Request too large.', [], 413);
}
if (!is_array($_POST) || count($_POST) > MAX_POST_FIELDS) {
    respond(false, 'Invalid form submission.', [], 400);
}

$env = load_env(dirname(__DIR__) . '/private/.env');
$ip = client_ip();
$started = microtime(true);

// Honeypot: look successful, do nothing spendy. Do not log the honeypot value.
if (post_string('website_url', 200) !== '') {
    log_trial([
        'event' => 'honeypot',
        'ip' => $ip,
        'ok' => true,
    ]);
    respond(true, 'Almost there - check your email to confirm, then try again.');
}

$emailRaw = post_string('email', MAX_EMAIL + 32);
$promptRaw = post_string('prompt', MAX_PROMPT + 64);
$tsToken = sanitize_turnstile(post_string('cf-turnstile-response', MAX_TURNSTILE + 32));

$email = sanitize_email($emailRaw);
[$prompt, $promptErr] = sanitize_prompt($promptRaw);

// Log only sanitized values (never raw POST).
$baseEvent = [
    'event' => 'try',
    'ip' => $ip,
    'email' => $email !== '' ? $email : mb_substr(preg_replace('/[^\x20-\x7E]/', '', $emailRaw) ?? '', 0, 64),
    'prompt' => $prompt !== '' ? $prompt : mb_substr(preg_replace('/[^\x20-\x7E]/', '', $promptRaw) ?? '', 0, 80),
    'prompt_len' => mb_strlen($prompt !== '' ? $prompt : $promptRaw),
];

if ($email === '' && ($prompt === '' && ($promptErr === null || $promptErr === 'empty'))) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'missing_fields']);
    respond(false, 'Enter an image description and your email to continue.');
}
if ($email === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'bad_email']);
    respond(false, 'Please enter a valid email address.');
}
if ($promptErr === 'too_short') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'prompt_too_short']);
    respond(false, 'Prompt is too short - use at least ' . MIN_PROMPT . ' characters.');
}
if ($promptErr === 'too_long') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'prompt_too_long']);
    respond(false, 'Keep the prompt under ' . MAX_PROMPT . ' characters.');
}
if ($promptErr === 'invalid') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'prompt_invalid']);
    respond(false, 'That prompt does not look like usable text. Try a short plain-language description.');
}
if ($promptErr === 'empty' || $prompt === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'missing_prompt']);
    respond(false, 'Enter an image description to continue.');
}

[$ipFile, $ipHits, $now] = rate_hits('ip:' . $ip, IP_WINDOW);
if (count($ipHits) >= IP_LIMIT) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'rate_ip']);
    respond(false, 'Too many tries from this connection. Please wait an hour and try again.', [], 429);
}
[$emFile, $emHits] = rate_hits('email:' . $email, EMAIL_WINDOW);
if (count($emHits) >= EMAIL_LIMIT) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'rate_email']);
    respond(false, 'This email has reached the free trial limit for today (3 images). Try again tomorrow.', [], 429);
}

$tsSecret = $env['TURNSTILE_SECRET'] ?? '';
if ($tsSecret === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'config_turnstile']);
    respond(false, 'The form is not fully configured yet. Please email jacob@stephens.page.', [], 500);
}
if ($tsToken === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'turnstile_missing']);
    respond(false, 'Please complete the verification challenge and try again.');
}
// Only pass a validated IP to Turnstile; unknown skips remoteip.
$tsIp = $ip !== 'unknown' ? $ip : '';
if (!turnstile_ok($tsSecret, $tsToken, $tsIp)) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'turnstile_fail']);
    respond(false, 'Verification failed. Please try the challenge again.');
}

// Record attempt against rate limits only after Turnstile (blocks pure spam burn).
rate_record($ipFile, $ipHits, $now);
rate_record($emFile, $emHits, $now);

$nlUrl = $env['NEWSLETTER_ADMIN_URL'] ?? 'http://127.0.0.1:3462';
$nlTok = $env['NEWSLETTER_ADMIN_TOKEN'] ?? '';
$already = false;
if ($nlTok === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'config_newsletter']);
    respond(false, 'Newsletter is not configured yet. Please email jacob@stephens.page.', [], 500);
}
[$nlStatus, $nlBody, $nlErr] = newsletter_add($nlUrl, $nlTok, $email);
if ($nlStatus < 200 || $nlStatus >= 300 || !($nlBody['ok'] ?? false)) {
    error_log('gpt-image try: newsletter add failed status=' . $nlStatus . ' err=' . $nlErr . ' body=' . substr(json_encode($nlBody), 0, 200));
    log_trial($baseEvent + ['ok' => false, 'error' => 'newsletter_fail', 'http' => $nlStatus]);
    respond(false, 'Could not complete newsletter signup. Please try again in a moment.', [], 502);
}
$msg = (string) ($nlBody['message'] ?? '');
if (stripos($msg, 'already') !== false) {
    $already = true;
}

$apiKey = $env['OPENAI_API_KEY'] ?? '';
if ($apiKey === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'config_openai', 'subscribed' => true]);
    respond(false, 'Image generation is not configured yet. Your newsletter signup was recorded - thank you.', [], 500);
}

[$oStatus, $oBody, $oErr] = openai_generate($apiKey, $prompt);
$latencyMs = (int) round((microtime(true) - $started) * 1000);
$latencySec = max(1, (int) round($latencyMs / 1000));
$b64 = $oBody['data'][0]['b64_json'] ?? null;
$cost = estimate_cost_from_usage(is_array($oBody['usage'] ?? null) ? $oBody['usage'] : null);

if ($oStatus < 200 || $oStatus >= 300 || !is_string($b64) || $b64 === '') {
    $apiMsg = $oBody['error']['message'] ?? $oErr ?: 'unknown';
    error_log('gpt-image try: openai fail status=' . $oStatus . ' msg=' . substr((string) $apiMsg, 0, 300));
    log_trial($baseEvent + [
        'ok' => false,
        'error' => 'openai_fail',
        'http' => $oStatus,
        'latency_ms' => $latencyMs,
        'subscribed' => true,
        'already_subscribed' => $already,
        'cost_usd' => $cost['cost_usd'],
        'input_tokens' => $cost['input_tokens'],
        'output_tokens' => $cost['output_tokens'],
    ]);
    respond(false, 'Image generation failed. Your newsletter signup was recorded - please try a different prompt later.', [], 502);
}

log_trial($baseEvent + [
    'ok' => true,
    'latency_ms' => $latencyMs,
    'subscribed' => true,
    'already_subscribed' => $already,
    'model' => 'gpt-image-2',
    'quality' => 'medium',
    'size' => '1024x1024',
    'cost_usd' => $cost['cost_usd'],
    'input_tokens' => $cost['input_tokens'],
    'output_tokens' => $cost['output_tokens'],
    'text_input' => $cost['text_input'],
    'image_output' => $cost['image_output'],
]);

$subNote = $already
    ? "You're already on the list - thanks for reading."
    : "You're on Jacob Stephens' blog newsletter (unsubscribe anytime from any email).";

$costLine = $cost['cost_line'] !== ''
    ? $cost['cost_line'] . " · {$latencySec}s"
    : "{$latencySec}s";

// Only return b64 if it is well-formed base64 (reject garbage / injection).
if (!preg_match('/^[A-Za-z0-9+\/]+=*$/', $b64) || strlen($b64) < 64) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'bad_image_payload', 'latency_ms' => $latencyMs]);
    respond(false, 'Image generation returned an unreadable result. Please try again.', [], 502);
}

respond(true, "Wrote trial.png · {$costLine} · {$subNote}", [
    'image_b64' => $b64,
    'already_subscribed' => $already,
    'latency_ms' => $latencyMs,
    'output' => 'trial.png',
    'cost_usd' => $cost['cost_usd'],
    'cost_line' => $costLine,
    'input_tokens' => $cost['input_tokens'],
    'output_tokens' => $cost['output_tokens'],
    'usage' => [
        'text_input' => $cost['text_input'],
        'image_input' => $cost['image_input'],
        'image_output' => $cost['image_output'],
        'text_output' => $cost['text_output'],
    ],
]);
