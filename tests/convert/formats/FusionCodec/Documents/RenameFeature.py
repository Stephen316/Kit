from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# shared rename feature setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RenameFeature(Value: DocumentModel, Label: str) -> DocumentModel:
    Segments = tuple(
        ReplaceValue(
            Segment,
            Records=tuple(
                ReplaceValue(
                    Record,
                    Groups=tuple(
                        ReplaceValue(
                            Group,
                            Fields=tuple(
                                (
                                    ReplaceValue(FieldValue, Value=Label)
                                    if FieldValue.FieldName == "featureUserName"
                                    else FieldValue
                                )
                                for FieldValue in Group.Fields
                            ),
                        )
                        for Group in Record.Groups
                    ),
                )
                for Record in Segment.Records
            ),
        )
        for Segment in Value.Segments
    )
    return ReplaceValue(Value, Segments=Segments)
