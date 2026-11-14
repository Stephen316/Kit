"""Research: EmitFormDoc documents from the merged head for native acceptance.

Each case reuses an accepted cage of the third-pass cage document run, so the
only change against that run is the merged design and ACT structure. The
report records the class tables that the shared vocabulary now declares and
the converted parts that stay byte-identical when the clock is pinned to the
recorded document.
"""

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
import convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc as EmitModule
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

ORACLE = 're/Fusion/LocalOracle/FormDocuments/'
WORK = ROOT / ORACLE / 'MergeDocuments'
CASES = ('BoxFresh', 'CreasedPlaneFresh', 'Valence5Fresh', 'WarpedPlane2x5')
WATCH = ('DcAssemblyFeature', 'DcPlaceComponentInstance', 'DcXRefPCIFeature', 'XRefManager', 'ACTRefdTable')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def class_names():
    found = {}
    for path in (ROOT / 'src/convert/formats/Fusion').rglob('*.json'):
        try:
            rows = json.loads(path.read_text())
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and 'ClassGuid' in row and 'NameValue' in row:
                    found[row['ClassGuid'].upper()] = row['NameValue']
    return found


NAMES = class_names()


def tables(model):
    rows = {}
    for segment in model.Segments:
        names = [NAMES.get(item.ClassGuid.upper(), item.ClassGuid) for item in segment.Metadata.Classes]
        rows[segment.Metadata.Header.Segment.value] = {'classes': len(names), 'records': len(segment.Records), 'watched': sorted(set(WATCH) & set(names))}
    return rows


def converted_parts(data):
    found = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            for suffix in ('.smbh', '.smb', '.tsm'):
                if name.endswith(suffix):
                    found[suffix] = archive.read(name)
    return found


class Clock:
    def __init__(self, text):
        self.text = text

    def now(self, zone):
        return self

    def isoformat(self):
        return self.text


def pinned_parts(cage, case, recorded):
    history = next(body.History for body in ReadDocument(recorded).Bodies if isinstance(body.History, JournalModel))
    micros = int(next(entity.UnixMicros for entity in history.Entities if hasattr(entity, 'UnixMicros')))
    clock, timer = EmitModule.DateTime, EmitModule.ReadTimeNano
    EmitModule.DateTime, EmitModule.ReadTimeNano = Clock(history.Stamp.SavedAt), lambda: micros * 1000
    try:
        payload = EmitModule.EmitFormDoc(FormSpec('Kit ' + case, cage, ConvertForm(cage)))
    finally:
        EmitModule.DateTime, EmitModule.ReadTimeNano = clock, timer
    mine, theirs = converted_parts(payload), converted_parts(recorded)
    return {suffix: mine.get(suffix) == theirs.get(suffix) for suffix in ('.smbh', '.smb', '.tsm')}


def main():
    WORK.mkdir(exist_ok=True)
    prior = {row['case']: row for row in json.loads((ROOT / ORACLE / 'CageDocuments/Preparation.json').read_text())['rows']}
    rows = []
    for case in CASES:
        source = prior[case]
        text = (ROOT / source['tsm_file']).read_bytes()
        if digest(text) != source['tsm_sha256']:
            raise RuntimeError(case + ': recorded cage changed')
        cage = ReadTspline(text)
        payload = EmitModule.EmitFormDoc(FormSpec('Kit ' + case, cage, ConvertForm(cage)))
        model = ReadDocument(payload)
        if len(model.Forms) != 1 or model.Forms[0].Surface != cage:
            raise RuntimeError(case + ': written cage differs')
        if ReadDocument(EmitParsed(model)) != model:
            raise RuntimeError(case + ': written document does not round-trip')
        document = WORK / (case + '.f3d')
        document.write_bytes(payload)
        recorded = (ROOT / source['document_file']).read_bytes()
        row = {'case': case, 'tsm_file': source['tsm_file'], 'tsm_sha256': source['tsm_sha256'], 'document_file': str(document.relative_to(ROOT)), 'document_sha256': digest(payload), 'third_pass_document': source['document_file'], 'class_tables': tables(model), 'third_pass_class_tables': tables(ReadDocument(recorded)), 'converted_parts_equal_with_pinned_clock': pinned_parts(cage, case, recorded)}
        rows.append(row)
        print(json.dumps({key: row[key] for key in ('case', 'class_tables', 'converted_parts_equal_with_pinned_clock')}))
    report = {'scope': 'EmitFormDoc documents from the merged head for accepted third-pass cages. The design and ACT class tables now declare the xref and assembly classes of the shared vocabulary, and the XZ origin plane uses the native frame. The converted BRep, snapshot and cage parts equal the third-pass documents when the clock is pinned', 'python': sys.version.split()[0], 'rows': rows}
    (WORK / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
