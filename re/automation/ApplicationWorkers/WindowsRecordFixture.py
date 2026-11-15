import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pywintypes
import ntsecuritycon
import win32con
import win32file

from ApplicationProtocol import file_bytes
from WindowsRecords import open_record, shared_identity

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from OutputFiles import open_output


def prepare(root):
    root.mkdir(exist_ok=True)
    source = root / "staged.json"
    source.write_bytes(b'{"version":1,"immutable":true}\n')
    handle = win32file.CreateFile(str(source), win32con.GENERIC_WRITE, 0, None, win32con.OPEN_EXISTING, 0, None)
    try:
        win32file.SetFileTime(handle, pywintypes.Time(946684800), None, None)
    finally:
        handle.Close()
    source.write_bytes(b'{"version":1,"immutable":true,"rewritten":true}\n')
    target = root / "record.json"
    os.replace(source, target)
    os.utime(target, ns=(946684860000000000, 946684860000000000))
    return target


def rewritten(root):
    target = prepare(root)
    with target.open("rb") as source:
        handle_info = os.fstat(source.fileno())
        path_info = target.stat()
    if handle_info.st_ctime_ns == path_info.st_ctime_ns:
        raise AssertionError("fixture did not establish distinct Windows path and handle ctime")
    content = file_bytes(target)
    with open_output(root, target.name) as source:
        if source.read() != content:
            raise AssertionError("durable output reader changed the application record")
    return {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content),
            "path_ctime_ns": path_info.st_ctime_ns, "handle_ctime_ns": handle_info.st_ctime_ns}


def hold(target):
    with open_record(target) as source:
        (target.parent / "ready").write_text(str(os.getpid()), encoding="ascii")
        if sys.stdin.readline().strip() != "release":
            raise ValueError("protected reader did not receive release")
        content = source.read()
    return {"sha256": hashlib.sha256(content).hexdigest()}


def mutations(target):
    outcomes = {}
    actions = {"write": lambda: target.write_bytes(b"changed"),
               "delete": target.unlink,
               "rename": lambda: target.rename(target.with_name("renamed.json")),
               "ancestor": lambda: target.parent.rename(target.parent.with_name("moved"))}
    for name, action in actions.items():
        try:
            action()
        except OSError as error:
            outcomes[name] = error.winerror
        else:
            raise AssertionError(f"protected application record allowed {name}")
    return outcomes


def metadata(target):
    try:
        with open_record(target) as source:
            before = os.fstat(source.fileno())
            handle = win32file.CreateFile(str(target), ntsecuritycon.FILE_WRITE_ATTRIBUTES, win32con.FILE_SHARE_READ, None, win32con.OPEN_EXISTING, 0, None)
            try:
                info = win32file.GetFileInformationByHandleEx(handle, win32file.FileBasicInfo)
                info["ChangeTime"] = pywintypes.Time(978307200)
                win32file.SetFileInformationByHandle(handle, win32file.FileBasicInfo, info)
            finally:
                handle.Close()
            after = os.fstat(source.fileno())
            if shared_identity(before) != shared_identity(after) or before.st_ctime_ns == after.st_ctime_ns:
                raise AssertionError("fixture did not isolate a handle-only ChangeTime mutation")
    except ValueError as error:
        if str(error) != "application input changed while reading":
            raise
        return {"change_time_rejected": True}
    raise AssertionError("handle ChangeTime mutation was accepted")


def refused(target):
    try:
        file_bytes(target)
    except (ValueError, OSError):
        return
    raise AssertionError(f"unsafe application record accepted: {target}")


def unsafe(root):
    target = prepare(root)
    linked = root / "linked.json"
    os.link(target, linked)
    refused(target)
    refused(linked)
    linked.unlink()
    junction = root / "junction"
    result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(root)], capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise AssertionError(f"junction creation failed: {result.stdout} {result.stderr}")
    try:
        refused(junction)
        refused(junction / target.name)
    finally:
        junction.rmdir()
    refused(root)
    try:
        file_bytes(target, 1)
    except ValueError as error:
        if str(error) != "application input exceeds its byte limit":
            raise
    else:
        raise AssertionError("record byte limit was ignored")
    return {"hardlinks": 2, "reparse_paths": 2, "directory": True, "byte_limit": True}


def main():
    operation, path = sys.argv[1:]
    target = Path(path)
    if operation == "rewritten":
        result = rewritten(target)
    elif operation == "prepare":
        result = {"path": str(prepare(target))}
    elif operation == "hold":
        result = hold(target)
    elif operation == "mutations":
        result = mutations(target)
    elif operation == "metadata":
        result = metadata(target)
    elif operation == "unsafe":
        result = unsafe(target)
    else:
        raise ValueError("unknown Windows record fixture operation")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
