import argparse
import json
import os
from pathlib import Path
import signal
import time

import ApplicationProtocol
from ApplicationProtocol import HostQueue, QueueClient, WaitingApplication, configuration, load_pinned, pin, record, write_record


def run_host(config, use_counterpart=False):
    host = HostQueue(config, provider="fixture.transport")
    counterpart = load_pinned(config, ApplicationProtocol.COUNTERPART) if use_counterpart else None
    if counterpart is not None:
        counterpart["protocol"] = vars(ApplicationProtocol)
    stopped = False

    def stop(number, frame):
        nonlocal stopped
        stopped = True

    def action(value, work):
        mode = value["body"]["mode"]
        if mode == "wait":
            write_record(host.root / "entered.json", {"work": str(work)})
            until = time.monotonic() + 30
            while not (host.root / "release.json").exists() and time.monotonic() < until:
                time.sleep(0.02)
        proof = {"claim": "transport_fixture", "native_qualified": False}
        if value["operation"] == "probe":
            return "completed", "fixture challenge", proof, {}
        (work / "fixture.bin").write_bytes(b"real filesystem transport bytes")
        if mode == "handoff":
            proof["restart_handoff"] = host.restart_handoff(value, "f" * 64)
        return "completed", "fixture transport only", proof, {"fixture": pin(work / "fixture.bin", "fixture.bin")}

    signal.signal(signal.SIGTERM, stop)
    write_record(host.root / "ready.json", {"host": host.host}, replace=True)
    try:
        while not stopped and not (host.root / "stop-fixture").exists():
            path = host.next_path()
            if path is None:
                time.sleep(0.02)
                continue
            if counterpart is not None:
                counterpart["serve"](host, path, None)
            else:
                host.perform(path, action)
    finally:
        host.close()


def run_client(config, mode, seconds):
    client = None
    try:
        client = QueueClient(config, time.time() + seconds, provider="fixture.transport")
        if mode == "queued":
            client.call("phase", {"mode": "echo"})
        else:
            client.call("probe", {"mode": "echo"})
            response = client.call("phase", {"mode": mode})
            if mode == "copied":
                work = Path(config["endpoint"]).parent / "Session/work"
                work.mkdir(mode=0o700, parents=True)
                artifacts = client.copy_files(work, response)
                write_record(Path(config["endpoint"]) / "copied.json", {"work": str(work), "spool": str(client.directory), "artifacts": artifacts})
                until = time.monotonic() + 30
                while not (Path(config["endpoint"]) / "release-client.json").exists() and time.monotonic() < until:
                    time.sleep(0.02)
            print(json.dumps(response), flush=True)
    except WaitingApplication as error:
        print(json.dumps({"outcome": "waiting_application", "reason": str(error), "native_qualified": False}), flush=True)
    finally:
        if client is not None:
            client.close()


def main():
    parser = argparse.ArgumentParser(description="Real-process fixture for the local application transport; no CAD claims")
    parser.add_argument("operation", choices=("host", "client", "counterpart"))
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--mode", choices=("echo", "handoff", "wait", "queued", "copied"), default="echo")
    parser.add_argument("--seconds", type=float, default=15)
    args = parser.parse_args()
    config = configuration(args.installation)
    if args.operation in ("host", "counterpart"):
        run_host(config, args.operation == "counterpart")
    else:
        run_client(config, args.mode, args.seconds)


if __name__ == "__main__":
    main()
