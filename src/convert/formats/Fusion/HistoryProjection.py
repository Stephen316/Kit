from convert.formats.Fusion.FeatureLabels import ReadFeatLabel
from convert.formats.Fusion.FeatureState import ReadFeatState
from convert.formats.Fusion.HistoryGroup import KGroupGuid
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.NativeHistory import ReadHistory
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep


# a qualified history can project neutral ordering without inventing feature definitions
def ProjectHistory(
    BulkData: bytes,
    History: RecordSpan,
    Owners: dict[int, RecordSpan],
    ParamIds: dict[int, list[str]],
) -> HistoryPart:
    OwnerId, Entries, Groups = ReadHistory(BulkData, History, Owners)
    Steps: list[FeatureStep] = []
    GroupIds = {
        Identity: Group.ObjectId for Group in Groups for Identity in Group.MemberIds
    }
    for Entry in Entries:
        SpanValue = Owners[Entry]
        if SpanValue.ClassGuid == KGroupGuid:
            continue
        BodyValue = BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset]
        LabelText, FeatureType = ReadFeatLabel(BodyValue, SpanValue.ClassGuid)
        State = ReadFeatState(BodyValue)
        Steps.append(
            FeatureStep(
                id=f"fusion-feature-{History.ObjectId}-{Entry}",
                name=LabelText,
                kind=FeatureType,
                order=len(Steps),
                parameter_ids=tuple(ParamIds.get(Entry, ())),
                suppressed=State[0] if State is not None else False,
                provenance=ParamOrigin(SpanValue),
                attributes=FreezeMapping(
                    {
                        "fusion.state_known": State is not None,
                        "fusion.rolled_back": State[1] if State is not None else None,
                        "fusion.history_group_id": GroupIds.get(Entry),
                    }
                ),
            )
        )
    return HistoryPart(History.ObjectId, OwnerId, Entries, Groups, tuple(Steps))
