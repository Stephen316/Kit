# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from math import pi as PiValue
from struct import pack as Pack
from zipfile import ZipFile

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NumericParam import KParamGuid
from convert.formats.Fusion.ZipParameters import ReadZipParams
from interchange.enums.EnumValues import ParameterRole, ValueKind


# the fixture builds length prefixed native strings from their semantic values
def NativeText(ValueText: str, WideText: bool = True) -> bytes:
    return Pack("<I", len(ValueText)) + ValueText.encode(
        "utf-16le" if WideText else "ascii"
    )


# one indexed numeric parameter exercises the public archive path and projection
def ParamFixture(Metadata: bytes) -> bytes:
    KindField = NativeText("FusionDesignSegmentType", False)
    MetaValue = b"".join(
        (
            KindField,
            Pack("<IIIIII", 0, 0, 1234, 8, 0, 0),
            KindField,
            Pack("<IIII", 0, 1, 0, 1),
            NativeText(KParamGuid, False),
            Pack("<IIIIQ", 0, 0, 0, 1, 42),
            Pack("<IIQQIQII", 0, 1, 42, 0, 0, 43, 0, 0),
        )
    )
    BulkValue = b"".join(
        (
            Pack("<I3sQ", 3, b"256", 42),
            bytes(4),
            bytes(7),
            b"\x06",
            bytes(4),
            NativeText("angle"),
            Pack("<I", 1),
            b"\1",
            Pack("<Q", 90),
            bytes(2),
            NativeText("45 deg"),
            Metadata,
            NativeText("AlongAngle"),
            NativeText(""),
            NativeText("deg"),
            NativeText("d1"),
            Pack("<d", PiValue / 4),
            b"\0\1\x10",
            bytes(9),
        )
    )
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        Archive.writestr(KDesignPrefix + "BulkStream.dat", BulkValue)
        Archive.writestr(KDesignPrefix + "MetaStream.dat", MetaValue)
    return Buffer.getvalue()


# equivalent legacy and extended encodings must carry the same dimensional value
def TestParamLayout() -> None:
    for Width in (10, 11):
        Params, Diagnostics = ReadZipParams(ParamFixture(bytes(Width)))
        assert not Diagnostics
        (Result,) = Params
        assert Result.name == "d1"
        assert Result.value.value == PiValue / 4
        assert Result.value.kind == ValueKind.KAngle
        assert Result.value.unit == "rad"
        assert Result.role == ParameterRole.KReference
        assert Result.expression is not None and Result.expression.source == "45 deg"
        assert Result.attributes["fusion.binding_id"] == 90
        assert Result.attributes["fusion.expression_metadata"] == "00" * Width
        assert Result.provenance is not None and Result.provenance.native_id == "42"


# unknown native layouts should remain visible to a future adapter as diagnostics
def TestParamReject() -> None:
    Params, (Issue,) = ReadZipParams(ParamFixture(bytes(10) + b"\1"))
    assert not Params
    assert Issue.code == "fusion.parameter.unsupported"
    assert Issue.provenance is not None and Issue.provenance.native_id == "42"
