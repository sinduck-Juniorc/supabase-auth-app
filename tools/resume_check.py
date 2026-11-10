"""자격 증명을 읽거나 네트워크 호출을 하지 않는 작업 재개 검사."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
def git(*args):
    p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=15)
    return p.stdout.strip() if p.returncode == 0 else None

state = json.loads((root / 'project-state.json').read_text(encoding='utf-8'))
branch = git('branch', '--show-current')
baseline = git('rev-parse', state['baseline_tag'] + '^{commit}')
checks = {'development_branch_matches': branch == state['development_branch'],
          'baseline_matches': baseline == state['baseline_commit']}
report = {'branch': branch, 'head': git('rev-parse', 'HEAD'), 'checks': checks,
          'working_tree_has_changes': bool(git('status', '--porcelain')),
          'services': {name: '미검증: 연결 도구에서 별도 확인 필요' for name in state['services']},
          'next_work': state['next_work'], 'handoff': state['handoff']}
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if all(checks.values()) else 2)
