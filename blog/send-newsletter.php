<?php
/**
 * Send a published blog post to all confirmed newsletter subscribers.
 *
 * CLI ONLY. Run as the web user so it can write the SQLite database:
 *     sudo -u www-data php send-newsletter.php <post-url-or-slug> [--dry-run] [--force]
 *
 * Examples:
 *     sudo -u www-data php send-newsletter.php the-agents-i-run --dry-run
 *     sudo -u www-data php send-newsletter.php https://stephens.page/blog/the-agents-i-run/
 *
 * --dry-run  Show the subject and recipient count, send nothing.
 * --force    Send even if this post was already sent before.
 *
 * Each email carries a per-subscriber one-click unsubscribe (RFC 8058) so it
 * lands well and stays CAN-SPAM compliant.
 */

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit("This script is CLI-only.\n");
}

require __DIR__ . '/newsletter-lib.php';

$args   = array_slice($argv, 1);
$dryRun = in_array('--dry-run', $args, true);
$force  = in_array('--force', $args, true);
$posArgs = array_values(array_filter($args, static fn($a) => $a !== '' && $a[0] !== '-'));

if (count($posArgs) !== 1) {
    fwrite(STDERR, "Usage: php send-newsletter.php <post-url-or-slug> [--dry-run] [--force]\n");
    exit(2);
}

// --- Resolve the post slug and its local index.html -------------------------
$input = $posArgs[0];
$slug  = trim($input);
if (str_contains($slug, '://')) {
    $path = parse_url($slug, PHP_URL_PATH) ?: '';
    $slug = trim(preg_replace('#^/blog/#', '', rtrim($path, '/')), '/');
}
$slug = basename($slug); // guard against traversal
if ($slug === '' || !preg_match('/^[a-z0-9-]+$/', $slug)) {
    fwrite(STDERR, "Invalid post slug: {$input}\n");
    exit(2);
}

$postFile = __DIR__ . '/' . $slug . '/index.html';
if (!is_file($postFile)) {
    fwrite(STDERR, "Post not found: {$postFile}\n");
    exit(2);
}
$postUrl = NL_SITE_URL . '/blog/' . $slug . '/';
$html    = (string) file_get_contents($postFile);

// --- Extract title and description ------------------------------------------
$title = $slug;
if (preg_match('#<title>(.*?)</title>#is', $html, $m)) {
    $title = trim(html_entity_decode($m[1], ENT_QUOTES, 'UTF-8'));
    $title = preg_replace('/\s*\|\s*Jacob Stephens\s*$/', '', $title);
}
$desc = '';
if (preg_match('#<meta name="description" content="(.*?)"#is', $html, $m)) {
    $desc = trim(html_entity_decode($m[1], ENT_QUOTES, 'UTF-8'));
}

// --- Guard against an accidental re-send ------------------------------------
$db = nl_db();
$prev = $db->prepare('SELECT sent_at FROM sends WHERE post_url = ? ORDER BY sent_at DESC LIMIT 1');
$prev->execute([$postUrl]);
if (($last = $prev->fetchColumn()) !== false && !$force && !$dryRun) {
    fwrite(STDERR, sprintf(
        "This post was already sent on %s. Re-run with --force to send again.\n",
        date('Y-m-d H:i', (int) $last)
    ));
    exit(1);
}

// --- Gather confirmed subscribers -------------------------------------------
$subs = $db->query(
    'SELECT email, unsubscribe_token FROM subscribers WHERE status = \'confirmed\' ORDER BY id'
)->fetchAll(PDO::FETCH_ASSOC);

$subject = $title;
printf("Post:       %s\n", $postUrl);
printf("Subject:    %s\n", $subject);
printf("Recipients: %d confirmed subscriber(s)\n", count($subs));

if ($dryRun) {
    foreach (array_slice($subs, 0, 5) as $s) {
        printf("  - %s\n", $s['email']);
    }
    if (count($subs) > 5) {
        printf("  ... and %d more\n", count($subs) - 5);
    }
    echo "Dry run - nothing sent.\n";
    exit(0);
}

if (count($subs) === 0) {
    echo "No confirmed subscribers. Nothing to send.\n";
    exit(0);
}

// --- Send -------------------------------------------------------------------
$safeTitle = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
$safeDesc  = htmlspecialchars($desc, ENT_QUOTES, 'UTF-8');
$safeUrl   = htmlspecialchars($postUrl, ENT_QUOTES, 'UTF-8');

$ok = 0;
$fail = 0;
foreach ($subs as $s) {
    $unsubUrl  = nl_unsubscribe_url($s['unsubscribe_token']);
    $safeUnsub = htmlspecialchars($unsubUrl, ENT_QUOTES, 'UTF-8');

    $body = <<<HTML
<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:16px;line-height:1.6;color:#181512;max-width:560px;">
  <p style="color:#625a52;font-size:14px;margin:0 0 16px;">New post on Jacob Stephens' blog</p>
  <h1 style="font-size:22px;line-height:1.25;margin:0 0 12px;color:#181512;">{$safeTitle}</h1>
  <p style="margin:0 0 24px;color:#333;">{$safeDesc}</p>
  <p style="margin:0 0 28px;">
    <a href="{$safeUrl}" style="background:#9b4d24;color:#fff;text-decoration:none;padding:11px 18px;border-radius:6px;font-weight:600;display:inline-block;">Read the post</a>
  </p>
  <hr style="border:none;border-top:1px solid #d6d1c9;margin:24px 0;">
  <p style="color:#8a8178;font-size:12px;margin:0;">
    You're receiving this because you subscribed at stephens.page/blog.
    <a href="{$safeUnsub}" style="color:#8a8178;">Unsubscribe</a>.
  </p>
</div>
HTML;

    $text = "New post on Jacob Stephens' blog\n\n{$title}\n\n"
          . ($desc !== '' ? "{$desc}\n\n" : '')
          . "Read it: {$postUrl}\n\n---\nUnsubscribe: {$unsubUrl}\n";

    $headers = [
        'List-Unsubscribe'      => "<{$unsubUrl}>, <mailto:jacob@stephens.page?subject=unsubscribe>",
        'List-Unsubscribe-Post' => 'List-Unsubscribe=One-Click',
    ];

    $res = nl_send([$s['email']], $subject, $body, $text, $headers);
    if ($res['ok']) {
        $ok++;
    } else {
        $fail++;
        fwrite(STDERR, sprintf("  FAILED %s: %s\n", $s['email'], $res['error'] ?? 'unknown'));
    }
    usleep(200000); // ~5/sec, gentle on the API and reputation
}

$db->prepare('INSERT INTO sends (post_url, subject, sent_at, recipient_count) VALUES (?, ?, ?, ?)')
   ->execute([$postUrl, $subject, time(), $ok]);

printf("Done. Sent %d, failed %d.\n", $ok, $fail);
exit($fail > 0 ? 1 : 0);
