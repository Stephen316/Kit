from convert.adapters.solidworks.container.Archive import ArchiveError


# both sketch readers must interpret saved column axes in the same order
def MatrixAxes(
    RowsValue: tuple[float, ...],
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    if len(RowsValue) != 9:
        raise ArchiveError("SOLIDWORKS basis requires nine matrix scalars")
    return (
        (RowsValue[0], RowsValue[3], RowsValue[6]),
        (RowsValue[1], RowsValue[4], RowsValue[7]),
        (RowsValue[2], RowsValue[5], RowsValue[8]),
    )
