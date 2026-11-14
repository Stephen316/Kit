from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.formats.Fusion.DocumentCodec.Tapered.TaperParameter import TaperParameter


def BindParamsMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Along = MakeNumeric(
        "d2", Author.SpecValue.LengthMm, "", Author.Policy.ParamBirthday
    )
    Along.update(
        creationIndex=2,
        dcParameter=Reference("along_binding"),
        expression=Author.SpecValue.ParamName,
        isUserDefined=False,
        name="AlongDistance",
    )
    Taper = TaperParameter(Author)
    Author.Change("along_parameter", **Along)
    Author.Change("taper_parameter", **Taper)
    for RoleName, ParamRole, RuntimeId, Value in [
        ("along_binding", "along_parameter", 1, Along["value"]),
        ("taper_binding", "taper_parameter", 2, Taper["value"]),
    ]:
        Author.Change(
            RoleName,
            value=Value,
            parameter=Reference(ParamRole),
            rparamId=RuntimeId,
            rrOwnerFeature=Reference("dc_extrude"),
            rParentFeature=Reference("dc_extrude"),
            rDynamicUpdateData=Reference(RoleName + "_dynamic"),
        )
        Author.Change(
            RoleName + "_dynamic",
            rOwnerNode=Reference(RoleName),
            timeStamp=Author.Policy.TimeStamp,
        )
    Author.Change("parameters", highWaterMark=3)
    Author.Change(
        "parameter_names",
        parameterMap=[
            {"key": Author.SpecValue.ParamName, "value": Reference("length_parameter")},
            {"key": "d2", "value": Reference("along_parameter")},
            {"key": "d3", "value": Reference("taper_parameter")},
        ],
    )
    Author.FindEntity("parameter_names").Subjects.extend(
        ["along_parameter", "taper_parameter"]
    )
