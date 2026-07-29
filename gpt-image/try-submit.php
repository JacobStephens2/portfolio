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
const IP_LIMIT = 5;
const IP_WINDOW = 3600;
const EMAIL_LIMIT = 3;
const EMAIL_WINDOW = 86400;

function respond(bool $ok, string $message, array $extra = [], int $code = 200): void {
    http_response_code($code);
    echo json_encode(array_merge(['ok' => $ok, 'message' => $message], $extra));
    exit;
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
    if ($xff !== '') {
        $first = trim(explode(',', $xff)[0]);
        if ($first !== '') {
            return $first;
        }
    }
    return $_SERVER['REMOTE_ADDR'] ?? 'unknown';
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
    $raw = @file_get_contents(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        false,
        stream_context_create([
            'http' => [
                'method'  => 'POST',
                'header'  => "Content-Type: application/x-www-form-urlencoded\r\n",
                'content' => http_build_query([
                    'secret'   => $secret,
                    'response' => $token,
                    'remoteip' => $ip,
                ]),
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

// --- Entry -------------------------------------------------------------------

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    respond(false, 'Method not allowed.', [], 405);
}

$env = load_env(dirname(__DIR__) . '/private/.env');
$ip = client_ip();
$started = microtime(true);

// Honeypot: look successful, do nothing spendy.
if (trim($_POST['website_url'] ?? '') !== '') {
    log_trial([
        'event' => 'honeypot',
        'ip' => $ip,
        'ok' => true,
    ]);
    respond(true, 'Almost there - check your email to confirm, then try again.');
}

$email = strtolower(trim($_POST['email'] ?? ''));
$prompt = trim($_POST['prompt'] ?? '');
$tsToken = trim($_POST['cf-turnstile-response'] ?? '');

$baseEvent = [
    'event' => 'try',
    'ip' => $ip,
    'email' => $email,
    'prompt' => mb_substr($prompt, 0, MAX_PROMPT),
    'prompt_len' => mb_strlen($prompt),
];

if ($email === '' || $prompt === '') {
    log_trial($baseEvent + ['ok' => false, 'error' => 'missing_fields']);
    respond(false, 'Enter an image description and your email to continue.');
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'bad_email']);
    respond(false, 'Please enter a valid email address.');
}
if (mb_strlen($prompt) > MAX_PROMPT) {
    log_trial($baseEvent + ['ok' => false, 'error' => 'prompt_too_long']);
    respond(false, 'Keep the prompt under ' . MAX_PROMPT . ' characters.');
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
if (!turnstile_ok($tsSecret, $tsToken, $ip)) {
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
$b64 = $oBody['data'][0]['b64_json'] ?? null;

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
]);

$subNote = $already
    ? "You're already on the list - thanks for reading."
    : "You're on Jacob Stephens' blog newsletter (unsubscribe anytime from any email).";

respond(true, "Wrote trial.png · {$subNote}", [
    'image_b64' => $b64,
    'already_subscribed' => $already,
    'latency_ms' => $latencyMs,
    'output' => 'trial.png',
]);
