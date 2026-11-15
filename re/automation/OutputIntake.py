import hashlib
import os
import tempfile
from pathlib import Path

from OutputFiles import open_output
from OutputManifest import InvalidOutput, output_manifest


class OutputIntake:
    def __init__(self, objects, root, manifest):
        self.objects = objects
        self.root = root
        self.manifest = output_manifest(manifest)
        self.staged = []

    def __enter__(self):
        try:
            seen = set()
            for role, item in sorted(self.manifest.items()):
                with open_output(self.root, item["path"]) as source, tempfile.NamedTemporaryFile(dir=self.objects.objects, delete=False) as output:
                    staged = Path(output.name)
                    self.staged.append((role, staged, item))
                    info = os.fstat(source.fileno())
                    identity = (info.st_dev, info.st_ino)
                    if identity in seen:
                        raise ValueError("output roles must identify distinct files")
                    seen.add(identity)
                    hasher = hashlib.sha256()
                    count = 0
                    while chunk := source.read(min(1024 * 1024, item["size_bytes"] - count + 1)):
                        count += len(chunk)
                        if count > item["size_bytes"]:
                            raise ValueError("output exceeds its declared size")
                        hasher.update(chunk)
                        output.write(chunk)
                    if count != item["size_bytes"] or hasher.hexdigest() != item["sha256"]:
                        raise ValueError("output does not match its declared size and digest")
                    output.flush()
                    os.fsync(output.fileno())
            return self
        except (OSError, ValueError) as error:
            self.__exit__(None, None, None)
            raise InvalidOutput(str(error)) from error
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def publish(self):
        return {role: {"sha256": self.objects.publish(path, item["sha256"]), "size_bytes": item["size_bytes"]} for role, path, item in self.staged}

    def __exit__(self, kind, value, traceback):
        for _, path, _ in self.staged:
            path.unlink(missing_ok=True)
