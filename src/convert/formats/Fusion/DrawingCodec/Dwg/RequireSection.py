from collections.abc import Mapping


def RequireSection(Named: Mapping[str, bytes], NameText: str) -> bytes:
    DataValue = Named.get(NameText)
    if DataValue is None:
        raise ValueError(f"DWG section {NameText!r} is missing")
    return DataValue
