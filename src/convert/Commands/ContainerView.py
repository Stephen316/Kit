from convert.Commands.CliOptions import CliOptions
from convert.Commands.FusionView import FusionView
from convert.Commands.SolidworksView import SolidworksView


# container inspection needs consistent format routing without assuming every archive has editable semantics
def ContainerView(Options: CliOptions) -> dict[str, object]:
    FormatId = (Options.SourceFormat or Options.Source.suffix).casefold()
    if FormatId in ("fusion.f3d", "f3d", ".f3d"):
        return FusionView(Options.Source.read_bytes(), Options.StreamName)
    if FormatId in (
        "solidworks.sldprt",
        "solidworks.sldasm",
        "sldprt",
        "sldasm",
        ".sldprt",
        ".sldasm",
    ):
        return SolidworksView(
            Options.Source.read_bytes(),
            Options.StreamName,
            (
                "solidworks.sldasm"
                if FormatId in ("solidworks.sldasm", "sldasm", ".sldasm")
                else "solidworks.sldprt"
            ),
        )
    raise ValueError(
        "Container decoding supports Fusion F3D and SOLIDWORKS SLDPRT/SLDASM; use --from for other filenames"
    )
