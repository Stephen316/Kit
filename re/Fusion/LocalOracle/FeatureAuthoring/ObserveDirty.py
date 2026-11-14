import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "ObserveRecompute.py"), init_globals={"PREPARATION": "DirtyPreparation.json", "OUTPUT": "DirtyObservation.json"}, run_name="__kit_fusion_oracle__")
