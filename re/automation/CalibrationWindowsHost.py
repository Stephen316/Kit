import os
import sys

from Sessions import write_private
from Supervisor import main as supervise
from WindowsProcess import process_start


def main():
    pid = os.getpid()
    started = process_start(pid)
    if started is None:
        raise OSError("Windows supervisor interpreter identity is unavailable")
    write_private(
        sys.argv[1], {"pid": pid, "parent_pid": os.getppid(), "process_start": started}
    )
    sys.argv = sys.argv[2:]
    return supervise()


if __name__ == "__main__":
    sys.exit(main())
