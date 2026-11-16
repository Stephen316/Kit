from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


# the label groups contract needs a shared interpretation so body topology remains consistent with its modeling operation
def LabelGroups(Label: FaceLabel) -> tuple[FaceLabel, ...]:
    return (ReplaceValue(Label, Merged=()), *Label.Merged)


# the merge labels contract needs a stable decomposition so body topology remains consistent with its modeling operation
def MergeLabels(First: FaceLabel, Second: FaceLabel) -> FaceLabel:
    Groups = LabelGroups(First) + tuple(
        Value for Value in LabelGroups(Second) if Value not in LabelGroups(First)
    )
    return ReplaceValue(Groups[0], Merged=Groups[1:])


# the label tags contract needs a shared interpretation so body topology remains consistent with its modeling operation
def LabelTags(Label: FaceLabel) -> tuple[FeatureTag, ...]:
    return tuple(
        FeatureTag(Value.PrimaryId, Value.OperationIds, Value.SecondaryId)
        for Value in LabelGroups(Label)
    )
