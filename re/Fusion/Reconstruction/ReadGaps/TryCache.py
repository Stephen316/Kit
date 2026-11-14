import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from CacheSpy import ROOT, where

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import EmitSceneParts
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer

BUNDLES = ('re/Fusion/examples/.f3z/example1.f3z', 're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z')


def main():
    members = [int(item) for item in sys.argv[1:]]
    for bundle in BUNDLES:
        documents = ReadBundle((ROOT / bundle).read_bytes()).Documents
        for member in members:
            label = f'{bundle.split("/")[-1]} member {member}'
            try:
                model = ReadDocument(documents[member].DataValue)
            except Exception as error:
                print(label, 'read fail', error, where(error))
                continue
            parts = {part.Name: part.Payload for part in ReadContainer(documents[member].DataValue).Parts if part.Name.startswith('OGS.BlobFolder/')}
            written = {part.Name: part.Payload for part in EmitSceneParts(model.Graphics)}
            slack = [len(item.Payload) for item in model.Graphics.MeshSlack + model.Graphics.FusionSlack] if model.Graphics else []
            try:
                again = ReadDocument(EmitParsed(model))
                print(label, 'read', 'round', again == model, 'scene bytes equal', parts == written, 'slack', slack)
            except Exception as error:
                print(label, 'read', 'round fail', error, where(error))


if __name__ == '__main__':
    main()
