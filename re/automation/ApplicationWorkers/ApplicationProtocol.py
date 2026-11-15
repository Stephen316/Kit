import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import time

MAX_BYTES = 256 * 1024 * 1024
PROTOCOL = "re/automation/ApplicationWorkers/ApplicationProtocol.py"
COUNTERPART = "re/automation/ApplicationWorkers/FusionCounterpart.py"
TOOL = "re/automation/PairedCaptures/FusionFreshProcess.py"
BOOTSTRAP = "re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py"
INPUTS = {"re/automation/PairedCaptures/FusionCapture.py", "re/automation/PairedCaptures/FusionBindings.py",
          "re/automation/PairSpecs.json", "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"}


class WaitingApplication(ValueError):
    pass


def require(value, reason):
    if not value:
        raise ValueError(reason)


def directory(path, create=False):
    path = Path(os.path.abspath(path))
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    for ancestor in (*reversed(path.parents), path):
        info = ancestor.lstat()
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
                and not getattr(info, "st_file_attributes", 0) & 0x400,
                "application paths cannot contain links or reparse points")
    if os.name == "posix":
        info = path.stat()
        require(info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o077,
                "application endpoint must be private to its owner")
    return path


def file_bytes(path, limit=1024 * 1024):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
            and not getattr(before, "st_file_attributes", 0) & 0x400,
            "application records must be regular files without links")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as source:
        opened = os.fstat(source.fileno())
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1, "application input is not a singly linked regular file")
        require((before.st_dev, before.st_ino, before.st_mode) == (opened.st_dev, opened.st_ino, opened.st_mode),
                "application input changed while opening")
        content = source.read(limit + 1)
        after = os.fstat(source.fileno())
    require(len(content) <= limit, "application input exceeds its byte limit")
    require((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns, opened.st_nlink)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink)
            == (path.stat(follow_symlinks=False).st_dev, path.stat(follow_symlinks=False).st_ino,
                path.stat(follow_symlinks=False).st_size, path.stat(follow_symlinks=False).st_mtime_ns,
                path.stat(follow_symlinks=False).st_ctime_ns, path.stat(follow_symlinks=False).st_nlink),
            "application input changed while reading")
    return content


def record(path):
    try:
        value = json.loads(file_bytes(path))
    except RecursionError as error:
        raise ValueError("application record exceeds the supported nesting") from error
    require(isinstance(value, dict), "application record must be an object")
    return value


def encoded(value):
    content = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    require(len(content) <= 1024 * 1024, "application record exceeds 1 MiB")
    return content


def write_new(path, content):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(content)
        target.flush()
        os.fsync(target.fileno())


def write_record(path, value, replace=False):
    path = Path(path)
    if not replace:
        write_new(path, encoded(value))
        return
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}")
    try:
        write_new(temporary, encoded(value))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def pin(path, relative):
    content = file_bytes(path, MAX_BYTES)
    return {"path": relative, "sha256": sha256(content), "size_bytes": len(content)}


def copy_pin(source, destination, expected):
    content = file_bytes(source, MAX_BYTES)
    require(sha256(content) == expected["sha256"] and len(content) == expected["size_bytes"], "application input pin mismatch")
    write_new(destination, content)


def identity(pid):
    require(os.name == "posix", "application process identity currently requires a POSIX host")
    require(type(pid) is int and pid > 0, "invalid application process id")
    result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True,
                            check=False, timeout=5, env=dict(os.environ, LC_ALL="C", TZ="UTC"))
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    require(result.returncode == 0 and result.stdout.strip(), "application process identity unavailable")
    return {"pid": pid, "started": result.stdout.strip()}


def configuration(path):
    value = record(path)
    require(set(value) == {"version", "installation", "application", "endpoint", "source_root", "source_revision"}
            and value["version"] == 1, "invalid application installation configuration")
    require(isinstance(value["installation"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value["installation"]), "invalid installation identity")
    require(value["application"] in ("fusion", "solidworks"), "unsupported application installation")
    require(isinstance(value["source_revision"], str) and re.fullmatch("[0-9a-f]{40}", value["source_revision"]), "installation needs an exact source revision")
    require(all(isinstance(value[key], str) and Path(value[key]).is_absolute() for key in ("endpoint", "source_root")), "installation paths must be absolute")
    return value


def committed_bytes(config, relative):
    require(relative in {PROTOCOL, COUNTERPART, TOOL, BOOTSTRAP, *INPUTS}, "unapproved application source path")
    root = Path(config["source_root"])
    source = subprocess.run(["git", "-C", str(root), "show", f"{config['source_revision']}:{relative}"],
                            capture_output=True, check=False, timeout=15)
    require(source.returncode == 0 and 0 < len(source.stdout) <= MAX_BYTES, "pinned application input is unavailable")
    require(file_bytes(root / relative, MAX_BYTES) == source.stdout, "application input differs from the installed trusted revision")
    return source.stdout


def load_pinned(config, relative):
    require(relative in (PROTOCOL, COUNTERPART, TOOL), "unapproved application helper")
    root = Path(config["source_root"])
    source = committed_bytes(config, relative)
    require(len(source) <= 1024 * 1024, "application executable source exceeds 1 MiB")
    scope = {"__name__": "__kit_pinned_application__", "__file__": str(root / relative)}
    exec(compile(source, str(root / relative), "exec"), scope)
    scope["_source_pin"] = {"path": relative, "sha256": sha256(source), "size_bytes": len(source), "revision": config["source_revision"]}
    return scope


def validate_request(value, config, job_id, operation):
    require(set(value) == {"version", "installation", "source_revision", "job_id", "operation", "nonce", "client", "deadline", "body"}
            and value["version"] == 1 and value["installation"] == config["installation"]
            and value["source_revision"] == config["source_revision"] and value["job_id"] == job_id
            and value["operation"] == operation and operation in ("probe", "phase"), "request does not match the pinned installation protocol")
    require(isinstance(value["nonce"], str) and re.fullmatch("[0-9a-f]{48}", value["nonce"]), "invalid application challenge")
    require(type(value["deadline"]) in (int, float) and 0 < value["deadline"] <= time.time() + 3600, "application deadline is invalid")
    require(isinstance(value["client"], dict) and set(value["client"]) == {"pid", "started"}
            and type(value["client"]["pid"]) is int and value["client"]["pid"] > 0
            and isinstance(value["client"]["started"], str) and len(value["client"]["started"]) <= 128, "invalid requesting process identity")
    require(isinstance(value["body"], dict), "invalid application request body")


class QueueClient:
    def __init__(self, config, deadline, provider="autodesk.fusion.addin"):
        import fcntl

        self.config = config
        self.deadline = deadline
        self.provider = provider
        self.root = directory(config["endpoint"])
        self.lock = os.open(self.root / "dispatch.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (self.root / "fence.json").exists():
                raise WaitingApplication("installation is fenced pending its external owner's restart or recovery")
            self.job_id = secrets.token_hex(16)
            self.directory = directory(self.root / "jobs" / self.job_id, True)
            self.client = identity(os.getpid())
        except BaseException:
            os.close(self.lock)
            raise
        self.host = None
        self.pending = False

    def close(self):
        if self.pending:
            self.cancel("requesting worker stopped before application completion")
        os.close(self.lock)

    def cancel(self, reason):
        write_record(self.directory / "cancel.json", {"reason": reason[:2048], "at": time.time()}, replace=True)
        write_record(self.root / "fence.json", {"installation": self.config["installation"], "job_id": self.job_id,
                     "reason": "quarantined", "host": self.host, "at": time.time()}, replace=True)

    def remove_completed(self):
        require(not self.pending and record(self.directory / "phase.done")["status"] == "completed",
                "only a completed dispatch spool may be removed")
        directory(self.directory)
        shutil.rmtree(self.directory)

    def call(self, operation, body):
        deadline = min(self.deadline, time.time() + 30) if operation == "probe" else self.deadline
        request = {"version": 1, "installation": self.config["installation"], "source_revision": self.config["source_revision"],
                   "job_id": self.job_id, "operation": operation, "nonce": secrets.token_hex(24), "client": self.client,
                   "deadline": deadline, "body": body}
        request_path = self.directory / f"{operation}.request"
        request_hash = sha256(encoded(request))
        write_record(request_path, request)
        self.pending = True
        response_path = self.directory / f"{operation}.done"
        while time.time() < deadline:
            if response_path.exists():
                response = record(response_path)
                require(response.get("version") == 1 and response.get("request_sha256") == request_hash
                        and response.get("nonce") == request["nonce"] and response.get("installation") == self.config["installation"]
                        and response.get("source_revision") == self.config["source_revision"] and response.get("provider") == self.provider,
                        "application response is not bound to this request")
                require(response.get("host") == identity(response["host"]["pid"]), "application response process exited or changed")
                if self.host is not None:
                    require(response["host"] == self.host, "application process changed within one dispatch")
                self.host = response["host"]
                require(time.time() < deadline, "application response arrived after the dispatch deadline")
                self.pending = False
                if response["status"] != "completed":
                    raise WaitingApplication(str(response.get("reason", "application is unavailable")))
                return response
            time.sleep(0.05)
        self.cancel("application challenge or operation exceeded its request deadline")
        raise WaitingApplication("application did not answer before its bounded deadline; installation quarantined")


class HostQueue:
    def __init__(self, config, provider="autodesk.fusion.addin"):
        import fcntl

        self.config = config
        self.provider = provider
        self.root = directory(config["endpoint"], True)
        directory(self.root / "jobs", True)
        self.lock = os.open(self.root / "host.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(self.lock)
            raise
        try:
            self.host = identity(os.getpid())
            self.loaded_sources = {}
            self.fenced()
        except BaseException:
            os.close(self.lock)
            raise

    def close(self):
        os.close(self.lock)

    def fenced(self):
        path = self.root / "fence.json"
        if not path.exists():
            return False
        value = record(path)
        old = value.get("host")
        if isinstance(old, dict) and old != self.host and identity(old["pid"]) is None:
            path.unlink()
            return False
        return True

    def legacy_available(self):
        if self.fenced():
            return False
        grant_path = self.root / "grant.json"
        if not grant_path.exists():
            return True
        grant = record(grant_path)
        return time.time() >= grant["until"] or identity(grant["client"]["pid"]) != grant["client"]

    def next_path(self):
        return next(iter(sorted((self.root / "jobs").glob("*/*.request"))), None)

    def accept(self, request_path):
        request_path = Path(request_path)
        require(request_path.parent.parent == self.root / "jobs" and re.fullmatch("[0-9a-f]{32}", request_path.parent.name), "request is outside the private spool")
        directory(request_path.parent)
        operation = request_path.stem
        value = record(request_path)
        validate_request(value, self.config, request_path.parent.name, operation)
        running = request_path.with_suffix(".running")
        os.rename(request_path, running)
        return value, running

    def perform(self, request_path, action):
        try:
            value, running = self.accept(request_path)
        except (ValueError, OSError, KeyError, TypeError) as error:
            path = Path(request_path)
            if path.exists() and path.parent.parent == self.root / "jobs":
                os.rename(path, path.with_suffix(".rejected"))
                write_record(path.with_suffix(".error"), {"reason": f"{type(error).__name__}: {error}"[:2048]})
            return None
        if self.fenced() or time.time() >= value["deadline"] or identity(value["client"]["pid"]) != value["client"] or (running.parent / "cancel.json").exists():
            return self.finish(value, running, "waiting_application", "installation is fenced, or its request expired")
        try:
            status, reason, proof, files = action(value, running.parent)
        except Exception as error:
            write_record(self.root / "fence.json", {"installation": self.config["installation"], "job_id": value["job_id"],
                         "reason": "quarantined", "host": self.host, "at": time.time()}, replace=True)
            return self.finish(value, running, "waiting_application", f"{type(error).__name__}: {error}")
        return self.finish(value, running, status, reason, proof, files)

    def finish(self, value, running, status, reason, proof=None, files=None):
        alive = identity(value["client"]["pid"]) == value["client"]
        if time.time() >= value["deadline"] or not alive or (running.parent / "cancel.json").exists():
            status, reason, proof, files = "expired", "request expired or its process exited", None, None
            write_record(self.root / "fence.json", {"installation": self.config["installation"], "job_id": value["job_id"],
                         "reason": "quarantined", "host": self.host, "at": time.time()}, replace=True)
        response = {"version": 1, "installation": self.config["installation"], "source_revision": self.config["source_revision"],
                    "provider": self.provider, "host": self.host, "request_sha256": sha256(encoded(value)), "nonce": value["nonce"],
                    "status": status, "reason": reason[:2048], "proof": proof, "files": files or {}, "finished_at": time.time()}
        running.unlink()
        write_record(running.with_suffix(".done"), response)
        return response

    def restart_handoff(self, value, plan_hash):
        handoff = {"installation": self.config["installation"], "job_id": value["job_id"], "reason": "restart_required",
                   "host": self.host, "plan_sha256": plan_hash, "at": time.time(), "owner": "external_application_owner"}
        write_record(self.root / "fence.json", handoff, replace=True)
        return handoff
