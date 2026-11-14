from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.Native.Policy.DesignClasses import KDesignClasses


def CheckClasses(Graph: NativeGraph) -> None:
    Schemas = {Schema.Value.ClassGuid.upper(): Schema.Value for Schema in ReadNames()}
    for NodeValue in Graph.Nodes.values():
        if NodeValue.SegmentId == 0 and NodeValue.ClassName not in KDesignClasses:
            raise ValueError("Unmodeled native Fusion semantic entity class")
        for Group in NodeValue.Groups:
            Schema = Schemas.get(Group.ClassGuid.upper())
            if Schema is None:
                if NodeValue.ClassName != "VisualAnalysesBrowserEntry" or Group.Fields:
                    raise ValueError("Unknown native Fusion semantic member group")
                continue
            Members = {Field.FieldName for Field in Schema.Members if Field.IsSaved}
            if not {Field.FieldName for Field in Group.Fields} <= Members:
                raise ValueError("Unknown native Fusion semantic member")
