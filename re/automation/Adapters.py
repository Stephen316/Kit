import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from GroupClaims import read_group
from Records import canonical, label, read_record
from OutputManifest import InvalidOutput

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
    OutputArtifactsVersion = 1
    GroupClaimsVersion = 1

    def __init__(self, options):
        if set(options) != {"store"} or not isinstance(options["store"], str):
            raise ValueError("the a03 adapter takes only a store path")
        self.store = Path(options["store"]).resolve()
        self.command = [sys.executable, str(Path(__file__).with_name("Controller.py")), "--store", str(self.store)]

    def Invoke(self, *items, stale=False):
        result = subprocess.run(self.command + [str(item) for item in items], capture_output=True, text=True, timeout=120, check=False)
        if stale and result.returncode == 3:
            return None
        if items[0] == "finish" and result.returncode == 4:
            raise InvalidOutput(result.stderr.strip()[-2048:])
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

    def ClaimGroup(self, pool, worker, path, kinds):
        registry = Path(path).with_suffix(".registry")
        descriptor = os.open(registry, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(canonical({"group_registry_version": 1, "kinds": kinds}))
            response = self.Invoke("claim-group", "--worker", worker, "--pool", pool, "--registry", registry, "--claim-dir", path)
        finally:
            registry.unlink(missing_ok=True)
        return [without_token(item) for item in read_group(path)] if response["count"] else None

    def RenewGroup(self, path):
        response = self.Invoke("heartbeat-group", "--lease", path)
        members = response.get("members")
        if not isinstance(members, list) or not 1 <= len(members) <= 20 or any(not isinstance(item, dict) or type(item.get("stale")) is not bool for item in members) or type(response.get("stale")) is not bool or response["stale"] != any(item["stale"] for item in members):
            raise ValueError("a03 returned an invalid group renewal response")
        return response

    def FinishGroup(self, path, result):
        response = self.Invoke("finish-group", "--lease", path, "--result", result)
        members = response.get("members")
        if not isinstance(members, list) or len(members) != len(read_group(path)) or any(not isinstance(item, dict) or type(item.get("stale")) is not bool for item in members):
            raise ValueError("a03 returned an invalid group finish response")
        return response

    def RenewLease(self, path):
        response = self.Invoke("heartbeat", "--lease", path, stale=True)
        return {"stale": True} if response is None else {"stale": False, "lease_until": response["lease_until"], "deadline": response["deadline"]}

    def FinishJob(self, path, outcome, result, reason):
        payload = read_record(result)
        declared = payload.get("result")
        output_args = ["--output-root", Path(result).parent / "work"] if isinstance(declared, dict) and "artifacts" in declared else []
        return {"stale": self.Invoke("finish", "--lease", path, "--result", result, "--outcome", outcome, "--reason", reason, *output_args, stale=True) is None}

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
    capability = getattr(adapter, "GroupClaimsVersion", None)
    if capability is not None and (type(capability) is not int or capability != 1 or any(not callable(getattr(adapter, name, None)) for name in ("ClaimGroup", "RenewGroup", "FinishGroup"))):
        raise ValueError("group-capable adapter must provide protocol 1 ClaimGroup, RenewGroup and FinishGroup")
    return adapter
