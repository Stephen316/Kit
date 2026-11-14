from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.convert.formats.FusionCodec.Documents.Dimensions.DimensionFields import (
    DimensionFields,
    DimensionRows,
)


def CheckDimGraph(Model: DocumentModel) -> None:
    Sketch = DimensionRows(Model, "DcSketch")[0]
    SketchRef = LocalRef(Sketch.ObjectId)
    Bindings = DimensionFields(Sketch)["dcParameters"]
    assert isinstance(Bindings, ValueSeries)
    assert len(Bindings.Items) == 2
    Compute = DimensionFields(DimensionRows(Model, "DcComputeManager")[0])
    Nodes = Compute["sortedNodesAll"]
    assert isinstance(Nodes, ValueSeries)
    assert Compute["sortIsCurrent"] is True
    assert all(
        Nodes.Items.index(Binding) < Nodes.Items.index(SketchRef)
        for Binding in Bindings.Items
    )
    Dependency = DimensionFields(DimensionRows(Model, "DcDependencyManager")[0])
    assert Dependency["mapsAreCurrent"] is True
    Predecessors = Dependency["predecessorMap"]
    Successors = Dependency["successorMap"]
    assert isinstance(Predecessors, ValueMap)
    assert isinstance(Successors, ValueMap)
    Incoming = next(
        Entry.Second for Entry in Predecessors.Entries if Entry.First == SketchRef
    )
    assert isinstance(Incoming, ValueMap)
    for Binding in Bindings.Items:
        assert ValuePair(Binding, 1) in Incoming.Entries
        Outgoing = next(
            Entry.Second for Entry in Successors.Entries if Entry.First == Binding
        )
        assert Outgoing == ValueMap((ValuePair(SketchRef, 1),))
