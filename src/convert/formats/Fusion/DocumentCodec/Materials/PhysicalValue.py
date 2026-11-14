from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def PhysicalValue(Author: AuthorState) -> list[dict[str, object]]:
    if Author.Materials is None:
        raise ValueError("Body material identity is absent")
    Identity = Author.Materials.Identity
    return [
        Author.MakeGroup(
            "PhysicalMaterialValue",
            {
                "ProteinAssetManager": Author.Reference("protein"),
                "assetReference": Identity.PhysicalId,
                "libraryID": Identity.LibraryId,
                "name": "",
                "proteinMaterialID": Identity.PhysicalDef,
            },
        )
    ]
