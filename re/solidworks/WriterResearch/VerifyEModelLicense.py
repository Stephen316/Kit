# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Compare generated eModel package fields with pinned licensed saves."""

from collections import Counter
from hashlib import sha256
import json

from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import ReadHeaderTail
from PartEModelLicense import EncodeEModelLicense, KEModelLicense
from PartFraming import KPartGeneration
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Archive import ArchiveError, ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


# check that unsupported save contexts fail before producing a stream
def CheckRefusals() -> int:
    Cases = (
        (18000, 4),
        (KPartGeneration, 2),
        (KPartGeneration, 8),
        (KPartGeneration, 4.0),
    )
    for Generation, Code in Cases:
        try:
            EncodeEModelLicense(Generation, Code)
        except ArchiveError:
            continue
        raise AssertionError("unsupported eModel license context was accepted")
    return len(Cases)


# construct from the independently saved header flag before comparing the target member
def report():
    Captures = {}
    Counts = Counter()
    for Recipe, Asset, Data, _, _ in principal_captures():
        Archive = SldprtArchive.from_bytes(Data, Asset["path"])
        Generation = ContainerMo(Archive.streams)
        Cursor, _ = ReadHeaderLogs(Archive.require("Header2"), Generation)
        ReadHeaderSelf(Cursor, Generation)
        Tail = ReadHeaderTail(Cursor, Generation)
        Encoded = EncodeEModelLicense(Generation, Tail.LicenseFlag)
        Original = Archive.require(KEModelLicense)
        require(
            Encoded == Original,
            f"complete eModel package field differs: {Asset['sha256']}",
        )
        Counts[Recipe] += 1
        Captures[Asset["sha256"]] = {
            "package_code": Tail.LicenseFlag,
            "sha256": sha256(Encoded).hexdigest(),
        }
    require(Counts == {"P01": 6, "P03": 8}, "unexpected licensed eModel captures")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Captures,
        "counts": dict(Counts),
        "refused_contexts": CheckRefusals(),
        "replay_sha256": sha256(
            json.dumps(Captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
