from convert.adapters.Fusion.Native.Circular.RadialSpecs import KRadialSpecs
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.Native.Policy.DesignClasses import KDesignClasses
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof


# invalid classes input must fail here so public document claims remain grounded in native records
def CheckClasses(
    Graph: NativeGraph,
    Dimension: NativeNode | None = None,
    Rectangle: RectSketchProof | None = None,
) -> None:
    Schemas = {Schema.Value.ClassGuid.upper(): Schema.Value for Schema in ReadNames()}
    RectNodes = (*Rectangle.Rules, *Rectangle.Dimensions) if Rectangle else ()
    for NodeValue in Graph.Nodes.values():
        IsRadial = NodeValue.ClassName in KRadialSpecs
        if NodeValue in RectNodes and NodeValue.SegmentId != 0:
            raise ValueError(
                "Constrained rectangle semantic entity uses another segment"
            )
        if (IsRadial and (NodeValue is not Dimension or NodeValue.SegmentId != 0)) or (
            not IsRadial
            and NodeValue.SegmentId == 0
            and NodeValue.ClassName not in KDesignClasses
            and NodeValue not in RectNodes
        ):
            raise ValueError("Unmodeled native Fusion semantic entity class")
        for Group in NodeValue.Groups:
            if NodeValue.SegmentId == 0 and Group.Opaque:
                if Dimension is not None:
                    raise ValueError(
                        "Native radial design contains opaque semantic members"
                    )
                if Rectangle is not None:
                    raise ValueError(
                        "Native rectangle design contains opaque semantic members"
                    )
            Schema = Schemas.get(Group.ClassGuid.upper())
            if Schema is None:
                if NodeValue.ClassName != "VisualAnalysesBrowserEntry" or Group.Fields:
                    raise ValueError("Unknown native Fusion semantic member group")
                continue
            Members = {Field.FieldName for Field in Schema.Members if Field.IsSaved}
            if not {Field.FieldName for Field in Group.Fields} <= Members:
                raise ValueError("Unknown native Fusion semantic member")
