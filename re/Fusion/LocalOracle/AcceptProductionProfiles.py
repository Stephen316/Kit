import runpy
from pathlib import Path

root = Path(__file__).resolve().parent
for name in ('AcceptProductionParameter.py', 'AcceptProductionCircle.py'):
    runpy.run_path(str(root / name), run_name='__kit_fusion_profile__')
