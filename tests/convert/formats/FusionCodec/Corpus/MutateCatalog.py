from dataclasses import replace as ReplaceValue
from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile
from tests.convert.formats.FusionCodec.Corpus.PickUnused import PickUnused

KRootPath = FilePath(__file__).resolve().parents[5]


def MutateCatalog(FileName: str, ChangeKind: str) -> bytes:
    Source = ReadCorpusFile(FileName)
    Target = (
        PickUnused(Source)
        if ChangeKind == "base"
        else next(Entry for Entry in Source.Metadata.Classes if Entry.OwnerIds)
    )
    Unknown = "00000000-0000-0000-0000-000000000001"
    Changed = (
        ReplaceValue(Target, ClassGuid=Unknown)
        if ChangeKind == "class"
        else (
            ReplaceValue(Target, BaseGuid=Unknown)
            if ChangeKind == "base"
            else ReplaceValue(Target, SchemaVersion=0xFFFFFFFF)
        )
    )
    Classes = tuple(
        Changed if Entry == Target else Entry for Entry in Source.Metadata.Classes
    )
    BulkData, MetaData = EmitSegment(
        ReplaceValue(Source.Metadata, Classes=Classes), Source.Records
    )
    assert BulkData == Source.BulkData
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
