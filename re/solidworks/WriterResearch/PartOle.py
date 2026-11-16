"""Generation-19000 part streams for an empty native OLE inventory."""

from collections.abc import Mapping
from dataclasses import dataclass
from struct import Struct

from PartFraming import VersionStorage


OLE_ITEMS = "Contents/OleItems"
OLE_IMAGES = "OleItemInformation/OLE_Item_Data"
OLE_COUNT = Struct("<I")


@dataclass(frozen=True)
class OleInventory:
    EmbeddedCount: int
    ImageMetadataCount: int


# The two save routines select their records independently.
def EncodePartOle(Generation: int, State: OleInventory) -> dict[str, bytes]:
    VersionStorage(Generation)
    if type(State.EmbeddedCount) is not int or type(State.ImageMetadataCount) is not int:
        raise ValueError("OLE inventory counts must be integers")
    if State.EmbeddedCount or State.ImageMetadataCount:
        raise ValueError("part OLE construction requires both inventories to be empty")
    return {
        OLE_ITEMS: OLE_COUNT.pack(State.EmbeddedCount),
        OLE_IMAGES: OLE_COUNT.pack(State.ImageMetadataCount),
    }


# A zero count must account for the entire stream in this profile.
def ReadPartOle(Generation: int, Streams: Mapping[str, bytes]) -> OleInventory:
    VersionStorage(Generation)
    Counts = []
    for Name in (OLE_ITEMS, OLE_IMAGES):
        Payload = Streams.get(Name)
        if Payload is None or len(Payload) != OLE_COUNT.size:
            raise ValueError(f"invalid empty OLE member extent: {Name}")
        (Count,) = OLE_COUNT.unpack(Payload)
        if Count != 0:
            raise ValueError(f"unsupported populated OLE member: {Name}")
        Counts.append(Count)
    return OleInventory(*Counts)
