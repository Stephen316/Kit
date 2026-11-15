from collections.abc import Mapping
from dataclasses import replace as ReplaceData
from hashlib import sha256 as HashContent

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordProvenance import Provenance
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.BuildTypedAsm import BuildTypedAsm

# retained source coverage must include aliases nested containers and empty declarations
KMetadataCases = (
    "Canonical",
    "Alias",
    "Nested",
    "Tuple",
    "List",
    "Set",
    "FrozenSet",
    "EmptyBytes",
    "EmptyText",
    "NullValue",
    "NestedEmpty",
)


# binary retention and harmless provenance must be distinguished on genuinely qualified source models
def BuildMetadata(RecordKind: str, FieldName: str = "Document") -> CadDocument:
    Metadata: Mapping[str, object]
    if RecordKind == "Provenance":
        Metadata = {
            "source_sha256": HashContent(KSamplePath.read_bytes()).hexdigest(),
            "source_path": "original.SLDPRT",
            "source_format": "solidworks.sldprt",
            "notes": {
                "tags": ("research", "provenance"),
                "revision": "source-revision",
            },
        }
    elif RecordKind in ("EmptyBytes", "EmptyText", "NullValue"):
        Metadata = {
            "solidworks_source_bytes": {
                "EmptyBytes": b"",
                "EmptyText": "",
                "NullValue": None,
            }[RecordKind]
        }
    elif RecordKind == "NestedEmpty":
        Metadata = {"analysis": {"solidworks_source_bytes": None}}
    else:
        Content = KSamplePath.read_bytes()
        Cases: dict[str, Mapping[str, object]] = {
            "Canonical": {"solidworks_source_bytes": Content},
            "Alias": {"vendor_archive": Content},
            "Nested": {"analysis": {"source": {"archive": Content}}},
            "Tuple": {"analysis": ("source", {"archive": Content})},
            "List": {"analysis": ["source", {"archive": Content}]},
            "Set": {"analysis": {Content}},
            "FrozenSet": {"analysis": frozenset((Content,))},
        }
        Metadata = Cases[RecordKind]
    Document = (
        BuildTypedAsm()
        if FieldName == "Assembly"
        else MakeFusionDoc(
            DocumentSpec(
                "Typed metadata history",
                "height",
                20.0,
                ProfileKind="cuboid",
                ConstrainRectangle=True,
            )
        )
    )
    if FieldName == "Document":
        return ReplaceData(Document, metadata={**Document.metadata, **Metadata})
    if FieldName in ("Feature", "Provenance"):
        Feature = ReplaceData(
            Document.feature_timeline[-1],
            attributes=(
                Metadata
                if FieldName == "Feature"
                else Document.feature_timeline[-1].attributes
            ),
            provenance=(
                Provenance("fixture", "feature:fixture", attributes=Metadata)
                if FieldName == "Provenance"
                else Document.feature_timeline[-1].provenance
            ),
        )
        return ReplaceData(
            Document, feature_timeline=(*Document.feature_timeline[:-1], Feature)
        )
    if FieldName == "Sketch":
        Sketch = ReplaceData(Document.sketches[0], attributes=Metadata)
        return ReplaceData(Document, sketches=(Sketch, *Document.sketches[1:]))
    if FieldName == "Assembly":
        assert Document.assembly is not None
        return ReplaceData(
            Document, assembly=ReplaceData(Document.assembly, attributes=Metadata)
        )
    if FieldName == "Source":
        return ReplaceData(
            Document, source=ReplaceData(Document.source, attributes=Metadata)
        )
    raise ValueError("Unknown metadata fixture field")
