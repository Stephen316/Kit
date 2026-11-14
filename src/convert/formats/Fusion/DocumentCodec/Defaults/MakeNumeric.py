def MakeNumeric(
    NameValue: str, LengthMm: float, Comment: str, Birthday: int
) -> dict[str, object]:
    return dict(
        UserDefaultUnit=False,
        actIdentifier="",
        birthday=Birthday,
        booleanValue=False,
        comment=Comment,
        creationIndex=1,
        dcParameter=None,
        expression=str(LengthMm) + " mm",
        expressionType=0,
        group=None,
        isDirty=False,
        isDriven=False,
        isExternal=False,
        isFavourite=False,
        isOrphan=False,
        isUserDefined=True,
        name="User Parameter",
        textValue="",
        unit="mm",
        userName=NameValue,
        value=LengthMm / 10.0,
    )
