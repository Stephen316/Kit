import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import SceneOnly
from convert.formats.Fusion.GraphicsCodec.Schema.AttrRules import KAttrRules
from convert.formats.Fusion.GraphicsCodec.Schema.GlobalVersions import KGlobalVersions

KGlobalVersions['BillBoardAttribute'] = (1,)
KAttrRules['BillBoardAttribute'] = KAttrRules['BillBoardAttribute'][:4]

if __name__ == '__main__':
    for name in sys.argv[1:]:
        print(Path(name).name[:16], json.dumps(SceneOnly.scene(Path(name).read_bytes()))[:600])
