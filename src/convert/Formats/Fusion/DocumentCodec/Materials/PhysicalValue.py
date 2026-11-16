from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


# physical value needs an explicit validity boundary so appearance references remain connected to their owning entities
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
