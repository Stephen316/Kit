from base64 import b64encode as EncodeBytes
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from hashlib import sha256 as DigestBytes
from zlib import compress as CompressBytes

from convert.adapters.base.SafeParsing import ParseUntrusted
from convert.adapters.freecad.Archive import CanonicalJson, KMaxDocSize, ValidateXml
from convert.adapters.freecad.ArchiveOutput.ArchiveWrite import BuildDocXmlMut
from convert.adapters.freecad.EditRead.XmlField import EditAttr, EditChild, EditFloat
from convert.adapters.freecad.ExtrusionCache.InlineProfile import ReadCacheFrame
from convert.adapters.freecad.LiteralQuantity import KLiteralPattern
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceParam import KLengthFactors
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Payloads.PayloadRoles import PayloadRole


# specialized native and retained geometry paths keep their existing reconciliation contracts
def ReadInlineScope(
    Document: CadDocument, Manifest: Mapping[str, object]
) -> FeatureStep | None:
    Features = tuple(
        Value
        for Value in Document.feature_timeline
        if not Value.suppressed and Value.kind != "reference"
    )
    if (
        Document.assembly is not None
        or Document.brep is not None
        or Document.metadata.get("freecad")
        or any(
            Value.role not in (PayloadRole.KAuxiliary, PayloadRole.KVerification)
            for Value in Document.brep_payloads
        )
        or len(Features) != 1
        or len(Document.bodies) != 1
    ):
        return None
    Feature = Features[0]
    if (
        Feature.kind != "extrusion"
        or Feature.operation not in (None, "create")
        or not isinstance(Feature.definition, ExtrudeFeature)
        or Document.bodies[0].final_feature_id != Feature.id
        or ReadCacheFrame(Manifest, Feature.id) is None
    ):
        return None
    Document.assert_valid()
    return Feature


# expected controls come from the exact pure emitter rather than a second interpretation of end ownership
def ReadExpected(Manifest: Mapping[str, object]) -> tuple[NativeObject, ...]:
    Canonical = CanonicalJson(Manifest)
    Encoded = EncodeBytes(CompressBytes(Canonical, 9)).decode("ascii")
    XmlData, _ = BuildDocXmlMut(Manifest, Encoded, DigestBytes(Canonical).hexdigest())
    if len(XmlData) > KMaxDocSize:
        raise ValueError("inline expected document exceeds the archive limit")
    RootValue = ParseUntrusted(XmlData)
    _ = ValidateXml(RootValue)
    return ParseObjects(RootValue)


# finite native distance properties are compared before any stale snapshot can be returned
def ReadInlineDepth(ObjectValue: NativeObject, FieldName: str) -> float:
    return EditFloat(
        EditChild(ObjectValue, FieldName, "App::PropertyDistance", "Float"), "value"
    )


# an inline extrusion can own only the two native end expression paths
def ReadInlineExpr(ObjectValue: NativeObject) -> dict[str, str]:
    Engine = EditChild(
        ObjectValue,
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
    )
    Entries = Engine.findall("Expression")
    if (
        Engine.get("count") != str(len(Entries))
        or len(Entries) != len(Engine)
        or len(Entries) > 2
    ):
        raise ValueError("inline end expression count changed")
    Result: dict[str, str] = {}
    for RowValue in Entries:
        PathValue, SourceText = EditAttr(RowValue, "path"), EditAttr(
            RowValue, "expression"
        )
        if (
            PathValue not in ("LengthFwd", "LengthRev")
            or PathValue in Result
            or len(SourceText) > 512
        ):
            raise ValueError("inline end expression owner changed")
        Result[PathValue] = SourceText
    return Result


# harmless literal spelling changes preserve exact physical millimetres without tolerating edited values
def IsInlineCell(Before: str, After: str, Millimetres: float | None) -> bool:
    if Before == After:
        return True
    if Millimetres is None or len(After) > 128:
        return False
    Matched = KLiteralPattern.fullmatch(After.removeprefix("=").strip())
    if Matched is None:
        return False
    NumberText, UnitName = Matched.groups()
    Factor = KLengthFactors.get(UnitName)
    if Factor is None:
        return False
    try:
        return Decimal(NumberText) * Decimal(str(Factor)) == Decimal(str(Millimetres))
    except InvalidOperation:
        return False
