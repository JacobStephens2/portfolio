<?php
/**
 * Shared library for the stephens.page/blog newsletter.
 *
 * Self-hosted, double opt-in subscriber list stored in SQLite outside the web
 * root. Email is sent through the Resend HTTP API using the shared fleet key in
 * private/.env (RESEND_API_KEY), which refresh-smtp-derived keeps in sync on
 * rotation - so there is no private copy of the key to drift. See CLAUDE.md.
 *
 * Used by:
 *   newsletter-subscribe.php   (public POST)   - add a pending subscriber, mail a confirm link
 *   newsletter-confirm.php     (public GET)    - confirm via token
 *   newsletter-unsubscribe.php (public GET/POST)- opt out via token (also RFC 8058 one-click)
 *   send-newsletter.php        (CLI only)      - blast a post to confirmed subscribers
 */

declare(strict_types=1);

const NL_DB_PATH      = '/var/lib/stephens-newsletter/newsletter.sqlite';
const NL_SITE_URL     = 'https://stephens.page';
const NL_FROM_EMAIL   = 'jacob@stephens.page';
const NL_FROM_NAME    = 'Jacob Stephens';
const NL_LIST_NAME    = "Jacob Stephens' blog";

/** Load key=value pairs from stephens.page/private/.env (same format as the contact form). */
function nl_env(): array
{
    static $env = null;
    if ($env !== null) {
        return $env;
    }
    $env = [];
    $envFile = __DIR__ . '/../private/.env';
    if (is_readable($envFile)) {
        foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
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
    }
    return $env;
}

/** Open the SQLite database, creating the schema on first use. */
function nl_db(): PDO
{
    static $db = null;
    if ($db !== null) {
        return $db;
    }
    $dir = dirname(NL_DB_PATH);
    if (!is_dir($dir)) {
        throw new RuntimeException('Newsletter data directory is missing: ' . $dir);
    }
    $db = new PDO('sqlite:' . NL_DB_PATH);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec('PRAGMA journal_mode = WAL');
    $db->exec('PRAGMA busy_timeout = 5000');
    $db->exec(
        'CREATE TABLE IF NOT EXISTS subscribers (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            email             TEXT NOT NULL UNIQUE COLLATE NOCASE,
            status            TEXT NOT NULL DEFAULT \'pending\',
            confirm_token     TEXT,
            unsubscribe_token TEXT NOT NULL,
            created_at        INTEGER NOT NULL,
            confirmed_at      INTEGER,
            unsubscribed_at   INTEGER,
            ip                TEXT
        )'
    );
    $db->exec(
        'CREATE TABLE IF NOT EXISTS sends (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            post_url        TEXT NOT NULL,
            subject         TEXT,
            sent_at         INTEGER NOT NULL,
            recipient_count INTEGER
        )'
    );
    return $db;
}

/** Cryptographically-random URL-safe token. */
function nl_token(): string
{
    return bin2hex(random_bytes(32));
}

/**
 * Send one email via the Resend HTTP API.
 *
 * @param array<int,string>    $to      Recipient addresses.
 * @param array<string,string> $headers Extra headers (e.g. List-Unsubscribe).
 * @return array{ok:bool,id?:string,error?:string}
 */
function nl_send(array $to, string $subject, string $html, string $text, array $headers = []): array
{
    $key = nl_env()['RESEND_API_KEY'] ?? '';
    if ($key === '') {
        return ['ok' => false, 'error' => 'RESEND_API_KEY is not configured'];
    }
    $payload = [
        'from'    => sprintf('%s <%s>', NL_FROM_NAME, NL_FROM_EMAIL),
        'to'      => array_values($to),
        'subject' => $subject,
        'html'    => $html,
        'text'    => $text,
    ];
    if ($headers !== []) {
        $payload['headers'] = $headers;
    }
    $ch = curl_init('https://api.resend.com/emails');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . $key,
            'Content-Type: application/json',
        ],
        CURLOPT_POSTFIELDS     => json_encode($payload),
    ]);
    $raw  = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $cerr = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        return ['ok' => false, 'error' => 'curl: ' . $cerr];
    }
    $data = json_decode((string) $raw, true);
    if ($code >= 200 && $code < 300 && isset($data['id'])) {
        return ['ok' => true, 'id' => (string) $data['id']];
    }
    $msg = is_array($data) && isset($data['message']) ? $data['message'] : ('HTTP ' . $code);
    return ['ok' => false, 'error' => $msg];
}

/** Absolute URL for a confirm link. */
function nl_confirm_url(string $token): string
{
    return NL_SITE_URL . '/blog/newsletter-confirm.php?token=' . urlencode($token);
}

/** Absolute URL for an unsubscribe link. */
function nl_unsubscribe_url(string $token): string
{
    return NL_SITE_URL . '/blog/newsletter-unsubscribe.php?token=' . urlencode($token);
}

/**
 * Minimal branded HTML page for the confirm / unsubscribe landing screens.
 * Mirrors the blog's typography and palette so it doesn't look bolted on.
 */
function nl_page(string $title, string $heading, string $bodyHtml): string
{
    $t = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $h = htmlspecialchars($heading, ENT_QUOTES, 'UTF-8');
    return <<<HTML
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/png" href="/bee-favicon.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>{$t} | Jacob Stephens</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
:root{--ink:#181512;--brand:#9b4d24;--muted:#625a52;--surface:#fff;--soft:#efe9df;--rule:#d6d1c9;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Source Sans 3',Arial,sans-serif;background:var(--surface);color:var(--ink);line-height:1.7;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1.5rem;}
.card{max-width:520px;text-align:center;}
h1{font-family:'Source Serif 4',Georgia,serif;font-weight:700;font-size:clamp(1.8rem,4vw,2.4rem);line-height:1.1;color:var(--brand);margin-bottom:1rem;}
p{color:var(--ink);margin-bottom:1rem;}
a{color:var(--brand);}
.actions{margin-top:1.5rem;}
.btn{display:inline-block;padding:0.6rem 1.1rem;border:1px solid var(--rule);border-radius:6px;color:var(--ink);text-decoration:none;font-weight:600;}
.btn:hover{border-color:var(--brand);color:var(--brand);}
</style>
</head>
<body>
<div class="card">
<h1>{$h}</h1>
{$bodyHtml}
<div class="actions"><a class="btn" href="/blog/">&larr; Back to the blog</a></div>
</div>
</body>
</html>
HTML;
}
