import hashlib as Hashing
import os as OsLayer
import secrets as Secrets
from pathlib import Path as FilePath
from shutil import copyfileobj as CopyFileObject

from tests.Research.MiniAdapter.MiniState import MiniState


class MiniObjects(MiniState):
    def StoreBytes(self, Content: bytes) -> str:
        Digest = Hashing.sha256(Content).hexdigest()
        TargetPath = self.RootPath / "objects" / Digest
        if not TargetPath.exists():
            StagePath = self.RootPath / "objects" / f".{Secrets.token_hex(8)}"
            _ = StagePath.write_bytes(Content)
            OsLayer.replace(StagePath, TargetPath)
        return Digest

    def BindInput(self, BindName: str, InputPath: FilePath) -> dict[str, object]:
        Digest = self.StoreBytes(FilePath(InputPath).read_bytes())
        with self.OpenState() as Current:
            Current.Bindings[BindName] = Digest
        return {"name": BindName, "sha256": Digest}

    def FetchInput(self, Digest: str, TargetPath: FilePath) -> int:
        SourcePath = self.RootPath / "objects" / Digest
        Content = SourcePath.read_bytes()
        if Hashing.sha256(Content).hexdigest() != Digest:
            raise ValueError("input object does not match its digest")
        with SourcePath.open("rb") as Source, open(TargetPath, "xb") as Output:
            CopyFileObject(Source, Output)
        return len(Content)
