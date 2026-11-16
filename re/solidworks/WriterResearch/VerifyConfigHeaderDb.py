# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Replay the ordinary configuration exchange independently of authored contents."""

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from struct import unpack_from
from uuid import UUID, uuid4

from PartConfigHeaderDb import EncodeConfigHeaderDb, KConfigDb
from PartFraming import KPartGeneration
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Container import SldprtArchive


# only the source clock and uuid are needed to reconstruct every byte
def ReadHeaderIdentity(Data: bytes) -> tuple[UUID, datetime]:
    require(len(Data) == 12288, "three configuration database pages")
    (Clock,) = unpack_from(">I", Data, 11)
    Created = datetime(
        1980 + (Clock >> 25),
        (Clock >> 21) & 15,
        (Clock >> 16) & 31,
        (Clock >> 11) & 31,
        (Clock >> 5) & 63,
        (Clock & 31) * 2,
    )
    (Cell,) = unpack_from(">H", Data, 8192)
    require(Cell == 12, "configuration record starts after its bucket header")
    _, Size, _, Link, Overflow = unpack_from(">IIQHQ", Data, 8192 + Cell)
    require((Size, Link, Overflow) == (36, 0, 0), "one local configuration record")
    Start = 8192 + Cell + 26
    Key = Data[Start : Start + Size].decode("ascii")
    Identity = UUID(Key)
    require(str(Identity) == Key, "configuration UUID text differs")
    return Identity, Created


# reconstruct all source pages and exercise refusal before emitting unsupported headers
def Report():
    Cases = {}
    Counts = Counter()
    for Recipe, Asset, Raw, _, _ in principal_captures():
        Archive = SldprtArchive.from_bytes(Raw, Asset["path"])
        Source = Archive.require(KConfigDb)
        RecordId, Created = ReadHeaderIdentity(Source)
        Output = EncodeConfigHeaderDb(KPartGeneration, RecordId, Created)
        require(Output == Source, "complete configuration exchange database differs")
        Counts[Recipe] += 1
        Cases[Asset["sha256"]] = sha256(Output).hexdigest()
    require(Counts == {"P01": 6, "P03": 8}, "configuration exchange discovery scope")
    require(
        len(set(Cases.values())) == 14,
        "the case roster needs fourteen distinct databases",
    )
    FreshKey = uuid4()
    FreshTime = datetime(2026, 1, 2, 3, 4, 6)
    Fresh = EncodeConfigHeaderDb(KPartGeneration, FreshKey, FreshTime)
    require(
        ReadHeaderIdentity(Fresh) == (FreshKey, FreshTime), "fresh database identity"
    )
    Refusals = 0
    for BadKey, BadTime in (
        (UUID(int=0), FreshTime),
        (FreshKey, datetime(1979, 1, 1)),
    ):
        try:
            EncodeConfigHeaderDb(KPartGeneration, BadKey, BadTime)
        except ValueError:
            Refusals += 1
        else:
            raise AssertionError("unmodeled configuration state emitted a database")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "refusals": Refusals,
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(Report(), sort_keys=True))
