import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import ReadEntitiesMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadStatesMut import ReadStatesMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadStreamNode import ReadStreamNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord


def members(path, suffix):
    archive = zipfile.ZipFile(path)
    return {info.filename: archive.read(info.filename) for info in archive.infolist() if info.filename.endswith(suffix)}


def raw_model(payload):
    cursor = MetaCursor(payload)
    header, stamp = ReadModelHead(cursor, True)
    active = ReadEntitiesMut(cursor, 'Begin-of-ASM-History-Data')
    stream = ReadStreamNode(ReadAsmRecord(cursor, ReadAsmName(cursor)))
    states = ReadStatesMut(cursor)
    archived = ReadEntitiesMut(cursor, 'End-of-ASM-data')
    return JournalModel(header, stamp, len(active), active + archived, stream, states)
