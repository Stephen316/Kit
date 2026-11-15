from tests.convert.solidworks.core.InchIndex.OwnerFrame import OwnerFrame
from tests.convert.solidworks.core.InchIndex.ScalarFrame import ScalarFrame


def InchRoster(Count: int) -> tuple[bytes, bytes]:
    Dimensions = "".join(
        f'<Dimension Name="Span{Index}">{(Index + 1) * 0.001 / 0.0254:.2f}</Dimension>'
        for Index in range(Count)
    )
    Keywords = (
        f'<Root><Feature id="20" Name="Owned" Type="Datum">{Dimensions}</Feature>'
    )
    Resolved = OwnerFrame("Owned", 20) + b"".join(
        ScalarFrame(f"Span{Index}", (Index + 1) * 0.001, 1000 + Index, 0)
        for Index in range(Count)
    )
    for Index in range(4):
        Keywords += f'<Feature id="{30 + Index}" Name="Parent{Index}" Type="Datum" DissectableChildren="20">{Dimensions}</Feature>'
        Resolved += OwnerFrame(f"Parent{Index}", 30 + Index)
    return (Keywords + "</Root>").encode("utf-8"), Resolved
