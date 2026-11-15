from __future__ import annotations

# the track errors order must stay explicit so dependency changes cannot revive stale passing results
KTrackErrors = (
    AttributeError,
    ImportError,
    KeyError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
)
