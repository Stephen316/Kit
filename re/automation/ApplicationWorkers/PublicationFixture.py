import argparse
import json
import os
from pathlib import Path
import signal
import stat
import sys
import time

from ApplicationProtocol import HostQueue, QueueClient, configuration, encoded, record, require, write_new, write_record

PAYLOAD = "transport payload " * 54000


def serve(config):
    host = HostQueue(config, provider="fixture.publication")
    stopped = False

    def stop(number, frame):
        nonlocal stopped
        stopped = True

    def respond(request, directory):
        require(request["body"] == {"payload": PAYLOAD}, "request bytes were incomplete")
        return "completed", "publication process fixture", {"payload": PAYLOAD, "native_qualified": False}, {}

    signal.signal(signal.SIGTERM, stop)
    write_record(host.root / "ready.json", {"host": host.host}, replace=True)
    try:
        while not stopped:
            request = host.next_path()
            if request is None:
                time.sleep(0.001)
            else:
                host.perform(request, respond)
    finally:
        host.close()


def exchange(config):
    client = QueueClient(config, time.time() + 90, provider="fixture.publication")
    try:
        for index in range(32):
            response = client.call("probe", {"payload": PAYLOAD})
            require(response["proof"] == {"payload": PAYLOAD, "native_qualified": False}, "response bytes were incomplete")
            (client.directory / "probe.done").unlink()
        print(json.dumps({"round_trips": index + 1, "payload_bytes": len(PAYLOAD), "native_qualified": False}), flush=True)
    finally:
        client.close()


def publish(root, writer):
    require(sys.stdin.buffer.read(1) == b"x", "publication barrier was not released")
    try:
        write_new(root / "winner.json", encoded({"writer": writer, "payload": PAYLOAD}))
    except FileExistsError:
        outcome = "exists"
    else:
        outcome = "published"
    print(json.dumps({"writer": writer, "outcome": outcome}), flush=True)


def observe(root):
    path = root / "winner.json"
    until = time.monotonic() + 30
    while not path.exists() and time.monotonic() < until:
        time.sleep(0.001)
    value = record(path)
    require(value["payload"] == PAYLOAD, "published record was incomplete")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "published record is not singly linked")
    print(json.dumps({"writer": value["writer"], "links": info.st_nlink, "size_bytes": info.st_size}), flush=True)


def main():
    parser = argparse.ArgumentParser(description="Real-process publication fixture; no CAD runtime")
    parser.add_argument("operation", choices=("host", "exchange", "publish", "observe"))
    parser.add_argument("--installation", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--writer")
    args = parser.parse_args()
    if args.operation == "host":
        serve(configuration(args.installation))
    elif args.operation == "exchange":
        exchange(configuration(args.installation))
    elif args.operation == "publish":
        publish(args.root, args.writer)
    else:
        observe(args.root)


if __name__ == "__main__":
    main()
