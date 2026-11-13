import hashlib
import os
import re
import tempfile
from pathlib import Path

from Records import canonical


class Artifacts:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if (self.root / "objects").is_symlink():
            raise ValueError("artifact directory cannot be a symbolic link")
        self.objects = self.root / "objects"
        self.objects.mkdir(exist_ok=True, mode=0o700)

    def path(self, sha256):
        if not isinstance(sha256, str) or not re.fullmatch("[0-9a-f]{64}", sha256):
            raise ValueError("artifact digest must be a lowercase SHA-256")
        path = self.objects / sha256[:2] / sha256
        if self.objects.is_symlink() or path.parent.is_symlink() or path.is_symlink():
            raise ValueError("artifact paths cannot be symbolic links")
        return path

    def verify(self, sha256):
        path = self.path(sha256)
        hasher = hashlib.sha256()
        count = 0
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                count += len(chunk)
                if count > 256 * 1024 * 1024:
                    raise ValueError("artifact exceeds 256 MiB")
                hasher.update(chunk)
        if hasher.hexdigest() != sha256:
            raise ValueError("artifact integrity mismatch")
        return count

    def publish(self, staged, sha256):
        target = self.path(sha256)
        target.parent.mkdir(exist_ok=True, mode=0o700)
        try:
            os.link(staged, target)
        except FileExistsError:
            self.verify(sha256)
        if os.name == "posix":
            for directory in (target.parent, self.objects, self.root, self.root.parent):
                descriptor = os.open(directory, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        return sha256

    def put_file(self, path):
        path = Path(path)
        if not path.is_file():
            raise ValueError("artifact input must be a regular file")
        staged = None
        try:
            with path.open("rb") as source, tempfile.NamedTemporaryFile(dir=self.objects, delete=False) as output:
                staged = Path(output.name)
                hasher = hashlib.sha256()
                count = 0
                while chunk := source.read(1024 * 1024):
                    count += len(chunk)
                    if count > 256 * 1024 * 1024:
                        raise ValueError("artifact exceeds 256 MiB")
                    hasher.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            return self.publish(staged, hasher.hexdigest())
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)

    def put_record(self, record):
        content = canonical(record).encode("utf-8")
        staged = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.objects, delete=False) as output:
                staged = Path(output.name)
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            return self.publish(staged, hashlib.sha256(content).hexdigest())
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)
