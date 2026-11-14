from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Vocabulary.CloseCatalog import CloseCatalog
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog
from convert.formats.Fusion.EntityCodec.Vocabulary.SelectClasses import SelectClasses
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


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
