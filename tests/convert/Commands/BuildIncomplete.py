from dataclasses import replace as ReplaceData

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.BuildTypedAsm import BuildTypedAsm


# assembly qualification needs valid graphs with explicitly unresolved or missing component evidence
def BuildIncomplete(RecordKind: str, OwnerName: str = "") -> CadDocument:
    Document = BuildTypedAsm()
    assert Document.assembly is not None
    Assembly = Document.assembly
    if RecordKind in (
        "MissingReference",
        "ExternalReference",
        "NativeComponent",
        "ResolvedReference",
        "ProvenanceOnly",
        "UnrepresentedPart",
        "SourceUnresolved",
        "SourceDeferred",
    ):
        Definition = Assembly.definitions[-1]
        if RecordKind in ("MissingReference", "ExternalReference", "UnrepresentedPart"):
            Definition = ReplaceData(
                Definition,
                kind=(
                    ComponentKind.KReference
                    if RecordKind == "MissingReference"
                    else ComponentKind.KPart
                ),
                document_id="",
                body_ids=(),
                source_path="" if RecordKind == "UnrepresentedPart" else "missing.part",
                attributes=(
                    {"source_resolved": False}
                    if RecordKind == "ExternalReference"
                    else Definition.attributes
                ),
            )
        elif RecordKind == "NativeComponent":
            Definition = ReplaceData(Definition, kind=ComponentKind.KNative)
        elif RecordKind == "SourceUnresolved":
            Definition = ReplaceData(Definition, attributes={"source_resolved": False})
        elif RecordKind == "SourceDeferred":
            Definition = ReplaceData(
                Definition, attributes={"source_resolution": "deferred"}
            )
        elif RecordKind == "ProvenanceOnly":
            Definition = ReplaceData(Definition, source_path="original.part")
        else:
            Definition = ReplaceData(Definition, kind=ComponentKind.KReference)
        Assembly = ReplaceData(
            Assembly, definitions=(*Assembly.definitions[:-1], Definition)
        )
    elif RecordKind == "EmptyAssembly":
        Assembly = ReplaceData(
            Assembly,
            definitions=(Assembly.definitions[0],),
            instances=(),
            documents=(),
            mate_entities=(),
            mates=(),
        )
    elif RecordKind == "TransformUnresolved":
        Instance = ReplaceData(
            Assembly.instances[0], attributes={"transform_resolved": False}
        )
        Assembly = ReplaceData(Assembly, instances=(Instance, *Assembly.instances[1:]))
    else:
        FieldName = (
            "transform_status"
            if RecordKind == "NativeTransforms"
            else "constraint_status"
        )
        Assembly = ReplaceData(
            Assembly,
            attributes={
                FieldName: (
                    "native-only" if RecordKind == "NativeTransforms" else "unresolved"
                )
            },
        )
    if OwnerName:
        Assembly = ReplaceData(
            Assembly,
            definitions=tuple(
                (
                    ReplaceData(Definition, source_path="original.assembly")
                    if Definition.id == "definition:" + OwnerName
                    else Definition
                )
                for Definition in Assembly.definitions
            ),
        )
    return ReplaceData(Document, assembly=Assembly)
