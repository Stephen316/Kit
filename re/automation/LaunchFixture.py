import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from Processes import KILL_SIGNAL, process_start, signal_group, start_process
from Sessions import Session, write_private
from Supervisor import Supervisor, read_config


def launch(root):
    process, release = start_process([sys.executable, str(Path(__file__).resolve()), "worker", "--root", str(root)], root, dict(os.environ), subprocess.DEVNULL, subprocess.DEVNULL)
    try:
        write_private(root / "bootstrap.json", {"pid": process.pid, "identity": process_start(process.pid)})
        sys.stdin.buffer.read(1)
    finally:
        if release is not None:
            os.close(release)
        signal_group(process.pid, KILL_SIGNAL)
        process.wait(timeout=10)
        write_private(root / "reaped.json", {"returncode": process.returncode})


def worker(root):
    write_private(root / "worker-entered.json", {"pid": os.getpid()})
    child = subprocess.Popen([sys.executable, "-I", "-S", "-c", "import time; time.sleep(60)"], start_new_session=False)
    write_private(root / "executed.json", {"pid": os.getpid(), "child": child.pid})
    while True:
        time.sleep(1)


def supervised(root):
    write_private(root / "worker-entered.json", {"pid": os.getpid()})
    session = Path(os.environ["KIT_SESSION"])
    metadata = json.loads((session / "session.json").read_text())
    assert metadata["pid"] == os.getpid()
    assert metadata["process_start"] == process_start(os.getpid())
    child = subprocess.Popen([sys.executable, "-I", "-S", "-c", "import time; time.sleep(60)"], start_new_session=False)
    write_private(root / "executed.json", {"pid": os.getpid(), "child": child.pid, "metadata": metadata})
    job = json.loads((session / "job.json").read_text())
    write_private(session / "result.json", {"outcome": "completed", "reason": "gated worker saw its durable process metadata", "records": {"count": len(job["inputs"]), "inputs": sorted(job["inputs"]), "tokenless": "lease_token" not in job}})


def metadata_failure(root):
    supervisor = Supervisor(read_config(root / "Supervisor.json"), True)
    supervisor.acquire()
    supervisor.synchronize()
    claim_path = supervisor.claims / "launch-failure.json"
    claim = supervisor.adapter.ClaimJob("decode", "launch:failure", claim_path)
    session = Session(supervisor, "decode", claim, claim_path, "launch-failure")
    session.prepare()
    (session.directory / "session.json").mkdir()
    try:
        session.start()
    except OSError:
        assert session.process is not None and session.process.poll() is not None
        assert not (root / "worker-entered.json").exists()
        print(json.dumps({"bootstrap_stopped": True, "pid": session.process.pid}), flush=True)
    else:
        raise AssertionError("invalid metadata destination did not reject startup")


def pipe_signal(root):
    reader, writer = os.pipe()
    os.close(reader)
    process, release = start_process(["/usr/bin/yes"], root, dict(os.environ), writer, subprocess.DEVNULL)
    os.close(writer)
    try:
        write_private(root / "session.json", {"pid": process.pid, "identity": process_start(process.pid)})
        os.write(release, b"x")
        assert process.wait(timeout=10) == -signal.SIGPIPE
        print(json.dumps({"signal": signal.SIGPIPE}), flush=True)
    finally:
        os.close(release)
        signal_group(process.pid, KILL_SIGNAL)
        process.wait(timeout=10)


class UnattributedWindow:
    def __init__(self, session, pid, start):
        self.session = session
        self.pid = pid
        self.start = start

    def finish(self, receipt):
        assert receipt["session"] == self.session
        assert receipt["pid"] == self.pid and receipt["process_start"] == self.start
        assert process_start(self.pid) != self.start
        assert receipt["signal"] == signal.SIGKILL and receipt["stop_reason"] is None
        print(json.dumps({"event": "kernel_observer_reaped", "session": self.session}), flush=True)
        return None

    def close(self):
        print(json.dumps({"event": "kernel_observer_closed", "session": self.session}), flush=True)


class UnattributedObserver:
    def __init__(self, state):
        self.state = state

    def arm(self, session, pid, start):
        assert process_start(pid) == start
        assert not (self.state / "sessions" / session / "session.json").exists()
        print(json.dumps({"event": "kernel_observer_armed", "session": session}), flush=True)
        return UnattributedWindow(session, pid, start)


def observe_signal(root):
    config = read_config(root / "Supervisor.json")
    supervisor = Supervisor(config, True, linux_oom_observer=UnattributedObserver(config["state"]))
    print(json.dumps(supervisor.run(1, 20)), flush=True)


def main():
    parser = argparse.ArgumentParser(description="Real-process fixture for the POSIX worker launch gate")
    parser.add_argument("operation", choices=("launch", "worker", "supervised", "metadata-failure", "pipe-signal", "observe-signal", "ordinary-sigkill"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if args.operation == "launch":
        launch(args.root)
    elif args.operation == "worker":
        worker(args.root)
    elif args.operation == "supervised":
        supervised(args.root)
    elif args.operation == "metadata-failure":
        metadata_failure(args.root)
    elif args.operation == "observe-signal":
        observe_signal(args.root)
    elif args.operation == "ordinary-sigkill":
        os.kill(os.getpid(), signal.SIGKILL)
    else:
        pipe_signal(args.root)


if __name__ == "__main__":
    main()
