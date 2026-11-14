import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import Probe

NAMES = (
    'TextureMappingAttribute', 'TextureEffectAttribute', 'NodeData', 'GraphicsBlobFeatures', 'F360InstanceNode',
    'BillBoardAttribute', 'GroupNode', 'GraphicsGlobalVersion', 'OGSBlobVersion',
)


def versions(world):
    found = {}
    for name in NAMES:
        marker = struct.pack('<I', len(name)) + name.encode('utf-16le')
        position = world.find(marker)
        if position >= 0:
            found[name] = struct.unpack_from('<I', world, position + len(marker))[0]
    return found


if __name__ == '__main__':
    for name in sys.argv[1:]:
        found = Probe.members(name)
        print(Path(name).name[:12], versions(found['world']) if 'world' in found else 'no world')
