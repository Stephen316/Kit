import os


class LogCapture:
    def __init__(self, path, limit):
        self.limit = limit
        self.seen = 0
        self.retained = 0
        self.reader = None
        self.writer = None
        self.output = None
        self.closed = False
        try:
            self.output = os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb")
            self.reader, self.writer = os.pipe()
            os.set_blocking(self.reader, False)
        except BaseException:
            self.close()
            raise

    def close_writer(self):
        if self.writer is not None:
            os.close(self.writer)
            self.writer = None

    def drain(self):
        remaining = 256 * 1024
        while self.reader is not None and remaining > 0:
            try:
                content = os.read(self.reader, min(65536, remaining))
            except BlockingIOError:
                break
            if not content:
                os.close(self.reader)
                self.reader = None
                break
            remaining -= len(content)
            self.seen += len(content)
            retained = content[:max(0, self.limit - self.retained)]
            if retained:
                self.output.write(retained)
                self.retained += len(retained)
        if self.output is not None:
            self.output.flush()

    def close(self):
        if self.closed:
            return
        self.close_writer()
        try:
            self.drain()
        finally:
            if self.reader is not None:
                os.close(self.reader)
                self.reader = None
            if self.output is not None:
                self.output.close()
                self.output = None
            self.closed = True

    def receipt(self):
        return {"limit_bytes": self.limit, "seen_bytes": self.seen, "retained_bytes": self.retained, "dropped_bytes": self.seen - self.retained}
