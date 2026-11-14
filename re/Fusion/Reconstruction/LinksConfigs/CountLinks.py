import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef


def crosses(value, found):
    if isinstance(value, CrossRef):
        found.append(value)
    elif isinstance(value, (tuple, list)):
        for item in value:
            crosses(item, found)
    elif hasattr(value, '__slots__'):
        for name in value.__slots__:
            crosses(getattr(value, name), found)
    return found


for name in sys.argv[1:]:
    model = ReadDocument(Path(name).read_bytes())
    counts = []
    tokens_ok = True
    for segment in model.Segments:
        found = crosses(segment.Records, [])
        tokens = {context.Token for context in segment.Metadata.Contexts}
        tokens_ok &= all(item.Token in tokens for item in found)
        counts.append((segment.Metadata.Header.Segment.name, len(segment.Metadata.Contexts), len(found)))
    names = sorted(dict(link.Properties).get('toDocDisplayName', '') for link in model.Document.Links)
    print(Path(name).stem, len(model.Document.Links), len(model.Asset.Links), counts, tokens_ok, names)
