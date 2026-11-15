from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# shared edit named setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def EditNamed(Records: tuple[EntityRecord, ...]) -> tuple[EntityRecord, ...]:
    Target = next(Record for Record in Records if Record.IsPrimary)
    Metadata = (
        *(Target.Frame.Metadata or ()),
        NamedMetadata("KitTarget", "StrongRefMetaType", LocalRef(Target.ObjectId)),
        NamedMetadata("KitNote", "IntrinsicMetaTypeHString", "typed entity note"),
    )
    Updated = ReplaceValue(Target, Frame=ReplaceValue(Target.Frame, Metadata=Metadata))
    return tuple(Updated if Record is Target else Record for Record in Records)
