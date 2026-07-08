<?php
/**
 * Newsletter subscribe handler for stephens.page/blog.
 * Double opt-in: records a pending subscriber and emails a confirmation link.
 * Verifies a Cloudflare Turnstile token, honeypot, and per-IP rate limit first.
 * Returns JSON: {ok, message}.
 */

declare(strict_types=1);
require __DIR__ . '/newsletter-lib.php';

header('Content-Type: application/json');

function nl_respond(bool $ok, string $message, int $code = 200): void
{
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $message]);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    nl_respond(false, 'Method not allowed.', 405);
}

$env = nl_env();
$ip  = $_SERVER['REMOTE_ADDR'] ?? 'unknown';

// --- Honeypot: silently accept and drop bots --------------------------------
if (trim($_POST['website_url'] ?? '') !== '') {
    nl_respond(true, 'Thanks! Please check your email to confirm.');
}

// --- Rate limit: 5 subscribe attempts per hour per IP -----------------------
$rlFile = sys_get_temp_dir() . '/sp_news_rl_' . md5($ip) . '.json';
$now    = time();
$hits   = [];
if (is_readable($rlFile)) {
    $hits = json_decode((string) file_get_contents($rlFile), true) ?: [];
}
$hits = array_values(array_filter($hits, static fn($t) => is_int($t) && $t > $now - 3600));
if (count($hits) >= 5) {
    nl_respond(false, 'Too many attempts from this connection. Please wait a bit and try again.', 429);
}

// --- Validate email ---------------------------------------------------------
$email = trim($_POST['email'] ?? '');
if ($email === '') {
    nl_respond(false, 'Please enter your email address.');
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || mb_strlen($email) > 254) {
    nl_respond(false, 'Please enter a valid email address.');
}

// --- Verify Cloudflare Turnstile --------------------------------------------
$tsSecret = $env['TURNSTILE_SECRET'] ?? '';
if ($tsSecret === '') {
    nl_respond(false, 'The form is not fully configured yet. Please email jacob@stephens.page.', 500);
}
$token = $_POST['cf-turnstile-response'] ?? '';
if ($token === '') {
    nl_respond(false, 'Please complete the verification challenge and try again.');
}
$verifyRaw = @file_get_contents(
    'https://challenges.cloudflare.com/turnstile/v0/siteverify',
    false,
    stream_context_create([
        'http' => [
            'method'  => 'POST',
            'header'  => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => http_build_query(['secret' => $tsSecret, 'response' => $token, 'remoteip' => $ip]),
            'timeout' => 10,
        ],
    ])
);
$verify = json_decode((string) $verifyRaw, true);
if (!is_array($verify) || ($verify['success'] ?? false) !== true) {
    nl_respond(false, 'Verification failed. Please try the challenge again.');
}

// --- Record this attempt against the rate limit -----------------------------
$hits[] = $now;
@file_put_contents($rlFile, json_encode($hits), LOCK_EX);

// --- Upsert the subscriber --------------------------------------------------
try {
    $db  = nl_db();
    $row = $db->prepare('SELECT id, status FROM subscribers WHERE email = ? COLLATE NOCASE');
    $row->execute([$email]);
    $existing = $row->fetch(PDO::FETCH_ASSOC);

    if ($existing && $existing['status'] === 'confirmed') {
        nl_respond(true, "You're already subscribed - thanks for reading.");
    }

    $confirmToken = nl_token();
    if ($existing) {
        // pending or previously unsubscribed: reset to pending with a fresh token
        $upd = $db->prepare(
            'UPDATE subscribers
                SET status = \'pending\', confirm_token = ?, unsubscribed_at = NULL, ip = ?
              WHERE id = ?'
        );
        $upd->execute([$confirmToken, $ip, $existing['id']]);
    } else {
        $ins = $db->prepare(
            'INSERT INTO subscribers (email, status, confirm_token, unsubscribe_token, created_at, ip)
             VALUES (?, \'pending\', ?, ?, ?, ?)'
        );
        $ins->execute([$email, $confirmToken, nl_token(), $now, $ip]);
    }
} catch (Throwable $e) {
    error_log('newsletter-subscribe: ' . $e->getMessage());
    nl_respond(false, 'Something went wrong on our end. Please try again later.', 500);
}

// --- Send the double opt-in confirmation email ------------------------------
$confirmUrl  = nl_confirm_url($confirmToken);
$safeConfirm = htmlspecialchars($confirmUrl, ENT_QUOTES, 'UTF-8');
$html = <<<HTML
<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:16px;line-height:1.6;color:#181512;max-width:520px;">
  <p>Thanks for subscribing to <strong>Jacob Stephens' blog</strong>.</p>
  <p>Please confirm your email address to start receiving new posts:</p>
  <p style="margin:24px 0;">
    <a href="{$safeConfirm}" style="background:#9b4d24;color:#fff;text-decoration:none;padding:11px 18px;border-radius:6px;font-weight:600;display:inline-block;">Confirm subscription</a>
  </p>
  <p style="color:#625a52;font-size:14px;">Or paste this link into your browser:<br><a href="{$safeConfirm}" style="color:#9b4d24;">{$safeConfirm}</a></p>
  <p style="color:#625a52;font-size:14px;">If you didn't request this, you can ignore this email and you won't be added.</p>
</div>
HTML;
$text = "Thanks for subscribing to Jacob Stephens' blog.\n\n"
      . "Confirm your email address to start receiving new posts:\n{$confirmUrl}\n\n"
      . "If you didn't request this, ignore this email and you won't be added.";

$res = nl_send([$email], "Confirm your subscription to Jacob Stephens' blog", $html, $text);
if (!$res['ok']) {
    error_log('newsletter-subscribe send failed: ' . ($res['error'] ?? 'unknown'));
    nl_respond(false, 'We could not send the confirmation email. Please try again later.', 502);
}

nl_respond(true, 'Almost there - check your email and click the confirmation link.');
