"""Read product history into an isolated guard-local clone; canonical hook only."""
import importlib.machinery, importlib.util, json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
GUARD = ROOT / 'bin/skipi-guard'
loader = importlib.machinery.SourceFileLoader('journal_replay_guard', str(GUARD))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
SOURCE = '/home/linux/Developer/worktrees/crewing-c3b1-20260922'
OLD = 'd6298ce9a4d5358e92884c54e73868058881871c'
NEW = sys.argv[2] if len(sys.argv) > 2 else 'f743a8e04611e1b5ae1e91a7ad33b23a3df6474b'
label = sys.argv[1]
def cmd(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kw)
with tempfile.TemporaryDirectory(prefix='actual-', dir=OUT) as tmp:
    tmp = pathlib.Path(tmp)
    repo = tmp / 'repo'
    cmd(['git', 'clone', '--shared', '--no-checkout', '-q', SOURCE, str(repo)])
    (tmp / 'skipi-plugins').symlink_to('/home/linux/Developer/skipi-plugins', target_is_directory=True)
    cmd(['git', '-C', str(repo), 'checkout', '-q', '--detach', '12a7ce4'])
    # Optional isolated rehearsal only: actual product checkout remains read-only.
    if len(sys.argv) > 3 or label == 'main-negative':
        cmd(['git', '-C', str(repo), 'config', 'user.name', 'Guard metadata rehearsal'])
        cmd(['git', '-C', str(repo), 'config', 'user.email', 'guard@example.invalid'])
        if label == 'main-negative':
            OLD = cmd(['git', '-C', str(repo), 'rev-parse', 'HEAD']).stdout.strip()
            journal = repo / 'docs/crewing-pilot-c3b1/WORKLOG.md'
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text('isolated main journal-only negative control\n')
        else:
            cmd(['git', '-C', str(repo), 'checkout', '-q', '--detach', NEW])
            workflow = repo / '.github/workflows/skipi-guard.yml'
            before = workflow.read_text()
            assert before.count('071eea0c3679c8b35bad2bd62adb2df4c3b17746') == 1
            workflow.write_text(before.replace('071eea0c3679c8b35bad2bd62adb2df4c3b17746', sys.argv[3]))
        cmd(['git', '-C', str(repo), 'add', '-f', 'docs/crewing-pilot-c3b1/WORKLOG.md'])
        cmd(['git', '-C', str(repo), 'add', '.github/workflows/skipi-guard.yml'])
        cmd(['git', '-C', str(repo), 'commit', '-qm', 'isolated metadata rehearsal'])
        NEW = cmd(['git', '-C', str(repo), 'rev-parse', 'HEAD']).stdout.strip()
        diff = cmd(['git', '-C', str(repo), 'diff', OLD, NEW, '--', '.github/workflows/skipi-guard.yml']).stdout
        (OUT / f'{label}-pin.diff').write_text(diff)
        if label == 'future-journal':
            OLD = NEW
            journal = repo / 'docs/crewing-pilot-c3b1/WORKLOG.md'
            journal.write_text(journal.read_text() + '\nFuture metadata update rehearsal.\n')
            cmd(['git', '-C', str(repo), 'add', '-f', 'docs/crewing-pilot-c3b1/WORKLOG.md'])
            cmd(['git', '-C', str(repo), 'commit', '-qm', 'isolated future journal update'])
            NEW = cmd(['git', '-C', str(repo), 'rev-parse', 'HEAD']).stdout.strip()
        cmd(['git', '-C', str(repo), 'checkout', '-q', '--detach', '12a7ce4'])
    result = OUT / f'{label}-hook.json' 
    adapter = tmp / 'capture-guard'
    adapter.write_text('#!/usr/bin/env python3\nimport os,sys\n' +
                      f'os.execv({str(GUARD)!r}, [{str(GUARD)!r}, *sys.argv[1:], "--json", {str(result)!r}])\n')
    adapter.chmod(0o755)
    hook = tmp / 'pre-push'
    hook.write_text(module.render_hook('crewing', str(adapter)))
    stdin = f'refs/heads/feature/crewing-c3b1-20260922 {NEW} refs/heads/feature/crewing-c3b1-20260922 {OLD}\n'
    (OUT / f'{label}-stdin.txt').write_text(stdin)
    env = os.environ.copy()
    env.pop('SKIPI_GUARD_OVERRIDE_TOKEN', None)
    proc = subprocess.run(['bash', str(hook)], cwd=repo, input=stdin, env=env, text=True, capture_output=True)
    (OUT / f'{label}-hook.log').write_text(f'rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}')
    report = json.loads(result.read_text())
    print(label, 'hook', proc.returncode, report['task'], [(t['name'], t['status']) for t in report['tests']])
    cmd(['git', '-C', str(repo), 'checkout', '-q', '--detach', NEW])
    result = OUT / f'{label}-ci.json'
    proc = subprocess.run([str(GUARD), 'verify', '--home', 'crewing', '--repo', str(repo), '--base', OLD, '--head', NEW,
                           '--auto-task', '--run-harness', '--json', str(result)], env=env, text=True, capture_output=True)
    (OUT / f'{label}-ci.log').write_text(f'rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}')
    report = json.loads(result.read_text())
    print(label, 'ci', proc.returncode, report['task'], [(t['name'], t['status']) for t in report['tests']])
