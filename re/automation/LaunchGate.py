import os
import selectors
import signal
import sys


def main():
    descriptor = int(sys.argv[1])
    try:
        with selectors.DefaultSelector() as waiting:
            waiting.register(descriptor, selectors.EVENT_READ)
            if not waiting.select(30):
                return 124
            released = os.read(descriptor, 1)
    finally:
        os.close(descriptor)
    if released != b"x":
        return 125
    for name in ("SIGPIPE", "SIGXFZ", "SIGXFSZ"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), signal.SIG_DFL)
    os.execvpe(sys.argv[2], sys.argv[2:], os.environ)


if __name__ == "__main__":
    sys.exit(main())
