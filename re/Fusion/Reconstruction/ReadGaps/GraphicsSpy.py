import sys
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from ExampleRecords import documents
import convert.formats.Fusion.GraphicsCodec.Schema.GlobalVersions as Globals
import convert.formats.Fusion.GraphicsCodec.Schema.AttrRules as Attrs
from convert.formats.Fusion.GraphicsCodec.Schema.FieldRule import FieldRule
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import ReadSceneParts

SEEN = []


def main():
    import convert.formats.Fusion.GraphicsCodec.Wire.XferObjectMut as Objects
    module = sys.modules[[name for name in sys.modules if name.endswith('XferGlobalMut')][0]] if any(name.endswith('XferGlobalMut') for name in sys.modules) else None
    if module is None:
        import importlib
        for name in ('convert.formats.Fusion.GraphicsCodec.Fields.XferGlobalMut', 'convert.formats.Fusion.GraphicsCodec.Wire.XferGlobalMut', 'convert.formats.Fusion.GraphicsCodec.Model.XferGlobalMut'):
            try:
                module = importlib.import_module(name)
                break
            except ImportError:
                continue
    for key, value in [item.split('=') for item in sys.argv[1:] if '=' in item]:
        Globals.KGlobalVersions.setdefault(key, ())
        Globals.KGlobalVersions[key] = tuple(sorted(set(Globals.KGlobalVersions[key]) | {int(value)}))
    source = module.XferGlobalMut

    def spy(state, value):
        start = state.Position
        try:
            return source(state, value)
        except ValueError:
            state.Position = start
            count = state.CountValue(None)
            versions = [(state.TextValue(None), state.Integer(None)) for _ in range(count)]
            SEEN.append((versions, state.TextValue(None)))
            raise

    module.XferGlobalMut = spy
    for name in list(sys.modules):
        if 'GraphicsCodec' in name and getattr(sys.modules[name], 'XferGlobalMut', None) is source:
            sys.modules[name].XferGlobalMut = spy
    for name, data in documents():
        container = ReadContainer(data)
        try:
            ReadSceneParts(container.Parts)
            print(name[-10:], 'graphics read')
        except Exception as error:
            frames = traceback.extract_tb(error.__traceback__)
            print(name[-10:], str(error)[:80], [f'{Path(f.filename).stem}:{f.lineno}' for f in frames[-3:]])
    for versions, environment in SEEN:
        known = Globals.KGlobalVersions
        print(environment, [(name, version) for name, version in versions if version not in known.get(name, ())], 'missing', sorted(set(known) - {name for name, _ in versions}))


if __name__ == '__main__':
    main()
