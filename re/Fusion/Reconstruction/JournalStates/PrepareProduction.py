import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.PermuteJournal import PermuteJournal
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    sources = (
        ('OffsetCylinder', 're/Fusion/Study/faceedits-3f120cbee8d9/offset_cylinder.f3d'),
        ('Draft', 're/Fusion/Study/moretools-88a2cd6cad0b/Draft.f3d'),
    )
    for label, relative in sources:
        source = ROOT / relative
        with ZipFile(source) as archive:
            members = tuple(name for name in archive.namelist() if name.endswith('.smbh'))
            if len(members) != 1:
                raise ValueError('Expected one native journal')
            member = members[0]
            original = archive.read(member)
            model = ReadJournal(original)
            order = (0, *reversed(range(1, model.ActiveCount)), *reversed(range(model.ActiveCount, len(model.Entities))))
            for variant, value in (('Production', model), ('ProductionPermuted', PermuteJournal(model, order))):
                emitted = EmitJournal(value)
                target = args.output / (label + variant + 'History.f3d')
                history = target.with_suffix('.smbh')
                history.write_bytes(emitted)
                with ZipFile(target, 'w', compression=ZIP_DEFLATED) as output:
                    for entry in archive.infolist():
                        output.writestr(entry.filename, emitted if entry.filename == member else archive.read(entry.filename))
                results.append(dict(label=label, variant=variant, source=str(source), sourceArchiveSha256=hashlib.sha256(source.read_bytes()).hexdigest(), member=member, sourceHistorySha256=hashlib.sha256(original).hexdigest(), target=str(target), targetArchiveSha256=hashlib.sha256(target.read_bytes()).hexdigest(), history=str(history), historySha256=hashlib.sha256(emitted).hexdigest(), historyBytes=len(emitted), byteIdentical=original == emitted, activeCount=value.ActiveCount, entityCount=len(value.Entities), stream=asdict(value.Stream), states=[dict(stateId=state.StateId, entityCount=len(state.Versions)) for state in Materialize(value)]))
    report = dict(schema='FusionProductionJournalNativePreparation/1', productionApis=['ReadJournal', 'EmitJournal', 'Materialize', 'PermuteJournal'], nativeAcceptance='pending', scope='Each source-specific archive retains its own non-history members; all history bytes are emitted from typed semantic models, with explicit allocation permutation in two candidates; no independent Design authoring claim', outputs=results)
    (args.output / 'ProductionPreparation.json').write_text(json.dumps(report, indent=2) + '\n')
    for result in results:
        print(result['target'], result['historySha256'], result['byteIdentical'])


if __name__ == '__main__':
    main()
