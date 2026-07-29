/**
 * Click-to-run (and type-to-run) CLI demos for the vaulted-agent writeup.
 * These are honest replays of recorded sessions - not a live shell - because
 * the real launcher needs bash, a vault backend, and a local process.
 */
(function () {
  'use strict';

  var DEMOS = {
    herestring: {
      title: 'Bug 1 · here-string spill',
      hint: 'Click Run, or type: small  /  big',
      lines: [
        { t: 'cmd', s: 'bash -c \'readlink /proc/self/fd/0\' <<< "small"' },
        { t: 'out', s: 'pipe:[112050729]' },
        { t: 'blank' },
        { t: 'cmd', s: 'big=$(head -c 100000 /dev/zero | tr \'\\0\' a)' },
        { t: 'cmd', s: 'bash -c \'readlink /proc/self/fd/0\' <<< "$big"' },
        { t: 'out', s: '/tmp/sh-thd.PJd9QD (deleted)' },
        { t: 'dim', s: '# above the pipe buffer, bash spilled the whole string to /tmp' }
      ],
      commands: {
        small: [
          { t: 'cmd', s: 'bash -c \'readlink /proc/self/fd/0\' <<< "small"' },
          { t: 'out', s: 'pipe:[112050729]' }
        ],
        big: [
          { t: 'cmd', s: 'bash -c \'readlink /proc/self/fd/0\' <<< "$big"' },
          { t: 'out', s: '/tmp/sh-thd.PJd9QD (deleted)' },
          { t: 'dim', s: '# secrets would have landed in that temp file' }
        ]
      }
    },

    token: {
      title: 'Bug 2 · vault token rides along',
      hint: 'Click Run, or type: before  /  after',
      lines: [
        { t: 'dim', s: '# before the fix: token exported, then agent exec\'d' },
        { t: 'cmd', s: 'set -a; . op.env; set +a' },
        { t: 'cmd', s: 'env | grep OP_SERVICE_ACCOUNT_TOKEN' },
        { t: 'out', s: 'OP_SERVICE_ACCOUNT_TOKEN=ops_••••••••••••••••' },
        { t: 'dim', s: '# agent inherits the master key - manifests are decorative' },
        { t: 'blank' },
        { t: 'dim', s: '# after: drop it before the handoff' },
        { t: 'cmd', s: 'unset OP_SERVICE_ACCOUNT_TOKEN' },
        { t: 'cmd', s: 'env | grep OP_SERVICE_ACCOUNT_TOKEN || echo "(absent)"' },
        { t: 'out', s: '(absent)' }
      ],
      commands: {
        before: [
          { t: 'cmd', s: 'env | grep OP_SERVICE_ACCOUNT_TOKEN' },
          { t: 'out', s: 'OP_SERVICE_ACCOUNT_TOKEN=ops_••••••••••••••••' }
        ],
        after: [
          { t: 'cmd', s: 'unset OP_SERVICE_ACCOUNT_TOKEN' },
          { t: 'cmd', s: 'env | grep OP_SERVICE_ACCOUNT_TOKEN || echo "(absent)"' },
          { t: 'out', s: '(absent)' }
        ]
      }
    },

    manifests: {
      title: 'Different harnesses, different secrets',
      hint: 'Click Run, or type: claude  /  grok  /  table',
      lines: [
        { t: 'cmd', s: 'vaulted-agent' },
        { t: 'out', s: '  claude           claude --permission-mode auto           full.env' },
        { t: 'out', s: '  grok             grok                                  readonly.env' },
        { t: 'blank' },
        { t: 'cmd', s: 'vaulted-agent claude   # prints env names the stub received' },
        { t: 'out', s: 'APP_DB_HOST' },
        { t: 'out', s: 'APP_DB_PASS' },
        { t: 'out', s: 'APP_DB_USER' },
        { t: 'out', s: 'GH_TOKEN' },
        { t: 'out', s: 'SMTP_PASS' },
        { t: 'blank' },
        { t: 'cmd', s: 'vaulted-agent grok' },
        { t: 'out', s: 'APP_DB_HOST' },
        { t: 'out', s: 'APP_DB_PASS' },
        { t: 'out', s: 'APP_DB_USER' },
        { t: 'blank' },
        { t: 'out', s: '                    claude   grok' },
        { t: 'out', s: '   APP_DB_HOST      yes      yes' },
        { t: 'out', s: '   APP_DB_PASS      yes      yes' },
        { t: 'out', s: '   APP_DB_USER      yes      yes' },
        { t: 'out', s: '   GH_TOKEN         yes       -' },
        { t: 'out', s: '   SMTP_PASS        yes       -' },
        { t: 'dim', s: "# grok's manifest never named GH_TOKEN or SMTP_PASS" }
      ],
      commands: {
        claude: [
          { t: 'cmd', s: 'vaulted-agent claude' },
          { t: 'out', s: 'APP_DB_HOST' },
          { t: 'out', s: 'APP_DB_PASS' },
          { t: 'out', s: 'APP_DB_USER' },
          { t: 'out', s: 'GH_TOKEN' },
          { t: 'out', s: 'SMTP_PASS' }
        ],
        grok: [
          { t: 'cmd', s: 'vaulted-agent grok' },
          { t: 'out', s: 'APP_DB_HOST' },
          { t: 'out', s: 'APP_DB_PASS' },
          { t: 'out', s: 'APP_DB_USER' },
          { t: 'dim', s: '# no GH_TOKEN, no SMTP_PASS' }
        ],
        table: [
          { t: 'out', s: '                    claude   grok' },
          { t: 'out', s: '   APP_DB_HOST      yes      yes' },
          { t: 'out', s: '   APP_DB_PASS      yes      yes' },
          { t: 'out', s: '   APP_DB_USER      yes      yes' },
          { t: 'out', s: '   GH_TOKEN         yes       -' },
          { t: 'out', s: '   SMTP_PASS        yes       -' }
        ]
      }
    },

    scrub: {
      title: 'Bug 3 · scrub before inject',
      hint: 'Click Run, or type: leak  /  scrubbed',
      lines: [
        { t: 'dim', s: '# narrow manifest (one var) but parent env still rides along' },
        { t: 'cmd', s: 'export GH_TOKEN=ghp_parenttoken  APP_DB_PASS=only-this-should-appear' },
        { t: 'cmd', s: 'vaulted-agent narrow   # before scrub fix' },
        { t: 'out', s: 'APP_DB_PASS' },
        { t: 'out', s: 'GH_TOKEN' },
        { t: 'dim', s: '# parent GitHub token leaked into a "narrow" agent' },
        { t: 'blank' },
        { t: 'cmd', s: 'vaulted-agent narrow   # after allowlist scrub' },
        { t: 'out', s: 'APP_DB_PASS' },
        { t: 'dim', s: '# only the manifest; caller secrets stripped' }
      ],
      commands: {
        leak: [
          { t: 'cmd', s: 'vaulted-agent narrow   # before scrub' },
          { t: 'out', s: 'APP_DB_PASS' },
          { t: 'out', s: 'GH_TOKEN' }
        ],
        scrubbed: [
          { t: 'cmd', s: 'vaulted-agent narrow   # after scrub' },
          { t: 'out', s: 'APP_DB_PASS' }
        ]
      }
    },

    bashfunc: {
      title: 'Bug 4 · exported functions slip past',
      hint: 'Click Run, or type: before  /  after',
      lines: [
        { t: 'dim', s: '# first demo run - scrub used compgen -e only' },
        { t: 'out', s: '                    claude   grok' },
        { t: 'out', s: '   APP_DB_HOST      yes      yes' },
        { t: 'out', s: '   GH_TOKEN         yes       -' },
        { t: 'out', s: '   BASH_FUNC_which%%   yes   yes' },
        { t: 'out', s: '   BASH_FUNC_module%%  yes   yes' },
        { t: 'out', s: '   BASH_FUNC_scl%%     yes   yes' },
        { t: 'dim', s: '# exported functions are not variables; unset NAME misses them' },
        { t: 'blank' },
        { t: 'cmd', s: '# fix: second pass over declare -Fx with unset -f' },
        { t: 'out', s: '                    claude   grok' },
        { t: 'out', s: '   APP_DB_HOST      yes      yes' },
        { t: 'out', s: '   GH_TOKEN         yes       -' },
        { t: 'dim', s: '# BASH_FUNC_* gone' }
      ],
      commands: {
        before: [
          { t: 'out', s: '   BASH_FUNC_which%%   yes   yes' },
          { t: 'out', s: '   BASH_FUNC_module%%  yes   yes' },
          { t: 'out', s: '   BASH_FUNC_scl%%     yes   yes' }
        ],
        after: [
          { t: 'out', s: '                    claude   grok' },
          { t: 'out', s: '   APP_DB_HOST      yes      yes' },
          { t: 'out', s: '   GH_TOKEN         yes       -' },
          { t: 'dim', s: '# no BASH_FUNC_* rows' }
        ]
      }
    },

    probe: {
      title: 'Where secrets live (and do not)',
      hint: 'Click Run, or type: probe',
      lines: [
        { t: 'cmd', s: 'CALLER_SECRET=leaked-from-parent vaulted-agent probe' },
        { t: 'out', s: '   in its environment   APP_DB_PASS=corr3ct-h0rse$battery`staple`' },
        { t: 'out', s: '   on its command line  probe' },
        { t: 'out', s: '   from the caller      CALLER_SECRET=removed by the scrub' },
        { t: 'dim', s: "# ps shows the cmdline, never the environment" }
      ],
      commands: {
        probe: [
          { t: 'cmd', s: 'CALLER_SECRET=leaked-from-parent vaulted-agent probe' },
          { t: 'out', s: '   in its environment   APP_DB_PASS=corr3ct-h0rse$battery`staple`' },
          { t: 'out', s: '   on its command line  probe' },
          { t: 'out', s: '   from the caller      CALLER_SECRET=removed by the scrub' }
        ]
      }
    },

    refuse: {
      title: 'It refuses half-fed starts',
      hint: 'Click Run, or type: broken  /  borrow',
      lines: [
        { t: 'cmd', s: 'vaulted-agent broken   # manifest points at a missing file' },
        { t: 'err', s: 'unreachable secrets: could not resolve does-not-exist.env' },
        { t: 'blank' },
        { t: 'cmd', s: 'grok-conductor -H claude   # borrow another harness via symlink path' },
        { t: 'err', s: 'refusing to run harness claude under name grok-conductor' },
        { t: 'dim', s: '# per-path sudoers stay meaningful when $0 is preserved' }
      ],
      commands: {
        broken: [
          { t: 'cmd', s: 'vaulted-agent broken' },
          { t: 'err', s: 'unreachable secrets: could not resolve does-not-exist.env' }
        ],
        borrow: [
          { t: 'cmd', s: 'grok-conductor -H claude' },
          { t: 'err', s: 'refusing to run harness claude under name grok-conductor' }
        ]
      }
    }
  };

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function lineHtml(line) {
    if (line.t === 'blank') return '<div class="cli-line cli-blank">&nbsp;</div>';
    if (line.t === 'cmd') {
      return '<div class="cli-line cli-cmd"><span class="cli-prompt">$ </span>' + esc(line.s) + '</div>';
    }
    if (line.t === 'dim') {
      return '<div class="cli-line cli-dim">' + esc(line.s) + '</div>';
    }
    if (line.t === 'err') {
      return '<div class="cli-line cli-err">' + esc(line.s) + '</div>';
    }
    return '<div class="cli-line cli-out">' + esc(line.s) + '</div>';
  }

  function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  function mount(root) {
    var id = root.getAttribute('data-demo');
    var demo = DEMOS[id];
    if (!demo) return;

    root.innerHTML =
      '<div class="cli-bar">' +
        '<span class="cli-dots" aria-hidden="true"><i></i><i></i><i></i></span>' +
        '<span class="cli-title">' + esc(demo.title) + '</span>' +
        '<button type="button" class="cli-run">Run</button>' +
      '</div>' +
      '<div class="cli-screen" role="log" aria-live="polite" aria-relevant="additions"></div>' +
      '<form class="cli-input-row" autocomplete="off">' +
        '<label class="cli-sr-only" for="cli-in-' + esc(id) + '">Type a demo command</label>' +
        '<span class="cli-prompt" aria-hidden="true">$</span>' +
        '<input id="cli-in-' + esc(id) + '" class="cli-input" type="text" spellcheck="false" ' +
          'placeholder="' + esc(demo.hint || 'type a command, or click Run') + '">' +
        '<button type="submit" class="cli-go">Go</button>' +
      '</form>' +
      '<p class="cli-caption">Browser replay of a recorded session - not a live shell. ' +
        'Click <strong>Run</strong>, or type one of the demo commands above.</p>';

    var screen = root.querySelector('.cli-screen');
    var runBtn = root.querySelector('.cli-run');
    var form = root.querySelector('.cli-input-row');
    var input = root.querySelector('.cli-input');
    var playing = false;
    var token = 0;

    function idlePrompt() {
      var idle = document.createElement('div');
      idle.className = 'cli-line cli-idle';
      idle.innerHTML = '<span class="cli-prompt">$ </span><span class="cli-cursor"></span>';
      screen.appendChild(idle);
      screen.scrollTop = screen.scrollHeight;
    }

    function clearScreen() {
      screen.innerHTML = '';
    }

    async function play(lines) {
      var my = ++token;
      playing = true;
      runBtn.disabled = true;
      runBtn.textContent = 'Running…';
      clearScreen();
      for (var i = 0; i < lines.length; i++) {
        if (my !== token) return;
        var el = document.createElement('div');
        el.innerHTML = lineHtml(lines[i]);
        screen.appendChild(el.firstChild);
        screen.scrollTop = screen.scrollHeight;
        var delay = lines[i].t === 'cmd' ? 220 : lines[i].t === 'blank' ? 80 : 90;
        await sleep(delay);
      }
      if (my !== token) return;
      idlePrompt();
      playing = false;
      runBtn.disabled = false;
      runBtn.textContent = 'Run again';
    }

    function unknown(cmd) {
      var keys = Object.keys(demo.commands || {}).join(', ');
      return play([
        { t: 'cmd', s: cmd },
        { t: 'err', s: 'demo: unknown command' },
        { t: 'dim', s: keys ? '# try: ' + keys + '  (or click Run for the full session)' : '# click Run for the full session' }
      ]);
    }

    runBtn.addEventListener('click', function () {
      if (playing) return;
      play(demo.lines);
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (playing) return;
      var raw = (input.value || '').trim();
      input.value = '';
      if (!raw) {
        play(demo.lines);
        return;
      }
      var key = raw.toLowerCase().replace(/^vaulted-agent\s+/, '').replace(/^sudo\s+/, '');
      // allow typing the full command strings as aliases
      if (demo.commands[key]) {
        play(demo.commands[key]);
        return;
      }
      // also match if they type something that starts with a known key
      var found = null;
      Object.keys(demo.commands || {}).some(function (k) {
        if (key === k || key.indexOf(k) === 0 || raw.toLowerCase().indexOf(k) !== -1) {
          found = k;
          return true;
        }
        return false;
      });
      if (found) play(demo.commands[found]);
      else unknown(raw);
    });

    // placeholder idle state
    clearScreen();
    var stub = document.createElement('div');
    stub.className = 'cli-line cli-dim';
    stub.textContent = '# click Run to play this session';
    screen.appendChild(stub);
    idlePrompt();
  }

  document.querySelectorAll('.cli-demo[data-demo]').forEach(mount);
})();
