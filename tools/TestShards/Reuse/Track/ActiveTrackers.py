from __future__ import annotations

from tools.TestShards.Reuse.Track.TrackState import TrackState

# the active trackers vocabulary must stay centralized so test reuse agrees on supported native identities
KActiveTrackers: dict[str, TrackState] = {}
