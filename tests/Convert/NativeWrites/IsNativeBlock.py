from collections.abc import Callable
from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory

from pytest import raises as RaisesError

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.Features.FeatureKinds import NativeFeature


# native refusal scenarios need consistent checks across public and adapter write routes
def IsNativeBlock(
    Document: CadDocument,
    WriteAction: Callable[[CadDocument, KTargetType, WriteOptions], WriteResult],
    SuffixText: str,
    ErrorText: str = "native-only feature definitions",
    OptionsData: WriteOptions | None = None,
) -> bool:
    if not any(
        isinstance(StepValue.definition, NativeFeature)
        for PartValue in WalkDocuments(Document)
        for StepValue in PartValue.feature_timeline
    ):
        return False
    with TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath) / f"Target{SuffixText}"
        _ = TargetPath.write_bytes(b"existing destination")
        Binary = ByteStream(b"existing stream")
        for Target in (TargetPath, Binary):
            with RaisesError(ValueError, match=ErrorText):
                _ = WriteAction(
                    Document, Target, OptionsData or WriteOptions(overwrite=True)
                )
        assert TargetPath.read_bytes() == b"existing destination"
        assert Binary.getvalue() == b"existing stream"
    return True
