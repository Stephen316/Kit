import os
import select
import subprocess
import time


# the short admission snapshot starts only after the native provider is ready to submit
def guarded_launch(arguments, timeout, admit):
    deadline = time.monotonic() + timeout
    with subprocess.Popen(
        arguments,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    ) as process:
        try:
            if wait_marker(process, b"R", deadline):
                with admit():
                    if process.stdin.write(b"x") != 1:
                        raise OSError("archive launch gate did not receive admission")
                    wait_marker(process, b"D", deadline)
            process.stdin.close()
            process.stdin = None
            output, errors = process.communicate(timeout=remaining(process, deadline))
        except BaseException:
            if process.poll() is None:
                process.kill()
            raise
    return subprocess.CompletedProcess(arguments, process.returncode, output, errors)


# a missing provider marker fails within the original launch budget
def remaining(process, deadline):
    budget = deadline - time.monotonic()
    if budget <= 0:
        raise subprocess.TimeoutExpired(process.args, 0)
    return budget


# eof preserves the original native refusal and arbitrary output cannot authorize launch
def wait_marker(process, expected, deadline):
    descriptor = process.stdout.fileno()
    if not select.select([descriptor], [], [], remaining(process, deadline))[0]:
        raise subprocess.TimeoutExpired(process.args, 0)
    seen = os.read(descriptor, 1)
    if seen and seen != expected:
        raise ValueError("unexpected archive launch provider handshake")
    return seen == expected
