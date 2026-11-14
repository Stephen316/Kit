import dataclasses
import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get('SWEEP_SRC', str(ROOT / 'src')))
sys.path.insert(0, str(BASE))

from Sweep import tracked

from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline


def main():
    result = {}
    for name in tracked():
        if not name.endswith('.f3d'):
            continue
        with zipfile.ZipFile(io.BytesIO((ROOT / name).read_bytes())) as archive:
            members = [item for item in archive.namelist() if item.lower().endswith('.tsm')]
            for index, item in enumerate(members):
                payload = archive.read(item)
                key = f'{name} {index}'
                try:
                    model = ReadTspline(payload)
                except Exception as error:
                    result[key] = ['fail', type(error).__name__]
                    continue
                encoded = json.dumps(dataclasses.asdict(model), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
                result[key] = [hashlib.sha256(encoded).hexdigest(), EmitTspline(model) == payload]
    Path(sys.argv[1]).write_text(json.dumps(result, indent=0, sort_keys=True))
    print(len(result))


if __name__ == '__main__':
    main()
