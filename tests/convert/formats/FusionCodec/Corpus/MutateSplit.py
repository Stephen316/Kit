from dataclasses import replace as ReplaceValue
from io import BytesIO
from pathlib import Path as FilePath
from struct import pack as PackValue
from zipfile import ZipFile

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile

KRootPath = FilePath(__file__).resolve().parents[5]


def MutateSplit(FileName: str, Sequence: int, TotalCount: int) -> bytes:
    Source = ReadCorpusFile(FileName)
    Target = next(
        Record
        for Record in Source.Records
        if Record.IsPrimary and Record.ObjectId == 437
    )
    Original = PackValue("<iQQIIIQ", 3, 114, 0, 0, 1, 2, 0)
    Altered = PackValue("<iQQIIIQ", 3, 114, 0, 0, Sequence, TotalCount, 0)
    assert Target.Payload.count(Original) == 1
    Changed = ReplaceValue(Target, Payload=Target.Payload.replace(Original, Altered))
    Records = tuple(
        Changed if Record == Target else Record for Record in Source.Records
    )
    BulkData, MetaData = EmitSegment(Source.Metadata, Records)
    assert len(BulkData) == len(Source.BulkData)
    assert MetaData == Source.MetaData
    Replacements = {
        KDesignPrefix + "BulkStream.dat": BulkData,
        KDesignPrefix + "MetaStream.dat": MetaData,
    }
    Buffer = BytesIO()
    with ZipFile(KRootPath / FileName) as Archive, ZipFile(Buffer, "w") as Output:
        for Entry in Archive.infolist():
            Content = (
                Replacements[Entry.filename]
                if Entry.filename in Replacements
                else Archive.read(Entry)
            )
            Output.writestr(Entry, Content)
    return Buffer.getvalue()
