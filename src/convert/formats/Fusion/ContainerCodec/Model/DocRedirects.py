from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.RedirectDesign import RedirectDesign
from convert.formats.Fusion.ContainerCodec.Model.RedirectRef import RedirectRef


@MakeDataClass(frozen=True, slots=True)
class DocRedirects:
    Designs: tuple[RedirectDesign, ...]
    References: tuple[RedirectRef, ...]
