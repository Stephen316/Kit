from base64 import b64encode as EncodeBase
from base64 import urlsafe_b64encode as EncodeSafe

from convert.Formats.Fusion.DrawingCodec.Author.Model.PartColumn import PartColumn

# property space must remain consistent across callers so sheet objects retain their intended document relationships
KPropertySpace = "BasePropertiesProd"

# property group must remain consistent across callers so sheet objects retain their intended document relationships
KPropertyGroup = "BasePropertiesGroupProd"

# property suffix must remain consistent across callers so sheet objects retain their intended document relationships
KPropertySuffix = "-1.0.0"


# the column ident contract needs a shared interpretation so sheet objects retain their intended document relationships
def ColumnIdent(Column: PartColumn) -> str:
    if not Column.Group:
        return Column.Ident
    Space = PlainBase(KPropertySpace)
    TextValue = "~".join(
        (
            "propdef",
            Space,
            PlainBase(KPropertyGroup),
            PlainBase(Column.Group),
            "parameters." + Space + ":" + Column.Ident + KPropertySuffix,
        )
    )
    return EncodeSafe(TextValue.encode("utf-8")).decode("ascii").rstrip("=")


# the plain base contract needs a shared interpretation so sheet objects retain their intended document relationships
def PlainBase(TextValue: str) -> str:
    return EncodeBase(TextValue.encode("utf-8")).decode("ascii").rstrip("=")
