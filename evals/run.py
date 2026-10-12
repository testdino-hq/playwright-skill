#!/usr/bin/env python3
"""Measure how well an agent routes to and uses this skill.

Usage: python3 -I evals/run.py --arm NAME=SKILL_DIR [--arm ...] [--model sonnet] [--jobs 6] [--only id1,id2] [--repeat 1] [--force]

Each case runs `claude -p` in a throwaway project that has the skill installed under
.claude/skills/playwright-skill and Playwright 1.64 in package.json. Only read tools are allowed.
A case passes when the agent read one of the expected guides, the answer matches every `must`
regex, and no fenced code block in the answer matches a `must_not` regex (prose may mention an old
flag to say it changed). --force prefixes every prompt with an explicit request to use
the skill, which separates routing inside the skill from whether the skill triggers at all.
"""
import argparse, concurrent.futures as cf, json, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {'.git', 'evals'}
SYSTEM = "Answer in chat. Do not create or modify files."


def make_project(skill_src, root):
    dst = os.path.join(root, '.claude', 'skills', 'playwright-skill')
    shutil.copytree(skill_src, dst, ignore=lambda d, names: [n for n in names if n in SKIP and d == skill_src])
    with open(os.path.join(root, 'package.json'), 'w') as f:
        json.dump({"name": "app", "private": True, "devDependencies": {"@playwright/test": "1.64.0"}}, f)
    with open(os.path.join(root, 'playwright.config.ts'), 'w') as f:
        f.write("import { defineConfig } from '@playwright/test';\n\nexport default defineConfig({ testDir: './tests' });\n")
    os.makedirs(os.path.join(root, 'tests'))
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    return dst


def run_case(case, project, skill_dir, model, force):
    prompt = ('Use the playwright-skill skill. ' if force else '') + case['prompt']
    cmd = ['claude', '-p', prompt, '--output-format', 'stream-json', '--verbose',
           '--setting-sources', 'project', '--strict-mcp-config', '--no-session-persistence',
           '--model', model, '--append-system-prompt', SYSTEM,
           '--allowedTools', 'Read', 'Grep', 'Glob', 'Skill',
           '--disallowedTools', 'Bash', 'Write', 'Edit', 'NotebookEdit', 'WebFetch', 'WebSearch', 'Agent']
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=600)
    reads, skills, answer, meta = [], [], '', {}
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get('type') == 'assistant':
            for block in ev['message'].get('content', []):
                if block.get('type') != 'tool_use':
                    continue
                if block['name'] == 'Read':
                    reads.append(block['input'].get('file_path', ''))
                elif block['name'] == 'Skill':
                    skills.append(block['input'].get('skill', ''))
        elif ev.get('type') == 'result':
            answer = ev.get('result') or ''
            meta = {'cost': ev.get('total_cost_usd', 0), 'turns': ev.get('num_turns', 0)}
    skill_dir = os.path.realpath(skill_dir)
    rel = [os.path.relpath(os.path.realpath(p), skill_dir) for p in reads if os.path.realpath(p).startswith(skill_dir + os.sep)]
    read_bytes = sum(os.path.getsize(os.path.join(skill_dir, p)) for p in rel if os.path.exists(os.path.join(skill_dir, p)))
    routed = any(g in rel for g in case['guides'])
    missing = [m for m in case['must'] if not re.search(m, answer, re.I)]
    code = '\n'.join(re.findall(r'```[^\n]*\n(.*?)```', answer, re.S))
    wrong = [m for m in case['must_not'] if re.search(m, code, re.I)]
    return {'id': case['id'], 'triggered': bool(skills) or 'SKILL.md' in rel, 'routed': routed,
            'facts': not missing, 'clean': not wrong, 'pass': routed and not missing and not wrong,
            'missing': missing, 'wrong': wrong, 'read': rel, 'raw_reads': reads, 'skills': skills, 'read_kb': round(read_bytes / 1024),
            'secs': round(time.time() - t0), 'answer': answer, **meta}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', action='append', required=True, help='NAME=SKILL_DIR')
    ap.add_argument('--model', default='sonnet')
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--only', default='')
    ap.add_argument('--repeat', type=int, default=1)
    ap.add_argument('--out', default=tempfile.gettempdir())
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    cases = json.load(open(os.path.join(HERE, 'cases.json')))
    if args.only:
        keep = set(args.only.split(','))
        cases = [c for c in cases if c['id'] in keep]

    work = tempfile.mkdtemp(prefix='pw-skill-eval-')
    jobs = []
    for spec in args.arm:
        name, src = spec.split('=', 1)
        for case in cases:
            for r in range(args.repeat):
                root = os.path.join(work, f'{name}-{case["id"]}-{r}')
                os.makedirs(root)
                jobs.append((name, case, root, make_project(os.path.abspath(src), root)))

    results = {}
    with cf.ThreadPoolExecutor(args.jobs) as pool:
        futs = {pool.submit(run_case, c, root, sd, args.model, args.force): name for name, c, root, sd in jobs}
        for fut in cf.as_completed(futs):
            name = futs[fut]
            res = fut.result()
            results.setdefault(name, []).append(res)
            print(f"{name:8} {res['id']:22} pass={int(res['pass'])} routed={int(res['routed'])} facts={int(res['facts'])} clean={int(res['clean'])} read={res['read_kb']}KB", flush=True)

    out = os.path.join(args.out, 'pw-skill-eval-results.json')
    json.dump(results, open(out, 'w'), indent=1)
    print(f"\n{'arm':8} {'n':>3} {'trigger':>8} {'routed':>7} {'facts':>6} {'clean':>6} {'pass':>5} {'avgKB':>6} {'cost$':>7}")
    for name, rs in results.items():
        n = len(rs)
        pct = lambda k: f"{100 * sum(r[k] for r in rs) // n}%"
        print(f"{name:8} {n:>3} {pct('triggered'):>8} {pct('routed'):>7} {pct('facts'):>6} {pct('clean'):>6} {pct('pass'):>5} "
              f"{sum(r['read_kb'] for r in rs) // n:>6} {sum(r.get('cost', 0) for r in rs):>7.2f}")
    print(f"results: {out}")


if __name__ == '__main__':
    sys.exit(main())
