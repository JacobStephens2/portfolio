<?php
/**
 * Newsletter double opt-in confirmation for stephens.page/blog.
 * GET ?token=... -> marks a pending subscriber confirmed and shows a landing page.
 */

declare(strict_types=1);
require __DIR__ . '/newsletter-lib.php';

header('Content-Type: text/html; charset=UTF-8');
header('X-Robots-Tag: noindex');

$token = (string) ($_GET['token'] ?? '');

if ($token === '' || !ctype_xdigit($token)) {
    http_response_code(400);
    echo nl_page('Invalid link', 'That link doesn\'t look right',
        '<p>The confirmation link is missing or malformed. Try subscribing again from the blog.</p>');
    exit;
}

try {
    $db  = nl_db();
    $sel = $db->prepare('SELECT id, status FROM subscribers WHERE confirm_token = ?');
    $sel->execute([$token]);
    $row = $sel->fetch(PDO::FETCH_ASSOC);

    if (!$row) {
        // Token already consumed (confirm clears it) or never existed.
        echo nl_page('Already confirmed', 'You\'re all set',
            '<p>This link has already been used. If you\'ve confirmed once, you\'re subscribed - nothing more to do.</p>');
        exit;
    }

    $upd = $db->prepare(
        'UPDATE subscribers
            SET status = \'confirmed\', confirmed_at = ?, confirm_token = NULL
          WHERE id = ?'
    );
    $upd->execute([time(), $row['id']]);

    echo nl_page('Subscription confirmed', 'You\'re subscribed',
        '<p>Thanks for confirming. You\'ll get an email when I publish a new post - nothing else.</p>'
        . '<p>Every email includes a one-click unsubscribe link if you ever change your mind.</p>');
} catch (Throwable $e) {
    error_log('newsletter-confirm: ' . $e->getMessage());
    http_response_code(500);
    echo nl_page('Something went wrong', 'Something went wrong',
        '<p>We couldn\'t confirm your subscription just now. Please try the link again in a little while.</p>');
}
