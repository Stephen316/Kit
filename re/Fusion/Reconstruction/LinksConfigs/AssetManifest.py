import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from RootManifest import Cur


def parse(data):
    c = Cur(data)
    out = {'name': c.w(), 'asset_id': c.w(), 'snapshot_id': c.w(), 'role': c.a(), 'wire': c.u32()}
    out['versions'] = [(c.a(), c.u32()) for _ in range(c.u32())]
    out['kind'] = [c.a(), c.u32(), c.u8()]
    out['properties'] = [(c.a(), c.w()) for _ in range(c.u32())]
    links = []
    for _ in range(c.u32()):
        links.append({'link': c.w(), 'asset': c.w(), 'snapshot': c.w(), 'k': c.u32(), 'marker': c.u32(), 'change': c.w()})
    out['links'] = links
    out['next_segment'] = c.u32()
    out['segments'] = [(c.u32(), c.a(), c.a()) for _ in range(c.u32())]
    out['rest'] = data[c.pos:].hex()
    return out


if __name__ == '__main__':
    print(json.dumps(parse(open(sys.argv[1], 'rb').read()), indent=1))
