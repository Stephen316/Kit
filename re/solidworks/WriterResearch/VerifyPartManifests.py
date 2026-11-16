# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Compare generated manifests with the independently authored discovery archives."""

from collections import Counter
from hashlib import sha256
import json

from PartManifests import KProperties, EncodeManifests
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Container import SldprtArchive


# pin complete member equality and independently check that missing targets are refused
def report():
    Captures = {}
    Counts = Counter()
    for Recipe, Asset, Data, _, _ in principal_captures():
        Streams = SldprtArchive.from_bytes(Data, Asset["path"]).streams
        Generated = EncodeManifests(Streams)
        for Name, Encoded in Generated.items():
            require(Encoded == Streams[Name], f"typed package manifest differs: {Name}")
        Captures[Asset["sha256"]] = {
            Name: sha256(Contents).hexdigest()
            for Name, Contents in sorted(Generated.items())
        }
        Counts[Recipe] += 1
        for Target, _, _, _ in KProperties:
            try:
                EncodeManifests(Streams.keys() - {Target})
            except ValueError as Error:
                require(
                    Target in str(Error),
                    "absent relationship target produced a different failure",
                )
            else:
                raise ValueError(
                    f"an absent package relationship target was admitted: {Target}"
                )
    require(Counts == {"P01": 6, "P03": 8}, "unexpected manifest capture roster")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Captures,
        "counts": dict(Counts),
        "missing_target_refusals": len(KProperties) * sum(Counts.values()),
        "replay_sha256": sha256(
            json.dumps(Captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
