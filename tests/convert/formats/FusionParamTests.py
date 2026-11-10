# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from math import pi as PiValue
from struct import pack as PackData
from zipfile import ZipFile

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NumericParam import KParamGuid
from convert.formats.Fusion.ZipParameters import ReadZipParams
from interchange.enums.EnumValues import ParameterRole, ValueKind


# the fixture builds length prefixed native strings from their semantic values
def NativeText(ValueText: str, WideText: bool = True) -> bytes:
    return PackData("<I", len(ValueText)) + ValueText.encode(
        "utf-16le" if WideText else "ascii"
    )


# reciprocal binding fixtures vary cached values while preserving record identities
def BindingFixture(CachedValue: float) -> bytes:
    BodyValue = bytearray(85)
    BodyValue[:6] = b"\1\1\0\0\0\1"
    BodyValue[6:14] = PackData("<Q", 200)
    BodyValue[21:29] = PackData("<d", CachedValue)
    BodyValue[29:38] = b"\1" + PackData("<Q", 42)
    BodyValue[-11:-2] = b"\1" + PackData("<Q", 200)
    return PackData("<I3sQ", 3, b"257", 90) + bytes(4) + BodyValue


# independent index positions tie parameters and bindings to distinct owner records
def ParamIndex(BindStart: int, OwnerStart: int) -> bytes:
    KindField = NativeText("FusionDesignSegmentType", False)
    Classes = b"".join(
        NativeText(GuidValue, False) + PackData("<IIIIQ", 0, 0, 0, 1, Identity)
        for GuidValue, Identity in (
            (KParamGuid, 42),
            ("D91D429C-1BB5-4640-B49F-69AF14F463E9", 90),
            ("SyntheticOwner", 200),
        )
    )
    return b"".join(
        (
            KindField,
            PackData("<IIIIII", 0, 0, 1234, 8, 0, 0),
            KindField,
            PackData("<IIII", 0, 1, 0, 3),
            Classes,
            PackData(
                "<IIQQQQQQIQII",
                0,
                3,
                42,
                0,
                90,
                BindStart,
                200,
                OwnerStart,
                0,
                201,
                0,
                0,
            ),
        )
    )


# an indexed numeric parameter exercises the archive path and source ownership
def ParamFixture(Metadata: bytes, CachedValue: float = PiValue / 4) -> bytes:
    BulkValue = b"".join(
        (
            PackData("<I3sQ", 3, b"256", 42),
            bytes(4),
            bytes(7),
            b"\x06",
            bytes(4),
            NativeText("angle"),
            PackData("<I", 1),
            b"\1",
            PackData("<Q", 90),
            bytes(2),
            NativeText("45 deg"),
            Metadata,
            NativeText("AlongAngle"),
            NativeText(""),
            NativeText("deg"),
            NativeText("d1"),
            PackData("<d", PiValue / 4),
            b"\0\1\x10",
            bytes(9),
        )
    )
    Binding = BindingFixture(CachedValue)
    MetaValue = ParamIndex(len(BulkValue), len(BulkValue) + len(Binding))
    BulkValue += Binding + PackData("<I3sQ", 3, b"258", 200)
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
        assert Result.attributes["fusion.owner_object_id"] == 200
        assert Result.attributes["fusion.expression_metadata"] == "00" * Width
        assert Result.provenance is not None and Result.provenance.native_id == "42"
        assert len(Result.provenance.spans) == 2


# unknown native layouts should remain visible to a future adapter as diagnostics
def TestParamReject() -> None:
    Params, (Issue,) = ReadZipParams(ParamFixture(bytes(10) + b"\1"))
    assert not Params
    assert Issue.code == "fusion.parameter.unsupported"
    assert Issue.provenance is not None and Issue.provenance.native_id == "42"


# a conflicting cache keeps the source numeric value without assigning an owner
def TestBadBinding() -> None:
    (Result,), (Issue,) = ReadZipParams(ParamFixture(bytes(10), CachedValue=0.0))
    assert Result.value.value == PiValue / 4
    assert "fusion.owner_object_id" not in Result.attributes
    assert Issue.code == "fusion.parameter.binding"
    assert Issue.message == "Fusion numeric binding value disagrees"
