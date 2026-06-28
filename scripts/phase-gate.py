#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase-gate.py - 阶段化开发状态机

为 phase-gated-dev skill 提供状态持久化和硬卡点校验。

核心功能：
- 从开发计划文档解析 phases
- 维护 .state/state.json（跨会话持久化）
- 强制 phase 顺序：上一个 phase 不通过，下一个 phase 不让开始
- 记录 review 轮数和历史

退出码：
  0 - 成功
  1 - 一般错误
  2 - 被硬卡点拒绝（如：跳过未通过的 phase）

使用示例：
  python phase-gate.py init ./development_plan_v1.0.md
  python phase-gate.py status
  python phase-gate.py start 1
  python phase-gate.py review 1 --pass
  python phase-gate.py review 1 --issues "问题1;问题2"
  python phase-gate.py reset 1
  python phase-gate.py skip 2
  python phase-gate.py list
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 强制 stdout 用 UTF-8（Windows PowerShell 兼容）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 中文数字 → 阿拉伯数字（支持 1-19）
CN_NUM_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9,
}


def parse_cn_num(s: str):
    """解析中文或阿拉伯数字。返回 int 或 None。"""
    s = s.strip()
    if s.isdigit():
        return int(s)
    if s in CN_NUM_MAP:
        return CN_NUM_MAP[s]
    if '十' in s:
        parts = s.split('十')
        if len(parts) == 2:
            tens = CN_NUM_MAP.get(parts[0], 1) if parts[0] else 1
            ones = CN_NUM_MAP.get(parts[1], 0) if parts[1] else 0
            return tens * 10 + ones
    return None


class PhaseGate:
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
        self.state_dir = skill_dir / '.state'
        self.state_file = self.state_dir / 'state.json'
        self.history_file = self.state_dir / 'history.log'

    # ---------------- 文件 IO ----------------

    def ensure_state_dir(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self):
        if not self.state_file.exists():
            return None
        return json.loads(self.state_file.read_text(encoding='utf-8'))

    def save_state(self, state: dict):
        self.ensure_state_dir()
        # ensure_ascii=False 让 JSON 里直接写中文，而不是 \u 转义
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    def log_history(self, action: str, **kwargs):
        self.ensure_state_dir()
        entry = {
            'time': datetime.now().isoformat(timespec='seconds'),
            'action': action,
            **kwargs,
        }
        with self.history_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # ---------------- 计划文档解析 ----------------

    def parse_plan(self, plan_path: Path):
        """从开发计划文档解析 phases。返回 [{num, title}, ...]。"""
        text = plan_path.read_text(encoding='utf-8')
        phases = []
        seen_nums = set()

        # 优先级 1: ### 阶段X：xxx  /  ### Phase X: xxx  /  ### Stage X - xxx
        pattern1 = re.compile(
            r'^#{2,4}\s*(?:阶段|Phase|Stage)\s*'
            r'([一二三四五六七八九十\d]+)\s*'
            r'[：:]\s*(.+?)\s*$',
            re.MULTILINE | re.IGNORECASE,
        )
        for m in pattern1.finditer(text):
            num = parse_cn_num(m.group(1))
            if num is None or num in seen_nums:
                continue
            seen_nums.add(num)
            phases.append({'num': num, 'title': m.group(2).strip()})

        # 优先级 2: ## 阶段X / ## Phase X（无冒号标题）
        if not phases:
            pattern2 = re.compile(
                r'^#{2,4}\s*(?:阶段|Phase|Stage)\s*([一二三四五六七八九十\d]+)\s*$',
                re.MULTILINE | re.IGNORECASE,
            )
            for m in pattern2.finditer(text):
                num = parse_cn_num(m.group(1))
                if num is None or num in seen_nums:
                    continue
                seen_nums.add(num)
                phases.append({'num': num, 'title': f'阶段 {num}'})

        return sorted(phases, key=lambda p: p['num'])

    def _find_phase(self, state: dict, n: int):
        for p in state['phases']:
            if p['num'] == n:
                return p
        return None

    # ---------------- Git 集成 ----------------

    def _detect_git_repo(self, start_dir: Path):
        """检测 start_dir（或其父目录链）是否在 git 仓库内。
        返回 (repo_root: Path | None, is_repo: bool)。
        如果 git 命令不存在或超时，返回 (None, False)。
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=str(start_dir),
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip()), True
            return None, False
        except FileNotFoundError:
            # 系统没有 git 命令
            return None, False
        except subprocess.TimeoutExpired:
            return None, False
        except Exception:
            return None, False

    def _has_git_user_config(self, repo_root: Path):
        """检查 git 是否配置了 user.name 和 user.email"""
        try:
            for key in ('user.name', 'user.email'):
                r = subprocess.run(
                    ['git', 'config', '--get', key],
                    cwd=str(repo_root), capture_output=True, text=True, timeout=5,
                )
                if r.returncode != 0 or not r.stdout.strip():
                    return False
            return True
        except Exception:
            return False

    def _set_fallback_git_user(self, repo_root: Path):
        """为本次 commit 设置 fallback user（如果未配置）"""
        try:
            subprocess.run(
                ['git', 'config', 'user.name', 'phase-gated-dev'],
                cwd=str(repo_root), capture_output=True, timeout=5,
            )
            subprocess.run(
                ['git', 'config', 'user.email', 'phase-gated-dev@local'],
                cwd=str(repo_root), capture_output=True, timeout=5,
            )
            return True
        except Exception:
            return False

    def _git_add_and_commit(self, repo_root: Path, message: str, add_all: bool = True):
        """在 repo_root 执行 git add + commit。
        返回 (success: bool, output: str)。失败不抛异常。
        """
        try:
            if add_all:
                r = subprocess.run(
                    ['git', 'add', '.'],
                    cwd=str(repo_root), capture_output=True, text=True, timeout=30,
                )
                if r.returncode != 0:
                    return False, f'git add 失败:\n{r.stderr}'
            r = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=str(repo_root), capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                # 无变化（nothing to commit）也视为成功但提示
                if 'nothing to commit' in (r.stdout + r.stderr).lower():
                    return True, r.stdout + r.stderr
                return False, f'git commit 失败:\n{r.stderr}\n{r.stdout}'
            return True, r.stdout
        except subprocess.TimeoutExpired:
            return False, 'git 命令超时'
        except Exception as e:
            return False, f'git 异常: {e}'

    def _generate_commit_message(self, phase: dict, custom: str = None) -> str:
        """生成 phase commit message"""
        if custom:
            return custom
        n = phase['num']
        title = phase['title']
        rounds = phase.get('review_rounds', 0)
        completed_at = phase.get('completed_at') or datetime.now().isoformat(timespec='seconds')

        msg = f"""phase {n}: {title}

review 轮数: {rounds}
通过时间: {completed_at}

Co-Authored-By: phase-gated-dev <noreply@local>"""
        return msg

    def cmd_commit(self, n: int = None, message: str = None, dry_run: bool = False):
        """commit 指定 phase（或当前 in_progress phase）的改动。
        没有 git 仓库 → 跳过 + 提示（不报错）。
        git 命令失败 → warning，不阻塞 phase 流程。
        """
        state = self.load_state()
        if not state:
            print('❌ 未初始化。请先运行 init。', file=sys.stderr)
            sys.exit(1)

        # 找目标 phase
        if n is None:
            target = next((p for p in state['phases'] if p['status'] == 'in_progress'), None)
            if not target:
                # 退而求其次：最近一个 completed
                completed = [p for p in state['phases'] if p['status'] == 'completed']
                if not completed:
                    print('⚠ 没有可 commit 的 phase（in_progress 或 completed 都没有）。', file=sys.stderr)
                    sys.exit(1)
                target = max(completed, key=lambda p: p['num'])
                print(f'⚠ 没有 in_progress phase，使用最近完成: phase {target["num"]}')
            n = target['num']
        else:
            target = self._find_phase(state, n)
            if not target:
                print(f'❌ Phase {n} 不存在。', file=sys.stderr)
                sys.exit(1)
            if target['status'] not in ('in_progress', 'completed'):
                print(f'⚠ Phase {n} 状态是 {target["status"]}，不适合 commit（应 in_progress 或 completed）。', file=sys.stderr)
                sys.exit(1)

        # 检测 git 仓库（从 plan 所在目录开始）
        plan_path = Path(state['plan_file'])
        start_dir = plan_path.parent
        repo_root, is_repo = self._detect_git_repo(start_dir)

        if not is_repo:
            print(f'⚠ 未检测到 git 仓库（从 {start_dir} 向上查找）')
            print('   跳过 git commit，不影响 phase 状态。')
            print('   如需启用 git 管理：在项目根运行 `git init` 初始化仓库后重试。')
            return  # exit 0，不算错

        print(f'>> 检测到 git 仓库: {repo_root}')

        # 检查/设置 user 配置
        if not self._has_git_user_config(repo_root):
            print('⚠ git 未配置 user.name/user.email，使用 fallback。')
            if not dry_run:
                self._set_fallback_git_user(repo_root)

        # 生成 commit message
        commit_msg = self._generate_commit_message(target, custom=message)

        if dry_run:
            print('\n[dry-run] 将执行:')
            print(f'  cd {repo_root}')
            print(f'  git add .')
            print(f'  git commit -m "{commit_msg.split(chr(10))[0]}..."')
            print('\n完整 message:')
            print('---')
            print(commit_msg)
            print('---')
            return

        # 执行
        print(f'>> 提交 phase {n} ({target["title"]}) ...')
        success, output = self._git_add_and_commit(repo_root, commit_msg)

        if success:
            # 记录到 history.log
            state.setdefault('git_commits', []).append({
                'phase': n,
                'time': datetime.now().isoformat(timespec='seconds'),
                'repo': str(repo_root),
            })
            self.save_state(state)
            self.log_history('git_commit', phase=n, repo=str(repo_root))
            print('✅ git commit 成功')
            # 显示简短输出（git commit 通常最后一行是分支+short SHA）
            tail = output.strip().splitlines()[-3:] if output.strip() else []
            for line in tail:
                print(f'   {line}')
        else:
            print(f'⚠ git commit 失败（不影响 phase 状态）：\n{output}')
            print('   请手动检查：是否有未解决的 conflict / hook 失败 / 权限问题')

    # ---------------- 子命令 ----------------

    def cmd_init(self, plan_path: str, force: bool = False):
        plan_file = Path(plan_path).resolve()
        if not plan_file.exists():
            print(f'❌ 计划文档不存在: {plan_file}', file=sys.stderr)
            sys.exit(1)

        phases = self.parse_plan(plan_file)
        if not phases:
            print(f'❌ 未能从 {plan_file.name} 解析出任何 phase', file=sys.stderr)
            print('  支持的格式:', file=sys.stderr)
            print('    ### 阶段X：xxx', file=sys.stderr)
            print('    ### Phase X: xxx', file=sys.stderr)
            print('    ## 阶段X / ## Phase X', file=sys.stderr)
            sys.exit(1)

        if self.state_file.exists():
            if not force:
                # 已有 state 时默认拒绝覆盖（防止误操作清空进度）
                print(f'❌ 状态文件已存在，拒绝覆盖以保护进度。', file=sys.stderr)
                print(f'   当前位置: {self.state_file}', file=sys.stderr)
                print(f'', file=sys.stderr)
                print(f'   如确需重新初始化：', file=sys.stderr)
                print(f'     1. 运行 init <plan_path> --force', file=sys.stderr)
                print(f'     2. 或手动删除 .state/state.json 后再 init', file=sys.stderr)
                print(f'', file=sys.stderr)
                print(f'   当前进度（status 命令可见）：', file=sys.stderr)
                try:
                    existing = self.load_state()
                    for p in existing['phases']:
                        print(f'     phase {p["num"]}: {p["title"]} [{p["status"]}]', file=sys.stderr)
                except Exception:
                    pass
                sys.exit(1)
            else:
                # 显式 force：备份后覆盖
                backup = self.state_file.with_suffix('.json.force-bak')
                self.state_file.replace(backup)
                print(f'⚠ --force 模式：已备份原 state 到 {backup.name}')

        state = {
            'plan_file': str(plan_file),
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'phases': [
                {
                    'num': p['num'],
                    'title': p['title'],
                    'status': 'pending',
                    'started_at': None,
                    'completed_at': None,
                    'review_rounds': 0,
                    'last_review_issues': [],
                }
                for p in phases
            ],
        }
        self.save_state(state)
        self.log_history('init', plan=str(plan_file), phase_count=len(phases))

        print(f'✅ 已从 {plan_file.name} 解析出 {len(phases)} 个 phase:')
        for p in phases:
            print(f'   {p["num"]}. {p["title"]}')
        print(f'\n状态已保存到: {self.state_file}')
        print(f'下一步: 等用户确认后运行 start 1 启动第一个 phase。')

    def cmd_status(self):
        state = self.load_state()
        if not state:
            print('⚠ 未初始化。请先运行 init <plan_path>')
            return

        plan = Path(state['plan_file']).name
        phases = state['phases']
        total = len(phases)
        completed = [p for p in phases if p['status'] == 'completed']
        skipped = [p for p in phases if p['status'] == 'skipped']
        in_progress = [p for p in phases if p['status'] == 'in_progress']

        current = in_progress[0] if in_progress else None
        next_phase = None
        if current:
            for p in phases:
                if p['num'] > current['num'] and p['status'] == 'pending':
                    next_phase = p
                    break
        else:
            # 没有进行中的，找第一个 pending 作为下一个可启动的
            for p in phases:
                if p['status'] == 'pending':
                    next_phase = p
                    break

        print('[Phase Status]')
        print(f'plan: {plan}')
        print(f'phases: {total} 个 (1-{phases[-1]["num"]})')
        if completed:
            print('已完成: ✓ ' + ', '.join(str(p['num']) for p in completed))
        else:
            print('已完成: 无')
        if skipped:
            print('已跳过: ⤴ ' + ', '.join(str(p['num']) for p in skipped))
        if current:
            print(f'当前:   ▶ {current["num"]} - {current["title"]}')
        elif next_phase:
            print(f'当前:   - (尚未开始，下一个可启动: {next_phase["num"]})')
        else:
            print('当前:   - (全部已完成)')
        if next_phase:
            print(f'下一:   {next_phase["num"]} - {next_phase["title"]}')
        if in_progress:
            r = in_progress[0]
            issue_text = '通过' if not r['last_review_issues'] else f'发现 {len(r["last_review_issues"])} 个问题'
            print(f'本轮:   第 {r["review_rounds"]} 轮 review | {issue_text}')

    def cmd_start(self, n: int):
        state = self.load_state()
        if not state:
            print('❌ 未初始化。请先运行 init。', file=sys.stderr)
            sys.exit(1)

        phase = self._find_phase(state, n)
        if not phase:
            print(f'❌ Phase {n} 不存在。', file=sys.stderr)
            sys.exit(1)

        if phase['status'] == 'completed':
            print(f'⚠ Phase {n} 已经完成。要重新开发请用 reset {n}。', file=sys.stderr)
            sys.exit(1)

        # 硬卡点：phase N-1 必须 completed 或 skipped
        if n > 1:
            prev = self._find_phase(state, n - 1)
            if prev and prev['status'] not in ('completed', 'skipped'):
                print(f'❌ Phase {n - 1} ({prev["title"]}) 未通过，无法开始 phase {n}。', file=sys.stderr)
                print(f'   当前 phase {n - 1} 状态: {prev["status"]}', file=sys.stderr)
                print(f'   请先完成 phase {n - 1}（review --pass）或用 skip {n - 1} 跳过。', file=sys.stderr)
                sys.exit(2)

        phase['status'] = 'in_progress'
        phase['started_at'] = datetime.now().isoformat(timespec='seconds')
        phase['review_rounds'] = 0
        phase['last_review_issues'] = []

        self.save_state(state)
        self.log_history('start', phase=n, title=phase['title'])

        print(f'✅ Phase {n} ({phase["title"]}) 已开始。')
        print(f'   启动时间: {phase["started_at"]}')

    def cmd_review(self, n: int, passed: bool, issues: str = None):
        state = self.load_state()
        if not state:
            print('❌ 未初始化。', file=sys.stderr)
            sys.exit(1)

        phase = self._find_phase(state, n)
        if not phase:
            print(f'❌ Phase {n} 不存在。', file=sys.stderr)
            sys.exit(1)

        if phase['status'] != 'in_progress':
            print(f'❌ Phase {n} 当前状态是 {phase["status"]}，不是 in_progress。', file=sys.stderr)
            print(f'   请先用 start {n} 启动该 phase。', file=sys.stderr)
            sys.exit(2)

        if passed:
            phase['status'] = 'completed'
            phase['completed_at'] = datetime.now().isoformat(timespec='seconds')
            phase['review_rounds'] += 1  # 通过也计为一轮 review
            phase['last_review_issues'] = []
            self.save_state(state)
            self.log_history('review_pass', phase=n, rounds=phase['review_rounds'])
            print(f'✅ Phase {n} review 通过！')
            print(f'   review 轮数: {phase["review_rounds"]}')
            print(f'   通过时间: {phase["completed_at"]}')
            next_p = self._find_phase(state, n + 1)
            if next_p:
                print(f'\n>> 下一阶段: {next_p["num"]} - {next_p["title"]}')
                print(f'   等用户说"继续 phase {next_p["num"]}"后运行 start {next_p["num"]} 启动。')
            else:
                print(f'\n>> 所有 phase 均已完成！')
        else:
            issue_list = [i.strip() for i in (issues or '').split(';') if i.strip()]
            phase['review_rounds'] += 1
            phase['last_review_issues'] = issue_list
            self.save_state(state)
            self.log_history('review_fail', phase=n, round=phase['review_rounds'], issues=issue_list)
            print(f'⚠ Phase {n} review 发现 {len(issue_list)} 个问题（第 {phase["review_rounds"]} 轮）:')
            for i, iss in enumerate(issue_list, 1):
                print(f'   {i}. {iss}')
            if phase['review_rounds'] >= 5:
                print(f'\n!!! 已达最大修复轮数 5。请停下让用户决策。')

    def cmd_reset(self, n: int):
        state = self.load_state()
        if not state:
            print('❌ 未初始化。', file=sys.stderr)
            sys.exit(1)

        phase = self._find_phase(state, n)
        if not phase:
            print(f'❌ Phase {n} 不存在。', file=sys.stderr)
            sys.exit(1)

        old_status = phase['status']
        phase['status'] = 'pending'
        phase['started_at'] = None
        phase['completed_at'] = None
        phase['review_rounds'] = 0
        phase['last_review_issues'] = []

        self.save_state(state)
        self.log_history('reset', phase=n, old_status=old_status)
        print(f'✅ Phase {n} 已重置（原状态: {old_status}）。')
        print(f'   现在可以运行 start {n} 重新开始。')

    def cmd_skip(self, n: int):
        state = self.load_state()
        if not state:
            print('❌ 未初始化。', file=sys.stderr)
            sys.exit(1)

        phase = self._find_phase(state, n)
        if not phase:
            print(f'❌ Phase {n} 不存在。', file=sys.stderr)
            sys.exit(1)

        if phase['status'] == 'completed':
            print(f'⚠ Phase {n} 已经完成，不需要跳过。', file=sys.stderr)
            sys.exit(1)

        old_status = phase['status']
        phase['status'] = 'skipped'
        phase['completed_at'] = datetime.now().isoformat(timespec='seconds')
        self.save_state(state)
        self.log_history('skip', phase=n, old_status=old_status)
        print(f'⤴ Phase {n} ({phase["title"]}) 已跳过。')

    def cmd_list(self):
        state = self.load_state()
        if not state:
            print('⚠ 未初始化。')
            return

        status_emoji = {
            'pending': '○',
            'in_progress': '▶',
            'completed': '✓',
            'skipped': '⤴',
        }
        print(f'计划: {Path(state["plan_file"]).name}')
        print(f'创建于: {state["created_at"]}')
        print()
        for p in state['phases']:
            emoji = status_emoji.get(p['status'], '?')
            extra = ''
            if p['status'] == 'in_progress':
                extra = f' [轮数: {p["review_rounds"]}]'
            elif p['status'] == 'completed':
                extra = f' [{p.get("completed_at", "")}]'
            print(f'  {emoji} {p["num"]:>2}. {p["title"]} [{p["status"]}]{extra}')


def main():
    parser = argparse.ArgumentParser(
        description='phase-gate.py - 阶段化开发状态机',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s init ./development_plan_v1.0.md
  %(prog)s status
  %(prog)s start 1
  %(prog)s review 1 --pass
  %(prog)s review 1 --issues "问题1;问题2"
  %(prog)s reset 1
  %(prog)s skip 2
  %(prog)s list
  %(prog)s commit          # commit 当前 in_progress phase
  %(prog)s commit 2        # commit 指定 phase
  %(prog)s commit --dry-run
  %(prog)s commit 3 -m "fix: 修复分析引擎边界条件"
""",
    )

    parser.add_argument(
        '--skill-dir', default=None,
        help='skill 目录路径（默认：脚本所在目录的上级）',
    )

    sub = parser.add_subparsers(dest='cmd', required=True, metavar='<command>')

    p_init = sub.add_parser('init', help='从开发计划文档初始化 phases（已有 state 时需 --force）')
    p_init.add_argument('plan_path', help='计划文档路径')
    p_init.add_argument('--force', dest='force', action='store_true',
                        help='强制覆盖已有 state.json（会清空当前所有 phase 进度，慎用）')

    sub.add_parser('status', help='显示当前状态')

    p_start = sub.add_parser('start', help='开始 phase N')
    p_start.add_argument('phase', type=int)

    p_review = sub.add_parser('review', help='review phase N')
    p_review.add_argument('phase', type=int)
    group = p_review.add_mutually_exclusive_group(required=True)
    group.add_argument('--pass', dest='passed', action='store_true', help='标记 review 通过')
    group.add_argument('--issues', dest='issues', type=str, default=None,
                       help='标记 review 发现的问题（分号分隔）')

    p_reset = sub.add_parser('reset', help='重置 phase 状态')
    p_reset.add_argument('phase', type=int)

    p_skip = sub.add_parser('skip', help='跳过 phase')
    p_skip.add_argument('phase', type=int)

    sub.add_parser('list', help='列出所有 phases')

    p_commit = sub.add_parser('commit', help='git commit 当前或指定 phase 的改动（无 git 仓库时跳过）')
    p_commit.add_argument('phase', type=int, nargs='?', default=None,
                          help='要 commit 的 phase 编号（默认：当前 in_progress 或最近完成）')
    p_commit.add_argument('-m', '--message', dest='message', type=str, default=None,
                          help='自定义 commit message（覆盖默认模板）')
    p_commit.add_argument('--dry-run', dest='dry_run', action='store_true',
                          help='只显示将执行的 commit，不实际提交')

    args = parser.parse_args()

    # 确定 skill_dir：脚本所在目录的上级
    script_dir = Path(__file__).parent.resolve()
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else script_dir.parent

    gate = PhaseGate(skill_dir)

    try:
        if args.cmd == 'init':
            gate.cmd_init(args.plan_path, args.force)
        elif args.cmd == 'status':
            gate.cmd_status()
        elif args.cmd == 'start':
            gate.cmd_start(args.phase)
        elif args.cmd == 'review':
            gate.cmd_review(args.phase, args.passed, args.issues)
        elif args.cmd == 'reset':
            gate.cmd_reset(args.phase)
        elif args.cmd == 'skip':
            gate.cmd_skip(args.phase)
        elif args.cmd == 'list':
            gate.cmd_list()
        elif args.cmd == 'commit':
            gate.cmd_commit(args.phase, args.message, args.dry_run)
    except KeyboardInterrupt:
        print('\n中断', file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print(f'❌ 错误: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()