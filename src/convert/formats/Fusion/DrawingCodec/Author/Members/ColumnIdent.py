from base64 import b64encode as EncodeBase
from base64 import urlsafe_b64encode as EncodeSafe

from convert.formats.Fusion.DrawingCodec.Author.Model.PartColumn import PartColumn

KPropertySpace = "BasePropertiesProd"

KPropertyGroup = "BasePropertiesGroupProd"

KPropertySuffix = "-1.0.0"


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


def PlainBase(TextValue: str) -> str:
    return EncodeBase(TextValue.encode("utf-8")).decode("ascii").rstrip("=")
