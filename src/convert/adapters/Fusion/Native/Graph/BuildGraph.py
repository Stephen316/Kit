from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.DocumentCodec.Records.NativeAuxiliary import (
    KAuxiliarySchemas,
)


def BuildGraph(Value: DocumentModel) -> NativeGraph:
    Catalog = {Entry.Value.ClassGuid.upper(): Entry for Entry in ReadNames()}
    Auxiliary = {Entry.ClassGuid.upper() for Entry in KAuxiliarySchemas}
    Nodes: dict[tuple[int, int], NativeNode] = {}
    for Segment in Value.Segments:
        SegmentId = Segment.Metadata.Header.SegmentId
        for Record in Segment.Records:
            if not Record.IsPrimary:
                continue
            Groups = tuple(
                Group
                for ItemValue in Segment.Records
                if ItemValue.ObjectId == Record.ObjectId
                for Group in ItemValue.Groups
            )
            Schema = Catalog.get(Groups[0].ClassGuid.upper())
            if Schema is None:
                if Groups[0].ClassGuid.upper() not in Auxiliary or SegmentId == 0:
                    raise ValueError("Unknown native Fusion entity class")
            ClassName = (
                Schema.NameValue if Schema is not None else "VisualAnalysesBrowserEntry"
            )
            Nodes[(SegmentId, Record.ObjectId)] = NativeNode(
                SegmentId, Record.ObjectId, ClassName, Groups, Record.Frame
            )
    Bases = {
        Schema.NameValue: ClassBases(Schema, Catalog) for Schema in Catalog.values()
    }
    Bases["VisualAnalysesBrowserEntry"] = ("EntityEntry",)
    return NativeGraph(Nodes, Bases)


def ClassBases(
    Value: NativeSchema, Catalog: dict[str, NativeSchema]
) -> tuple[str, ...]:
    Result: list[str] = []
    NextGuid = Value.Value.BaseGuid.upper()
    while NextGuid:
        Schema = Catalog.get(NextGuid)
        if Schema is None:
            break
        if Schema.NameValue in Result:
            raise ValueError("Cyclic native Fusion class inheritance")
        Result.append(Schema.NameValue)
        NextGuid = Schema.Value.BaseGuid.upper()
    return tuple(Result)
