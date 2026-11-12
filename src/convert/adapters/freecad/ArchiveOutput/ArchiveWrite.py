# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import base64 as BaseSixFour
import hashlib as Hashlib
import io as IoStream
import zipfile as Zipfile
import zlib as ZlibValue
from typing import Mapping, cast as CastValue

from convert.adapters.freecad.Archive import (
    BuildDocCoreMut,
    CanonicalJson,
    IsPayloadMap,
    KDocEntry,
    KManifestEntry,
    KNativeBrepKey,
    KNoTrustedNativeBreps,
    PayloadBrepKeys,
    PayloadMapMap,
    PayloadStrMap,
    Sequence,
    TextAction,
)
from convert.adapters.freecad.EditBodyRev.BodyRevEmit import HasBodyRevMut
from convert.adapters.freecad.EditDatum.DatumEmit import AddDatumsMut
from convert.adapters.freecad.EditScale.ScaleBinding import KScaleBinding
from convert.adapters.freecad.EditScale.ScaleEmit import HasScaleMut


def BuildDocXmlMut(
    Manifest: Mapping[str, object],
    ManifestData: str,
    ManifestShaTwoFiveSix: str,
    OuterLinks: Mapping[str, Mapping[str, object]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str = "1980-01-01T00:00:00Z",
    TrustedNativeBreps: frozenset[KNativeBrepKey] = KNoTrustedNativeBreps,
    EditableFeatures: set[str] | None = None,
) -> tuple[bytes, dict[str, bytes]]:
    return BuildDocCoreMut(
        Manifest,
        ManifestData,
        ManifestShaTwoFiveSix,
        OuterLinks,
        NativeOuterLinks,
        DocTimestamp,
        TrustedNativeBreps,
        EditableFeatures,
        EmitDatums=AddDatumsMut,
        EmitBodyRev=HasBodyRevMut,
        EmitScale=HasScaleMut,
    )


def ZipEntry(NameValue: str, DataValue: bytes) -> tuple[Zipfile.ZipInfo, bytes]:
    InfoValue = Zipfile.ZipInfo(NameValue, (1980, 1, 1, 0, 0, 0))
    setattr(InfoValue, "compress_type", Zipfile.ZIP_DEFLATED)
    setattr(InfoValue, "external_attr", 384 << 16)
    setattr(InfoValue, "create_system", 3)
    return (InfoValue, DataValue)


def BuildFcstdMut(
    Manifest: Mapping[str, object],
    OuterLinks: Mapping[str, Mapping[str, object]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str | None = None,
    TrustedNativeBreps: frozenset[KNativeBrepKey] = KNoTrustedNativeBreps,
    EditableFeatures: set[str] | None = None,
) -> bytes:
    Canonical = CanonicalJson(Manifest)
    Digest = Hashlib.sha256(Canonical).hexdigest()
    Embedded = BaseSixFour.b64encode(ZlibValue.compress(Canonical, 9)).decode("ascii")
    ProducedFeatures: set[str] | None = set() if EditableFeatures is not None else None
    DocXml, PayloadEntries = BuildDocXmlMut(
        Manifest,
        Embedded,
        Digest,
        OuterLinks,
        NativeOuterLinks,
        DocTimestamp or "1980-01-01T00:00:00Z",
        TrustedNativeBreps,
        ProducedFeatures,
    )
    Output = IoStream.BytesIO()
    with Zipfile.ZipFile(Output, "w", allowZip64=True) as Archive:
        Archive.writestr(*ZipEntry(KDocEntry, DocXml))
        MetaValue = Manifest.get("metadata")
        FreecadValue = MetaValue.get("freecad") if IsPayloadMap(MetaValue) else None
        FreecadMeta: Mapping[str, object] = (
            FreecadValue if IsPayloadMap(FreecadValue) else {}
        )
        HasScaleShapes = f'name="{KScaleBinding}"'.encode("ascii") in DocXml
        EntryOrder = (
            () if HasScaleShapes else Sequence(FreecadMeta.get("entry_order", []))
        )
        Written: set[str] = set()
        for Value in EntryOrder:
            Entry = TextAction(Value)
            if Entry in PayloadEntries and Entry not in Written:
                Archive.writestr(*ZipEntry(Entry, PayloadEntries[Entry]))
                Written.add(Entry)
        Archive.writestr(*ZipEntry(KManifestEntry, Canonical + b"\n"))
        Remaining = (
            PayloadEntries.items() if HasScaleShapes else sorted(PayloadEntries.items())
        )
        for Entry, DataValue in Remaining:
            if Entry in Written:
                continue
            Archive.writestr(*ZipEntry(Entry, DataValue))
    if EditableFeatures is not None and ProducedFeatures:
        EditableFeatures.update(ProducedFeatures)
    return Output.getvalue()


def BuildFcstdApi(
    Manifest: Mapping[str, object],
    OuterLinks: Mapping[str, Mapping[str, object]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str | None = None,
    TrustedNativeBreps: frozenset[KNativeBrepKey] = KNoTrustedNativeBreps,
    *,
    EditableFeatures: set[str] | None = None,
    **LegacyValues: object,
) -> bytes:
    LegacyCopy = dict(LegacyValues)
    OuterLinks = PayloadMapMap(LegacyCopy.pop("external_links", OuterLinks))
    NativeOuterLinks = PayloadStrMap(
        LegacyCopy.pop("native_external_links", NativeOuterLinks)
    )
    TimestampValue = LegacyCopy.pop("document_timestamp", DocTimestamp)
    if TimestampValue is not None and not isinstance(TimestampValue, str):
        raise TypeError("document timestamp must be text")
    DocTimestamp = TimestampValue
    TrustedNativeBreps = PayloadBrepKeys(
        LegacyCopy.pop("trusted_native_breps", TrustedNativeBreps)
    )
    EditSink = LegacyCopy.pop("editable_features", EditableFeatures)
    if EditSink is not None and not isinstance(EditSink, set):
        raise TypeError("editable features must be a set")
    if LegacyCopy:
        Unexpected = next(iter(LegacyCopy))
        raise TypeError(
            f"build_fcstd_archive() got an unexpected keyword argument {Unexpected!r}"
        )
    return BuildFcstdMut(
        Manifest,
        OuterLinks,
        NativeOuterLinks,
        DocTimestamp,
        TrustedNativeBreps,
        CastValue(set[str] | None, EditSink),
    )


build_fcstd_archive = BuildFcstdApi
