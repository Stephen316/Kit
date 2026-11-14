from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot

KContainerTypes: tuple[type[object], ...] = (
    AssetHeader,
    ContainerPart,
    DocumentHeader,
    SegmentSlot,
)
