import ctypes
from contextlib import ExitStack, contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import time

MAX_BYTES = 256 * 1024 * 1024
MAX_SPOOL_BYTES = 520 * 1024 * 1024
MAX_SPOOL_FILES = 32
ACKNOWLEDGEMENT = "acceptance-journal.json"
CANCEL_REASON = "requesting worker stopped before application completion"
FUSION_PROVIDER = "autodesk.fusion.addin"
PROTOCOL = "re/automation/ApplicationWorkers/ApplicationProtocol.py"
RESTART_GRANT = "re/automation/ApplicationWorkers/FusionRestartGrant.py"
MAC_REPLACEMENT_LAUNCH = "re/automation/ApplicationWorkers/MacReplacementLaunch.swift"
COUNTERPART = "re/automation/ApplicationWorkers/FusionCounterpart.py"
TOOL = "re/automation/PairedCaptures/FusionFreshProcess.py"
SCOPE_TOOL = "re/automation/PairedCaptures/ScopeControl/FusionScopeControl.py"
SCOPE_INPUTS = {
    "re/automation/PairedCaptures/ScopeControl/FusionScopeModel.py",
    "re/automation/PairedCaptures/ScopeControl/ScopeControlSpec.json",
}
BOOTSTRAP = "re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py"

# windows embedded python must load these exact helpers before reading records
WINDOWS_HELPERS = {
    "windows_identity": "re/automation/ApplicationWorkers/WindowsIdentity.py",
    "windows_records": "re/automation/ApplicationWorkers/WindowsRecords.py",
}

# only embedded windows dispatch supplies helper functions from private pinned namespaces
WINDOWS_API = {}

# the embedded addin retains the absolute git executable selected before source loading
WINDOWS_GIT = None

INPUTS = {"re/automation/PairedCaptures/FusionCapture.py", "re/automation/PairedCaptures/FusionBindings.py",
          "re/automation/PairSpecs.json", "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
          "re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py",
          "re/automation/ApplicationWorkers/RearmSolidWorks.py",
          "re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1"}


class WaitingApplication(ValueError):
    pass


class ApplicationTimeout(WaitingApplication):
    def __init__(self, request):
        super().__init__("application did not answer before its bounded deadline; installation quarantined")
        self.request = request


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
    if os.name == "nt":
        open_record = windows_function("windows_records", "open_record")

        with open_record(path) as source:
            content = source.read(limit + 1)
            require(len(content) <= limit, "application input exceeds its byte limit")
        return content
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
    final = path.stat(follow_symlinks=False)
    require((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns, opened.st_nlink)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink)
            == (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns, final.st_ctime_ns, final.st_nlink),
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


def stage_bytes(path, content):
    path = Path(path)
    require(isinstance(content, bytes) and len(content) <= MAX_BYTES, "application publication exceeds its byte limit")
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(16)}")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
            info = os.fstat(target.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "application publication must remain singly linked")
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def exclusive_rename(source, destination):
    if os.name == "nt":
        os.rename(source, destination)
        return
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux"):
        rename = getattr(library, "renameat2", None)
        require(rename is not None, "atomic application publication requires libc renameat2")
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
    elif sys.platform == "darwin":
        rename = getattr(library, "renamex_np", None)
        require(rename is not None, "atomic application publication requires libc renamex_np")
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(os.fsencode(source), os.fsencode(destination), 4)
    else:
        raise OSError(errno.ENOTSUP, "atomic exclusive application publication is unsupported on this platform")
    if result != 0:
        code = ctypes.get_errno()
        if code in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP}:
            raise OSError(code, "filesystem or kernel does not support atomic exclusive application publication", str(destination))
        raise OSError(code, os.strerror(code), str(destination))


def sync_directory(path):
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_new(path, content):
    path = Path(path)
    temporary = stage_bytes(path, content)
    try:
        exclusive_rename(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def write_record(path, value, replace=False):
    path = Path(path)
    if not replace:
        write_new(path, encoded(value))
        return
    temporary = stage_bytes(path, encoded(value))
    try:
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def request_link(value):
    return {"queue_job_id": value["job_id"], "request_sha256": sha256(encoded(value)),
            "nonce": value["nonce"], "client": value["client"]}


def pin(path, relative):
    content = file_bytes(path, MAX_BYTES)
    return {"path": relative, "sha256": sha256(content), "size_bytes": len(content)}


def copy_pin(source, destination, expected):
    content = file_bytes(source, MAX_BYTES)
    require(sha256(content) == expected["sha256"] and len(content) == expected["size_bytes"], "application input pin mismatch")
    write_new(destination, content)


def check_spool(root, reserve_bytes=0, reserve_files=0):
    total, count = reserve_bytes, reserve_files
    for path in Path(root).rglob("*"):
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                "application spool cannot contain links or reparse points")
        if stat.S_ISDIR(info.st_mode):
            continue
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "application spool contains a non-regular or multiply linked file")
        count += 1
        total += info.st_size
        require(count <= MAX_SPOOL_FILES and total <= MAX_SPOOL_BYTES, "application spool exceeds 32 files or 520 MiB")
    return {"files": count, "size_bytes": total}


def identity(pid, *, timeout=5):
    require(type(pid) is int and pid > 0, "invalid application process id")
    if os.name == "nt":
        process_start = windows_function("windows_identity", "process_start")

        started = process_start(pid)
        return None if started is None else {"pid": pid, "started": started}
    require(os.name == "posix", "application process identity requires Windows or POSIX")
    result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True,
                            check=False, timeout=timeout, env=dict(os.environ, LC_ALL="C", TZ="UTC"))
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    require(result.returncode == 0 and result.stdout.strip(), "application process identity unavailable")
    return {"pid": pid, "started": result.stdout.strip()}


@contextmanager
def owner_lock(path):
    if os.name == "nt":
        open_owner_lock = windows_function("windows_records", "open_owner_lock")

        with open_owner_lock(path):
            yield
        return
    import fcntl

    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


# standard tools and the embedded addin share the same native file and process checks
def windows_function(role, name):
    if WINDOWS_API:
        return WINDOWS_API[role][name]
    if role == "windows_records":
        import WindowsRecords as module
    else:
        import WindowsIdentity as module
    return getattr(module, name)


# windows capture stays parked without an explicit owner installation setting
def windows_phase_a(config):
    return sys.platform == "win32" and config.get("application") == "fusion" and config.get("windows_phase_a") is True


# the request cannot vouch for its own token or its session
def peer_live(config, provider, peer):
    if windows_phase_a(config) and provider == FUSION_PROVIDER:
        return (isinstance(peer, dict) and set(peer) == {"pid", "started"}
                and windows_function("windows_identity", "peer_matches")(peer["pid"], peer["started"]))
    return identity(peer["pid"]) == peer


# reports retain exact windows process identity alongside the existing time field
def windows_process(peer):
    started = peer["started"]
    require(re.fullmatch(r"windows:[1-9][0-9]{0,19}", started), "invalid Windows process creation time")
    ticks = int(started.split(":")[1])
    return {"pid": peer["pid"], "started": started,
            "start_unix_seconds": ticks // 10_000_000 - 11_644_473_600}


def configuration(path):
    return validate_configuration(record(path))


def validate_configuration(value):
    require(isinstance(value, dict), "invalid application installation configuration")
    keys = {"version", "installation", "application", "endpoint", "source_root", "source_revision"}
    if "windows_phase_a" in value:
        require(windows_phase_a(value), "Windows Phase A opt-in requires a Windows Fusion installation")
        keys.add("windows_phase_a")
    require(set(value) == keys and value["version"] == 1, "invalid application installation configuration")
    require(isinstance(value["installation"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value["installation"]), "invalid installation identity")
    require(value["application"] in ("fusion", "solidworks"), "unsupported application installation")
    require(isinstance(value["source_revision"], str) and re.fullmatch("[0-9a-f]{40}", value["source_revision"]), "installation needs an exact source revision")
    require(all(isinstance(value[key], str) and Path(value[key]).is_absolute() for key in ("endpoint", "source_root")), "installation paths must be absolute")
    return value


# the windows dispatcher must never interpret a session directory as executable authority
def windows_git():
    if WINDOWS_GIT is not None:
        return WINDOWS_GIT
    for entry in os.get_exec_path():
        candidate = Path(entry.strip('"')) / "git.exe"
        if candidate.is_absolute() and not candidate.anchor.startswith("\\\\") and candidate.is_file():
            directory(candidate.parent)
            info = candidate.lstat()
            require(stat.S_ISREG(info.st_mode)
                    and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                    "Windows dispatch Git executable must be a local regular file")
            return str(candidate)
    raise ValueError("Windows dispatch requires trusted Git on an absolute PATH entry")


def committed_bytes(config, relative):
    require(
        relative
        in {PROTOCOL, COUNTERPART, TOOL, SCOPE_TOOL, BOOTSTRAP, RESTART_GRANT, MAC_REPLACEMENT_LAUNCH,
            *WINDOWS_HELPERS.values(), *INPUTS, *SCOPE_INPUTS},
        "unapproved application source path",
    )
    root = Path(config["source_root"])
    git = [windows_git(), "--no-replace-objects"] if windows_phase_a(config) else ["git"]
    source = subprocess.run([*git, "-C", str(root), "show", f"{config['source_revision']}:{relative}"],
                            capture_output=True, check=False, timeout=15)
    require(source.returncode == 0 and 0 < len(source.stdout) <= MAX_BYTES, "pinned application input is unavailable")
    require(file_bytes(root / relative, MAX_BYTES) == source.stdout, "application input differs from the installed trusted revision")
    return source.stdout


def load_pinned(config, relative):
    require(
        relative in (PROTOCOL, COUNTERPART, TOOL, SCOPE_TOOL, RESTART_GRANT),
        "unapproved application helper",
    )
    root = Path(config["source_root"])
    source = committed_bytes(config, relative)
    require(len(source) <= 1024 * 1024, "application executable source exceeds 1 MiB")
    scope = {"__name__": "__kit_pinned_application__", "__file__": str(root / relative)}
    exec(compile(source, str(root / relative), "exec"), scope)
    scope["_source_pin"] = source_pin(config, relative, source)
    return scope


# loaded code receipts must identify the byte extent and revision together
def source_pin(config, relative, source):
    return {"path": relative, "sha256": sha256(source), "size_bytes": len(source), "revision": config["source_revision"]}


# dispatch independently reconciles embedded helper and phase implementation bytes
def require_win_sources(config, sources):
    expected = {"bootstrap": BOOTSTRAP, "protocol": PROTOCOL, "counterpart": COUNTERPART,
                "tool": TOOL, **WINDOWS_HELPERS}
    require(sources == {
        role: source_pin(config, path, committed_bytes(config, path))
        for role, path in expected.items()
    }, "Windows Fusion loaded sources do not match the installed revision")


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
    def __init__(self, config, deadline, provider=FUSION_PROVIDER):
        self.config = config
        self.deadline = deadline
        self.provider = provider
        self.root = directory(config["endpoint"])
        self.lock = ExitStack()
        try:
            self.lock.enter_context(owner_lock(self.root / "dispatch.lock"))
            if os.path.lexists(self.root / "fence.json") or os.path.lexists(self.root / ACKNOWLEDGEMENT):
                raise WaitingApplication("installation is fenced pending controller acceptance or its external owner's recovery")
            spools = directory(self.root / "jobs", True)
            if any(spools.iterdir()):
                raise WaitingApplication("installation retains an unacknowledged spool; owner acceptance or recovery is required")
            self.job_id = secrets.token_hex(16)
            self.directory = directory(self.root / "jobs" / self.job_id, True)
            self.client = identity(os.getpid())
        except BaseException:
            self.lock.close()
            raise
        self.host = None
        self.pending = False

    def close(self):
        try:
            if self.pending:
                self.cancel(CANCEL_REASON)
        finally:
            self.lock.close()

    def cancel(self, reason):
        write_record(self.directory / "cancel.json", {"reason": reason[:2048], "at": time.time()}, replace=True)
        fence = self.root / "fence.json"
        if fence.exists() and record(fence).get("reason") == "acceptance_required":
            return
        write_record(self.root / "fence.json", {"installation": self.config["installation"], "job_id": self.job_id,
                     "reason": "quarantined", "host": self.host, "at": time.time()}, replace=True)

    def copy_files(self, destination, response):
        files = response["files"]
        require(isinstance(files, dict) and len(files) <= 63
                and sum(item["size_bytes"] for item in files.values()) <= MAX_BYTES, "invalid application output roster")
        artifacts = {}
        for role, item in files.items():
            relative = item["path"]
            require(isinstance(relative, str) and 1 <= len(relative) <= 4096 and not any(char in relative for char in "\\:\0")
                    and all(part and part not in (".", "..") for part in relative.split("/")), "application output escapes its spool")
            target = Path(destination) / relative
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            copy_pin(self.directory / relative, target, item)
            artifacts[role] = pin(target, relative)
        write_record(self.directory / "copied.json", {"status": "copied_pending_controller_acceptance", "artifacts": artifacts})
        check_spool(self.directory)
        return artifacts

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
                require(peer_live(self.config, self.provider, response["host"]),
                        "application response process exited or changed or failed owner admission")
                if self.host is not None:
                    require(response["host"] == self.host, "application process changed within one dispatch")
                self.host = response["host"]
                require(time.time() < deadline, "application response arrived after the dispatch deadline")
                self.pending = False
                if response["status"] != "completed":
                    raise WaitingApplication(str(response.get("reason", "application is unavailable")))
                return response
            time.sleep(0.05)
        try:
            self.cancel(CANCEL_REASON)
        except (OSError, ValueError) as error:
            self.pending = False
            raise WaitingApplication(
                "application reached its deadline and cancellation evidence could not be fully recorded"
            ) from error
        self.pending = False
        raise ApplicationTimeout(request)


def fusion_startup_loaded(config, sources):
    for role, path in (("bootstrap", BOOTSTRAP), ("protocol", PROTOCOL)):
        pin = sources.get(role)
        if not (isinstance(pin, dict) and set(pin) == {"path", "revision", "sha256", "size_bytes"}
                and pin["path"] == path and pin["revision"] == config["source_revision"]
                and isinstance(pin["sha256"], str) and re.fullmatch("[0-9a-f]{64}", pin["sha256"])
                and type(pin["size_bytes"]) is int and pin["size_bytes"] > 0):
            return False
    return True


class HostQueue:
    def __init__(self, config, provider=FUSION_PROVIDER):
        self.config = config
        self.provider = provider
        self.root = directory(config["endpoint"], not windows_phase_a(config))
        directory(self.root / "jobs", True)
        self.lock = ExitStack()
        try:
            self.lock.enter_context(owner_lock(self.root / "host.lock"))
            self.host = identity(os.getpid())
            self.loaded_sources = {}
            self.fenced()
        except BaseException:
            self.lock.close()
            raise

    def close(self):
        self.lock.close()

    def fenced(self):
        if os.path.lexists(self.root / ACKNOWLEDGEMENT):
            return True
        path = self.root / "fence.json"
        try:
            value = record(path)
        except FileNotFoundError:
            return False
        if value.get("reason") == "acceptance_required":
            return True
        if value.get("reason") == "restart_required" and self.provider == FUSION_PROVIDER:
            if (sys.platform == "win32" or value.get("installation") != self.config["installation"]
                    or not fusion_startup_loaded(self.config, self.loaded_sources)):
                return True
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
        if self.fenced() or time.time() >= value["deadline"] or not peer_live(self.config, self.provider, value["client"]) or (running.parent / "cancel.json").exists():
            return self.finish(value, running, "waiting_application", "installation is fenced, or its request expired")
        try:
            status, reason, proof, files = action(value, running.parent)
        except Exception as error:
            write_record(self.root / "fence.json", {"installation": self.config["installation"], "job_id": value["job_id"],
                         "reason": "quarantined", "host": self.host, "at": time.time()}, replace=True)
            return self.finish(value, running, "waiting_application", f"{type(error).__name__}: {error}")
        return self.finish(value, running, status, reason, proof, files)

    def finish(self, value, running, status, reason, proof=None, files=None):
        alive = peer_live(self.config, self.provider, value["client"])
        if time.time() >= value["deadline"] or not alive or (running.parent / "cancel.json").exists():
            status, reason, proof, files = "expired", "request expired or its process exited", None, None
            write_record(self.root / "fence.json", {"installation": self.config["installation"], "job_id": value["job_id"],
                         "reason": "quarantined", "host": self.host, "at": time.time()}, replace=True)
        if status == "completed" and value["operation"] == "phase":
            try:
                check_spool(running.parent, reserve_bytes=3 * 1024 * 1024, reserve_files=3)
                retained = {"installation": self.config["installation"], "job_id": value["job_id"],
                            "reason": "acceptance_required", "host": self.host, "at": time.time(),
                            "files": files or {}, "plan_sha256": value["body"].get("plan_sha256"),
                            "restart_handoff": proof.get("restart_handoff") if isinstance(proof, dict) else None,
                            "owner": "external_application_owner", "acknowledgement": "pending_controller_acceptance"}
                write_record(running.parent / "pending-acceptance.json", retained)
                write_record(self.root / "fence.json", retained, replace=True)
            except (OSError, ValueError) as error:
                status, reason, proof, files = "waiting_application", str(error), None, None
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
