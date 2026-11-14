import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "ObserveVariants.py"), init_globals={"FOLDER": "Regressions"}, run_name="__kit_fusion_oracle__")
