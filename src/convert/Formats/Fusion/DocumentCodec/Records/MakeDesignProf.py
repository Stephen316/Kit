from convert.Formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.Formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.EntityCodec.Vocabulary.CloseCatalog import CloseCatalog
from convert.Formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.Formats.Fusion.EntityCodec.Vocabulary.SelectClasses import SelectClasses
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# the design prof operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def MakeDesignProf(
    Schemas: tuple[ClassSchema, ...],
    Classes: tuple[MetaClass, ...],
    Targets: tuple[ExternalTarget, ...],
) -> EntityProfile:
    Catalog = DocumentCatalog(Schemas)
    Selected = SelectClasses(Classes, Catalog, True)
    Profile = EntityProfile(
        KNativeRoot,
        CloseCatalog(Selected, Catalog, Targets),
        Targets,
        Catalog.NamedTypes,
    )
    _ = BindProfile(Profile, Classes)
    return Profile
