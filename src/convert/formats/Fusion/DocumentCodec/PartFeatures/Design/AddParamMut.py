from convert.formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadSeries,
)

KCountClass = "DcIntParameter"
KCountModes: dict[str, object] = dict(isRoundToNearestInt=True)


def ExprText(Amount: float) -> str:
    TextValue = repr(float(Amount))
    return TextValue[:-2] if TextValue.endswith(".0") else TextValue


def AddParamMut(
    Author: AuthorState,
    RoleName: str,
    OwnerRole: str,
    NameValue: str,
    Amount: float,
    UnitName: str,
    Expression: str | None = None,
    ClassName: str = "DcDoubleParameter",
) -> None:
    Watermark = ReadInteger(
        Author.FindEntity("parameters").FieldValues["highWaterMark"]
    )
    RuntimeId = ReadInteger(Author.FindEntity("fragment").FieldValues["nextParamId"])
    UserName = "d" + str(Watermark + 1)
    Fields = MakeNumeric(UserName, Amount, "", Author.Policy.ParamBirthday)
    Value = Amount / 10.0 if UnitName == "mm" else Amount
    AddNodeMut(Author, RoleName, ClassName, OwnerRole, False)
    Fields.update(
        creationIndex=Watermark + 1,
        dcParameter=Author.Reference(RoleName),
        expression=(
            ExprText(Amount) + (" " + UnitName if UnitName else "")
            if Expression is None
            else Expression
        ),
        isUserDefined=False,
        name=NameValue,
        unit=UnitName,
        value=Value,
    )
    Author.Allocate(
        RoleName + "_parameter", "Parameter", ParentRole="parameters", Fields=Fields
    )
    Author.FindEntity(RoleName).Subjects.append(OwnerRole)
    Numbers: dict[str, object] = dict(value=Value)
    if ClassName == KCountClass:
        Numbers = dict(KCountModes, value=round(Value))
    Author.Change(
        RoleName,
        **Numbers,
        parameter=Author.Reference(RoleName + "_parameter"),
        rparamId=RuntimeId + 1,
        rrOwnerFeature=Author.Reference(OwnerRole),
    )
    Author.Change("parameters", highWaterMark=Watermark + 1)
    Author.Change("fragment", nextParamId=RuntimeId + 1)
    Names = list(
        ReadSeries(Author.FindEntity("parameter_names").FieldValues["parameterMap"])
    )
    Names.append({"key": UserName, "value": Author.Reference(RoleName + "_parameter")})
    Author.Change("parameter_names", parameterMap=Names)
    Author.FindEntity("parameter_names").Subjects.append(RoleName + "_parameter")
