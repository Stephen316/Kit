import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

for name in sys.argv[1:]:
    model = ReadDocument(Path(name).read_bytes())
    document = model.Document
    print(Path(name).name, 'ancestry', len(document.Ancestry), 'lineage', document.Lineage)
    for link in document.Links:
        print('  root link', link.LinkId, link.SourcePath, link.CachePath, link.XrefPath)
        for key, value in link.Properties:
            print('     ', key, '=', value)
    for link in model.Asset.Links:
        print('  asset link', link)
    for segment in model.Segments:
        for context in segment.Metadata.Contexts:
            print('  context', segment.Metadata.Header.Segment.name, context)
    print('  properties', model.Properties)
    print('  redirects', model.Redirects)
