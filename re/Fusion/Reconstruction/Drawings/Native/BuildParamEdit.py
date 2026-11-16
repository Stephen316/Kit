import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.Convert.Formats.FusionCodec.Parameters.RebuildParams import RebuildParams

SOURCE = Path(
    os.environ.get(
        "KIT_PARAM_SOURCE",
        str(ROOT / "re/Fusion/Study/advanced-627f7fe095f4/advanced.f3d"),
    )
)
OUT = Path(os.environ.get("KIT_DESIGN_OUT", str(HERE / "Out"))) / "Designs"
LABEL = os.environ.get("KIT_PARAM_LABEL", "KitParamEdit")
PARAM = os.environ.get("KIT_PARAM_NAME", "d1")
NEW_MM = float(os.environ.get("KIT_PARAM_MM", "45.0"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    original = SOURCE.read_bytes()
    seen = []

    def change(value):
        seen.append(value)
        if value.ParamName != PARAM:
            return value
        return replace(
            value,
            Number=NEW_MM / 10.0,
            Formula=f"{NEW_MM:.2f} mm",
        )

    edited = RebuildParams(SOURCE, change)
    path = OUT / f"{LABEL}.f3d"
    path.write_bytes(edited)
    control = OUT / f"{LABEL}Control.f3d"
    control.write_bytes(original)
    before = next(value for value in seen if value.ParamName == PARAM)
    row = {
        "label": LABEL,
        "file": path.name,
        "control": control.name,
        "source": str(SOURCE.relative_to(ROOT)),
        "param": PARAM,
        "before_number": before.Number,
        "before_formula": before.Formula,
        "after_number": NEW_MM / 10.0,
        "after_formula": f"{NEW_MM:.2f} mm",
        "bytes": len(edited),
        "sha256": hashlib.sha256(edited).hexdigest(),
        "control_sha256": hashlib.sha256(original).hexdigest(),
    }
    (OUT / "ParamPlan.json").write_text(json.dumps(row, indent=1) + "\n")
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
