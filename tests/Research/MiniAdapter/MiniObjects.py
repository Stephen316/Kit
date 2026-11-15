import hashlib as Hashing
import os as OsLayer
import secrets as Secrets
from pathlib import Path as FilePath
from shutil import copyfileobj as CopyFileObject

from tests.Research.MiniAdapter.MiniState import MiniState


# the fixture requires immutable content storage so claims and results can be verified independently
class MiniObjects(MiniState):

    # content identity must be shared across request retries without duplicating stored evidence
    def StoreBytes(self, Content: bytes) -> str:
        Digest = Hashing.sha256(Content).hexdigest()
        TargetPath = self.RootPath / "objects" / Digest
        if not TargetPath.exists():
            StagePath = self.RootPath / "objects" / f".{Secrets.token_hex(8)}"
            _ = StagePath.write_bytes(Content)
            OsLayer.replace(StagePath, TargetPath)
        return Digest

    # named input bindings must refer to durable content available to later supervisor sessions
    def BindInput(self, BindName: str, InputPath: FilePath) -> dict[str, object]:
        Digest = self.StoreBytes(FilePath(InputPath).read_bytes())
        with self.OpenState() as Current:
            Current.Bindings[BindName] = Digest
        return {"name": BindName, "sha256": Digest}

    # the supervisor must receive only the bytes represented by the claimed immutable digest
    def FetchInput(self, Digest: str, TargetPath: FilePath) -> int:
        SourcePath = self.RootPath / "objects" / Digest
        Content = SourcePath.read_bytes()
        if Hashing.sha256(Content).hexdigest() != Digest:
            raise ValueError("input object does not match its digest")
        with SourcePath.open("rb") as Source, open(TargetPath, "xb") as Output:
            CopyFileObject(Source, Output)
        return len(Content)
