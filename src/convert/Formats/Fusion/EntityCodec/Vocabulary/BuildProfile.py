from convert.Formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.EntityCodec.Vocabulary.CloseCatalog import CloseCatalog
from convert.Formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog
from convert.Formats.Fusion.EntityCodec.Vocabulary.SelectClasses import SelectClasses
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# the profile operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def BuildProfile(
    Classes: tuple[MetaClass, ...], Targets: tuple[ExternalTarget, ...] = ()
) -> EntityProfile:
    Catalog = ReadCatalog()
    Selected = SelectClasses(Classes, Catalog)
    Profile = EntityProfile(
        KNativeRoot,
        CloseCatalog(Selected, Catalog, Targets),
        Targets,
        Catalog.NamedTypes,
    )
    _ = BindProfile(Profile, Classes)
    return Profile
