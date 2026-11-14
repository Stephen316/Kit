from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def DimGraphMap(
    Author: AuthorState, Edges: tuple[tuple[str, str, int], ...]
) -> list[dict[str, object]]:
    Grouped: dict[str, list[tuple[str, int]]] = {}
    for Source, Target, TypeValue in Edges:
        Grouped.setdefault(Source, []).append((Target, TypeValue))
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
