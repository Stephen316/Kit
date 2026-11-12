from collections.abc import Mapping
from operator import itemgetter as GetItems

from convert.formats.Fusion.Assembly.ScopeLinks import GetScopeLinks
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter

# scoped documents retain only records needed to explain their own bodies
KScopeRecord = FeatureStep | Sketch | SupportPlane | Selection | Parameter

# indexing once keeps repeated component documents independent of total history size
KScopeIndex = dict[tuple[str, str], tuple[int, KScopeRecord]]


# stable source positions preserve the ordering of detached records
def IndexScope(Document: CadDocument) -> KScopeIndex:
    Groups: tuple[tuple[str, tuple[KScopeRecord, ...]], ...] = (
        ("step", Document.feature_timeline),
        ("sketch", Document.sketches),
        ("plane", Document.support_planes),
        ("selection", Document.selections),
        ("parameter", Document.parameters),
    )
    return {
        (RecordKind, Value.id): (Order, Value)
        for RecordKind, Records in Groups
        for Order, Value in enumerate(Records)
    }


# traverse only explicit native timeline and neutral record dependencies
def GetScopeRecords(
    Bodies: tuple[DesignBody, ...],
    Index: KScopeIndex,
    Sketches: Mapping[str, Sketch],
) -> tuple[KScopeRecord, ...]:
    Pending = [("step", BodyValue.final_feature_id) for BodyValue in Bodies]
    Selected: dict[tuple[str, str], tuple[int, KScopeRecord]] = {}
    while Pending:
        RecordKey = Pending.pop()
        if RecordKey in Selected:
            continue
        Entry = Index.get(RecordKey)
        if Entry is None:
            raise ValueError(
                f"Fusion component has a missing {RecordKey[0]} dependency {RecordKey[1]}"
            )
        Selected[RecordKey] = Entry
        Pending.extend(GetScopeLinks(Entry[1], Sketches))
    Ordered = sorted(
        (
            (RecordKind, Order, Record)
            for (RecordKind, _), (Order, Record) in Selected.items()
        ),
        key=GetItems(0, 1),
    )
    return tuple(Record for _, _, Record in Ordered)
