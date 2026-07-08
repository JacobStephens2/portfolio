<?php
/**
 * Newsletter unsubscribe for stephens.page/blog.
 *  - GET  ?token=... -> opt out and show a landing page (link in the email footer).
 *  - POST ?token=... -> RFC 8058 one-click unsubscribe (List-Unsubscribe-Post),
 *                       invoked by the mail client; returns 200 with no page.
 */

declare(strict_types=1);
require __DIR__ . '/newsletter-lib.php';

$token  = (string) ($_GET['token'] ?? '');
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

function nl_unsub_apply(string $token): string
{
    // Returns: 'done' | 'already' | 'notfound'
    $db  = nl_db();
    $sel = $db->prepare('SELECT id, status FROM subscribers WHERE unsubscribe_token = ?');
    $sel->execute([$token]);
    $row = $sel->fetch(PDO::FETCH_ASSOC);
    if (!$row) {
        return 'notfound';
    }
    if ($row['status'] === 'unsubscribed') {
        return 'already';
    }
    $upd = $db->prepare(
        'UPDATE subscribers SET status = \'unsubscribed\', unsubscribed_at = ? WHERE id = ?'
    );
    $upd->execute([time(), $row['id']]);
    return 'done';
}

// One-click (RFC 8058): mail clients POST here. No HTML, just acknowledge.
if ($method === 'POST') {
    header('Content-Type: text/plain; charset=UTF-8');
    if ($token !== '' && ctype_xdigit($token)) {
        try {
            nl_unsub_apply($token);
        } catch (Throwable $e) {
            error_log('newsletter-unsubscribe (POST): ' . $e->getMessage());
        }
    }
    http_response_code(200);
    echo 'OK';
    exit;
}

// Browser click (GET): show a landing page.
header('Content-Type: text/html; charset=UTF-8');
header('X-Robots-Tag: noindex');

if ($token === '' || !ctype_xdigit($token)) {
    http_response_code(400);
    echo nl_page('Invalid link', 'That link doesn\'t look right',
        '<p>The unsubscribe link is missing or malformed. Email <a href="mailto:jacob@stephens.page">jacob@stephens.page</a> and I\'ll remove you.</p>');
    exit;
}

try {
    $result = nl_unsub_apply($token);
    if ($result === 'notfound') {
        echo nl_page('Not found', 'We couldn\'t find that subscription',
            '<p>This link doesn\'t match anyone on the list. You may already be removed. Email <a href="mailto:jacob@stephens.page">jacob@stephens.page</a> if you need help.</p>');
    } else {
        echo nl_page('Unsubscribed', 'You\'ve been unsubscribed',
            '<p>You won\'t receive any more newsletter emails. Sorry to see you go - you\'re welcome back anytime from the blog.</p>');
    }
} catch (Throwable $e) {
    error_log('newsletter-unsubscribe: ' . $e->getMessage());
    http_response_code(500);
    echo nl_page('Something went wrong', 'Something went wrong',
        '<p>We couldn\'t process that just now. Please try again shortly, or email <a href="mailto:jacob@stephens.page">jacob@stephens.page</a>.</p>');
}
