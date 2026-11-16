# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the ordinary standalone configuration exchange database."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from PartFeatureIndex import KConfiguration
from PartFraming import VersionStorage
from UnqlitePage import WriteSingleBucket

KConfigDb = "Contents/3DExperienceExchange_ConfigHeader"

# exact semantic fields retained by the observed ordinary configuration record
KConfigFields = (
    ("_3dExpType", 0),
    ("class", "dmConfigHeader_c"),
    ("configHeaderfamilyMemberID", -2),
    ("id", 0),
    ("name", KConfiguration),
    ("repParent", ""),
)


# a new configuration owns its record identity and database creation clock
@dataclass(frozen=True, slots=True)
class ConfigExchange:
    RecordId: UUID
    Created: datetime


# the ordinary messagepack record uses only compact strings and fixints
def EncodeConfigScalar(Value: str | int) -> bytes:
    if isinstance(Value, str):
        Encoded = Value.encode("utf-8")
        if len(Encoded) < 32:
            return bytes((0xA0 | len(Encoded),)) + Encoded
    elif type(Value) is int and -32 <= Value <= 127:
        return bytes((Value & 0xFF,))
    raise ValueError("configuration exchange scalar exceeds the observed compact type")


# a standalone default configuration has one typed record under its own UUID
def EncodeConfigHeaderDb(Generation: int, RecordId: UUID, Created: datetime) -> bytes:
    VersionStorage(Generation)
    if RecordId.version != 4:
        raise ValueError(
            "configuration exchange requires a caller-issued version-four UUID"
        )
    Value = bytes((0x80 | len(KConfigFields),)) + b"".join(
        EncodeConfigScalar(Name) + EncodeConfigScalar(Scalar)
        for Name, Scalar in KConfigFields
    )
    return WriteSingleBucket(Created, ((str(RecordId).encode("ascii"), Value),))
