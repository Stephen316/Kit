import select
import sys
import time
from contextlib import contextmanager

from ApplicationProtocol import require
from MacApplicationPeer import process_peer


class PeerUnavailable(ValueError):
    pass


def verify_peer(peer, executable):
    try:
        observed = process_peer(peer["pid"])
    except (OSError, ValueError) as error:
        raise PeerUnavailable(
            "exact macOS application peer unavailable before exit observation"
        ) from error
    require(
        observed == {**peer, "executable": executable},
        "macOS application peer differs from its pinned exit identity",
    )


@contextmanager
def watch_peer(peer, executable):
    require(sys.platform == "darwin", "Fusion exit observation requires macOS")
    verify_peer(peer, executable)
    monitor = select.kqueue()
    try:
        event = select.kevent(
            peer["pid"],
            filter=select.KQ_FILTER_PROC,
            flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
            fflags=select.KQ_NOTE_EXIT | select.KQ_NOTE_EXEC,
        )
        try:
            monitor.control([event], 0, 0)
        except ProcessLookupError as error:
            raise PeerUnavailable(
                "exact macOS application peer disappeared during exit registration"
            ) from error
        verify_peer(peer, executable)
        yield monitor
    finally:
        monitor.close()


def observe_exit(monitor, peer, seconds):
    events = monitor.control(None, 1, seconds)
    if not events:
        return None
    (event,) = events
    require(
        event.ident == peer["pid"]
        and event.filter == select.KQ_FILTER_PROC
        and not event.flags & select.KQ_EV_ERROR
        and not event.fflags & select.KQ_NOTE_EXEC
        and event.fflags & select.KQ_NOTE_EXIT,
        "macOS application exit observation was replaced by another process event",
    )
    return {"observation": "darwin_process_exit_event", "observed_at": time.time()}
