import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from Records import label

OPERATIONS = ("LockPath", "DefinePool", "DefineResource", "SubmitJobs", "BindInput", "ClaimJob", "RenewLease", "FinishJob", "FetchInput", "ReadStatus")


def copy_verified(source, destination, sha256):
    hasher = hashlib.sha256()
    count = 0
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with Path(source).open("rb") as reader, os.fdopen(descriptor, "wb") as writer:
        while chunk := reader.read(1024 * 1024):
            count += len(chunk)
            if count > 256 * 1024 * 1024:
                raise ValueError("input artifact exceeds 256 MiB")
            hasher.update(chunk)
            writer.write(chunk)
        writer.flush()
        os.fsync(writer.fileno())
    if hasher.hexdigest() != sha256:
        raise ValueError("input copy does not match its digest")
    return count


def without_token(record):
    return {key: value for key, value in record.items() if key != "lease_token"}


class A03Adapter:
    def __init__(self, options):
        if set(options) != {"store"} or not isinstance(options["store"], str):
            raise ValueError("the a03 adapter takes only a store path")
        self.store = Path(options["store"]).resolve()
        self.command = [sys.executable, str(Path(__file__).with_name("Controller.py")), "--store", str(self.store)]

    def Invoke(self, *items, stale=False):
        result = subprocess.run(self.command + [str(item) for item in items], capture_output=True, text=True, timeout=120, check=False)
        if stale and result.returncode == 3:
            return None
        if result.returncode != 0:
            raise ValueError(f"a03 {items[0]} failed: {result.stderr.strip()[-2048:]}")
        return json.loads(result.stdout)

    def LockPath(self):
        return self.store / "supervisor.lock"

    def DefinePool(self, name, kinds):
        return self.Invoke("pool", name, *[part for kind in kinds for part in ("--kind", kind)])

    def DefineResource(self, name, capacity):
        return self.Invoke("resource", name, "--capacity", capacity)

    def SubmitJobs(self, path):
        return self.Invoke("submit-batch", path)

    def BindInput(self, name, path):
        return self.Invoke("bind", name, path)

    def ClaimJob(self, pool, worker, path):
        response = self.Invoke("claim", "--worker", worker, "--pool", pool, "--claim-file", path)
        if response["job"] is None:
            return None
        return without_token(json.loads(Path(path).read_text(encoding="utf-8")))

    def RenewLease(self, path):
        response = self.Invoke("heartbeat", "--lease", path, stale=True)
        return {"stale": True} if response is None else {"stale": False, "lease_until": response["lease_until"], "deadline": response["deadline"]}

    def FinishJob(self, path, outcome, result, reason):
        return {"stale": self.Invoke("finish", "--lease", path, "--result", result, "--outcome", outcome, "--reason", reason, stale=True) is None}

    def FetchInput(self, sha256, destination):
        response = self.Invoke("artifact", sha256)
        return copy_verified(response["path"], destination, sha256)

    def ReadStatus(self, job=None, after=None):
        items = ["status"]
        if job is not None:
            items += ["--job", label(job)]
        if after is not None:
            items += ["--after", label(after)]
        return self.Invoke(*items)


def load_adapter(config, root):
    if not isinstance(config, dict):
        raise ValueError("controller configuration must be an object")
    if config.get("adapter") == "a03":
        return A03Adapter({key: value for key, value in config.items() if key != "adapter"})
    if set(config) != {"module", "class", "options"} or not isinstance(config["options"], dict):
        raise ValueError("controller needs adapter a03, or a module, class and options")
    path = Path(config["module"])
    path = (path if path.is_absolute() else Path(root) / path).resolve()
    specification = importlib.util.spec_from_file_location(f"controller_adapter_{hashlib.sha256(str(path).encode()).hexdigest()[:16]}", path)
    if specification is None or specification.loader is None or not path.is_file():
        raise ValueError("controller adapter module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    adapter = getattr(module, config["class"])(config["options"])
    missing = [name for name in OPERATIONS if not callable(getattr(adapter, name, None))]
    if missing:
        raise ValueError(f"controller adapter lacks {', '.join(missing)}")
    return adapter
