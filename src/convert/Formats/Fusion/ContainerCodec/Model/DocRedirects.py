from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.ContainerCodec.Model.RedirectDesign import RedirectDesign
from convert.Formats.Fusion.ContainerCodec.Model.RedirectRef import RedirectRef


# doc redirects needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DocRedirects:
    Designs: tuple[RedirectDesign, ...]
    References: tuple[RedirectRef, ...]
