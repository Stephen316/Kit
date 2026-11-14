from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def AddUnitsMut(Author: AuthorState) -> None:
    Choices: list[tuple[str | int, str]] = [
        ("ModelingLength", "millimeter"),
        ("ModelingMass", "gram"),
    ]
    Choices += [
        (Number, UnitName)
        for (Number, UnitName) in [
            (0, "meter"),
            (1, "kilogram"),
            (2, "second"),
            (3, "celsius"),
            (4, "ampere"),
            (5, "Mole"),
            (6, "candela"),
            (7, "degree"),
            (8, "dollar"),
            (10, "MetersPerSecond"),
            (12, "liter"),
            (13, "pascal"),
            (14, "newton"),
            (15, "watt"),
            (16, "joule"),
            (31, "percent"),
            (33, "pieces"),
        ]
    ]
    for KeyName, UnitName in Choices:
        FieldValues: dict[str, object] = {
            "name": Author.Localize(UnitName),
            "unitString": UnitName,
        }
        FieldValues["id" if isinstance(KeyName, str) else "eSimpleUnitType"] = KeyName
        Author.Allocate(
            "unit_" + str(KeyName),
            (
                "UnitSystemChoiceById"
                if isinstance(KeyName, str)
                else "UnitSystemChoiceByUnit"
            ),
            ParentRole="unit_system",
            Fields=FieldValues,
        )
    Author.Change("unit_system", id="MmMKS", name=Author.Localize("Millimeter MKS"))
