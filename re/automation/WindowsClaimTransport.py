import os
import queue
import subprocess
import sys
import threading
import time
from contextlib import ExitStack
from pathlib import Path

from ClaimWire import CLAIM_NAME, ClaimExchangeLost, read_frame, send_frame
from RecoveryFence import StaleOwner
from WindowsProcess import WindowsProcess

SERVER = Path(__file__).with_name("ClaimProcess.py")


class WindowsClaimTransport:
    def __init__(self, store, claims):
        self.claims = claims
        self.sequence = 0
        self.thread = None
        self.closed = False
        with ExitStack() as child, ExitStack() as parent:
            read_request, write_request = os.pipe()
            child.callback(os.close, read_request)
            self.writer = parent.enter_context(os.fdopen(write_request, "wb"))
            read_response, write_response = os.pipe()
            child.callback(os.close, write_response)
            self.reader = parent.enter_context(os.fdopen(read_response, "rb"))
            errors = child.enter_context(open(os.devnull, "wb"))
            self.process = WindowsProcess(
                [sys.executable, str(SERVER), str(store), str(claims)],
                Path.cwd(),
                dict(os.environ),
                write_response,
                errors.fileno(),
                stdin=read_request,
            )
            self.streams = parent.pop_all()

    def transfer(self, request, result):
        try:
            send_frame(self.writer, request)
            reply = read_frame(self.reader)
            result.put((True, reply))
        except (OSError, ValueError):
            result.put((False, None))

    def claim(self, owner, worker, pool, path, deadline):
        if (
            self.closed
            or self.thread is not None
            or path.parent != self.claims
            or not CLAIM_NAME.fullmatch(path.name)
        ):
            raise ValueError("invalid private Windows claim helper state")
        self.sequence += 1
        request = {
            "sequence": self.sequence,
            "owner": owner,
            "worker": worker,
            "pool": pool,
            "name": path.name,
        }
        result = queue.Queue(maxsize=1)
        self.thread = threading.Thread(
            target=self.transfer, args=(request, result), daemon=True
        )
        try:
            self.thread.start()
            ok, response = result.get(timeout=max(0, deadline - time.monotonic()))
            self.thread.join(max(0, deadline - time.monotonic()))
            if self.thread.is_alive():
                raise ClaimExchangeLost(
                    "Windows claim helper did not finish the timed exchange"
                )
            self.thread = None
            if (
                not ok
                or response is None
                or type(response.get("sequence")) is not int
                or response["sequence"] != self.sequence
            ):
                raise ClaimExchangeLost("Windows claim helper response was lost")
            if response == {"sequence": self.sequence, "error": "stale_owner"}:
                raise StaleOwner("a03 rejected the replaced supervisor owner")
            value = response.get("result")
            if (
                set(response) != {"sequence", "result"}
                or not isinstance(value, dict)
                or "job" not in value
            ):
                raise ClaimExchangeLost(
                    "Windows claim helper did not confirm a committed outcome"
                )
            return value
        except queue.Empty as error:
            self.close(terminate=True)
            raise ClaimExchangeLost(
                "Windows claim helper exceeded the controller deadline"
            ) from error
        except BaseException:
            self.close(terminate=True)
            raise

    def close(self, *, terminate=False):
        if self.closed:
            return
        self.closed = True
        try:
            if not terminate:
                self.writer.close()
                try:
                    self.process.wait(5)
                except subprocess.TimeoutExpired:
                    terminate = True
            if terminate:
                self.process.signal(9)
                self.process.wait(5)
            self.process.finish()
        finally:
            self.process.close()
            if self.thread is not None and self.thread.ident is not None:
                self.thread.join(5)
            if self.thread is not None and self.thread.is_alive():
                raise OSError("Windows claim helper pipe did not close")
            self.streams.close()
