from convert.adapters.solidworks.container.Archive import ArchiveError


# typed readers need a consistent failure when a native branch falls outside their layout
def RequireArch(Value: object, Expected: object, FieldName: str) -> None:
    if Value != Expected:
        raise ArchiveError(f"{FieldName}: got {Value!r}, expected {Expected!r}")
