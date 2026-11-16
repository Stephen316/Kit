# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Compare generated live exchange records with the receipt-pinned database."""

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from struct import unpack_from
from uuid import UUID

from OrdinaryResolved import ReadResolvedSystem
from PartObjectExchange import (
    EncodeObjectExchangeDb,
    ExchangeRecords,
    KIndexKey,
    KObjectDb,
    ObjectExchange,
)
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved


# the on-disk chain names the active records even if older freed records remain
def LiveRecords(Data: bytes) -> tuple[tuple[bytes, bytes], ...]:
    require(len(Data) == 12288, "three exchange database pages")
    (Mapped,) = unpack_from(">Q", Data, 4096 + 52)
    require(Mapped == 2, "ordinary exchange bucket page mapping")
    Base = Mapped * 4096
    Offset, _, Slave = unpack_from(">HHQ", Data, Base)
    require(Slave == 0, "ordinary exchange has no secondary bucket")
    Seen = set()
    Entries = []
    while Offset:
        require(
            12 <= Offset <= 4096 - 26 and Offset not in Seen, "exchange cell boundary"
        )
        Seen.add(Offset)
        _, KeyLen, DataLen, Prior, Overflow = unpack_from(">IIQHQ", Data, Base + Offset)
        Start = Base + Offset + 26
        KeyEnd, End = Start + KeyLen, Start + KeyLen + DataLen
        require(
            Overflow == 0 and KeyLen in (3, 36) and End <= len(Data),
            "ordinary exchange cell payload",
        )
        Entries.append((Offset, Data[Start:KeyEnd], Data[KeyEnd:End]))
        Offset = Prior
    return tuple((Key, Value) for _, Key, Value in sorted(Entries))


# only the exchange identifiers and wall time come from the database under comparison
def ReadExchangeKeys(
    Data: bytes, Records: tuple[tuple[bytes, bytes], ...]
) -> ObjectExchange:
    require(
        len(Records) == 6 and Records[4][0] == KIndexKey, "ordinary exchange inventory"
    )
    KeyList = tuple(UUID(Key.decode("ascii")) for Key, _ in Records if Key != KIndexKey)
    Folder, Front, Top, Right, Document = KeyList
    (Clock,) = unpack_from(">I", Data, 11)
    Created = datetime(
        1980 + (Clock >> 25),
        (Clock >> 21) & 15,
        (Clock >> 16) & 31,
        (Clock >> 11) & 31,
        (Clock >> 5) & 63,
        (Clock & 31) * 2,
    )
    Toc = Records[4][1]
    Planes = (Front, Top, Right)
    Names = tuple(str(Plane).encode("ascii") for Plane in Planes)
    require(
        all(Toc.count(Name) == 1 for Name in Names), "distinct TOC datum references"
    )
    Order = tuple(sorted(range(3), key=lambda Slot: Toc.index(Names[Slot])))
    return ObjectExchange(Folder, Planes, Document, Created, Order)


# the independent solved feature archive supplies the datum and folder states
def ReadSystem(Archive: SldprtArchive, Generation: int):
    Configuration, Model = ReadOrdinaryMap(
        Archive.require("Contents/Config-0"), Generation
    )
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Cursor = OpenResolved(Resolved, Configuration, 18 + Model["atom_count"])
    return ReadResolvedSystem(Cursor, Generation)


# compare live bytes and prove the fresh database leaves cleared free space
def Report():
    Cases = {}
    Counts = Counter()
    ReplayRecords = 0
    IndexOrders = set()
    for Recipe, Asset, Raw, _, _ in principal_captures():
        Archive = SldprtArchive.from_bytes(Raw, Asset["path"])
        Generation = ContainerMo(Archive.streams)
        Source = Archive.require(KObjectDb)
        Expected = LiveRecords(Source)
        Keys = ReadExchangeKeys(Source, Expected)
        System = ReadSystem(Archive, Generation)
        Built = ExchangeRecords(Generation, Keys, System)
        require(
            Built == Expected,
            f"typed exchange records differ for {Asset['sha256']}: "
            f"{[(len(Actual), len(Saved)) for (_, Actual), (_, Saved) in zip(Built, Expected)]}",
        )
        Fresh = EncodeObjectExchangeDb(Generation, Keys, System)
        require(LiveRecords(Fresh) == Expected, "fresh exchange live record linkage")
        (Free,) = unpack_from(">H", Fresh, 8194)
        require(
            unpack_from(">HH", Fresh, 8192 + Free) == (0, 4096 - Free)
            and not any(Fresh[8192 + Free + 4 :]),
            "fresh bucket must have one empty free-space tail",
        )
        Counts[Recipe] += 1
        ReplayRecords += len(Built)
        IndexOrders.add(Keys.IndexOrder)
        Cases[Asset["sha256"]] = {
            "native": sha256(Source).hexdigest(),
            "fresh": sha256(Fresh).hexdigest(),
            "live": sha256(b"".join(Key + Value for Key, Value in Built)).hexdigest(),
        }
    require(Counts == {"P01": 6, "P03": 8}, "object exchange discovery scope")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "live_records": ReplayRecords,
        "index_orders": len(IndexOrders),
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(Report(), sort_keys=True))
