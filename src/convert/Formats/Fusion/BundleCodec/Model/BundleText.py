from dataclasses import dataclass as MakeDataClass


# bundle text needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class BundleText:
    FieldName: str
    TextValue: str
