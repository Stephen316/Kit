from collections.abc import Mapping


# invalid section input must fail here so section boundaries and object references remain consistent
def RequireSection(Named: Mapping[str, bytes], NameText: str) -> bytes:
    DataValue = Named.get(NameText)
    if DataValue is None:
        raise ValueError(f"DWG section {NameText!r} is missing")
    return DataValue
