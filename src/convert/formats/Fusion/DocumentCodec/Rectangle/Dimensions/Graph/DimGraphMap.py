from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


# the dim graph map contract needs a shared interpretation so model state retains its native feature and ownership relationships
def DimGraphMap(
    Author: AuthorState, Edges: tuple[tuple[str, str, int], ...]
) -> list[dict[str, object]]:
    Grouped: dict[str, list[tuple[str, int]]] = {}
    for Source, Target, TypeValue in Edges:
        Grouped.setdefault(Source, []).append((Target, TypeValue))

    # ordering by author roles role name must stay deterministic so document reconstruction resolves equivalent inputs consistently
    return [
        {
            "key": Author.Reference(Source),
            "value": [
                {"key": Author.Reference(Target), "value": TypeValue}
                for Target, TypeValue in sorted(
                    Grouped[Source], key=lambda Entry: Author.Roles[Entry[0]]
                )
            ],
        }
        for Source in sorted(Grouped, key=lambda RoleName: Author.Roles[RoleName])
    ]
