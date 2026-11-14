from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def VisualValue(Author: AuthorState) -> list[dict[str, object]]:
    if Author.Materials is None:
        raise ValueError("Body appearance identity is absent")
    Identity = Author.Materials.Identity
    Color = Author.SpecValue.Material.Color
    return [
        Author.MakeGroup(
            "VisualMaterialValue",
            {
                "CustomizedColor": {
                    "red": Color.RedValue,
                    "green": Color.GreenValue,
                    "blue": Color.BlueValue,
                    "alpha": Color.AlphaValue,
                },
                "ProteinAssetManager": Author.Reference("protein"),
                "UseCustomizedColor": False,
                "assetReference": Identity.AppearanceId,
                "libraryID": Identity.LibraryId,
                "name": "",
                "proteinMaterialID": Identity.AppearanceDef,
                "proteinMaterialRotation": 0.0,
                "proteinMaterialScale": 1.0,
            },
        )
    ]
