from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


def LabelGroups(Label: FaceLabel) -> tuple[FaceLabel, ...]:
    return (ReplaceValue(Label, Merged=()), *Label.Merged)


def MergeLabels(First: FaceLabel, Second: FaceLabel) -> FaceLabel:
    Groups = LabelGroups(First) + tuple(
        Value for Value in LabelGroups(Second) if Value not in LabelGroups(First)
    )
    return ReplaceValue(Groups[0], Merged=Groups[1:])


def LabelTags(Label: FaceLabel) -> tuple[FeatureTag, ...]:
    return tuple(
        FeatureTag(Value.PrimaryId, Value.OperationIds, Value.SecondaryId)
        for Value in LabelGroups(Label)
    )
