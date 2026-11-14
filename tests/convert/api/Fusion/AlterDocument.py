from dataclasses import replace as ReplaceData

from interchange import CadDocument, ParameterValue


def AlterDocument(Document: CadDocument, FieldName: str) -> CadDocument:
    if FieldName == "parameter":
        FirstParam = Document.parameters[0]
        NewValue = ParameterValue(31.0, FirstParam.value.kind, FirstParam.value.unit)
        return ReplaceData(
            Document,
            parameters=(
                ReplaceData(FirstParam, value=NewValue),
                *Document.parameters[1:],
            ),
        )
    if FieldName == "material":
        return ReplaceData(
            Document, materials=(ReplaceData(Document.materials[0], Density=100.0),)
        )
    if FieldName == "body":
        return ReplaceData(
            Document, bodies=(ReplaceData(Document.bodies[0], name="changed"),)
        )
    if FieldName == "history":
        LastStep = ReplaceData(Document.feature_timeline[-1], suppressed=True)
        return ReplaceData(
            Document, feature_timeline=(*Document.feature_timeline[:-1], LastStep)
        )
    if FieldName == "metadata":
        return ReplaceData(
            Document, metadata={**Document.metadata, "unaccounted": True}
        )
    if FieldName == "source":
        return ReplaceData(
            Document, source=ReplaceData(Document.source, path="unaccounted.f3d")
        )
    raise ValueError("Unknown adapter rejection case")
