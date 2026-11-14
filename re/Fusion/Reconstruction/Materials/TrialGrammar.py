"""Research-only grammar trial for schema kinds that the production reader lacks.

Each trial form is accepted only when every record in the sweep decodes to its
exact end, because records are positional and a wrong width breaks the rest.
"""

from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package import SchemaModels as SchemaModule
from convert.formats.Fusion.MaterialCodec.Package.Schema import SchemaGrammar
from convert.formats.Fusion.MaterialCodec.Schema import BuildSchemas as BuildModule
from convert.formats.Fusion.MaterialCodec.Values import DecodeScalar as ScalarModule
from convert.formats.Fusion.MaterialCodec.Values import DecodeValue as ValueModule

SchemaGrammar.KSchemaAttrs['Distance'] = ('id', 'val', 'label', 'unit')
SchemaGrammar.KSchemaAttrs['TextureURI'] = ('id', 'val', 'label', 'allowmultiplevalues')
SchemaGrammar.KSchemaAttrs['PropertyAlias'] = ('id', 'alias')
SchemaGrammar.KSchemaAttrs['Float'] = SchemaGrammar.KSchemaAttrs['Float'] + ('allowmultiplevalues',)
SchemaGrammar.KSchemaChildren['AssetSchema'] = SchemaGrammar.KSchemaChildren['AssetSchema'] + ('Distance', 'TextureURI', 'PropertyAlias')
SchemaGrammar.KSchemaChildren['Distance'] = ('Bounds',)

COUNTS = {}
original_scalar = ScalarModule.DecodeScalar
original_model = SchemaModule.PropertyModel


def trial_model(value):
    if value.TagName == 'PropertyAlias':
        return PropertySpec('alias:' + dict(value.Attributes)['id'], 'Reference', False, True, False, None, 'single')
    attrs = dict(value.Attributes)
    if value.TagName == 'Distance':
        return PropertySpec(attrs['id'], 'Float', attrs.get('definitionIteratorData') == 'true', attrs.get('readonly') == 'true', False, attrs.get('unit') or 'Distance', 'none')
    if value.TagName == 'TextureURI':
        return PropertySpec(attrs['id'], 'URL', False, False, False, 'TextureURI', 'none')
    return original_model(value)


def trial_scalar(reader, field):
    if field.UnitName == 'TextureURI':
        count = reader.TakeBytes(1)[0]
        COUNTS[count] = COUNTS.get(count, 0) + 1
        return tuple(reader.ReadText() for _ in range(count))
    if field.ValueKind == 'Float' and field.UnitName is not None:
        return UnitValue(reader.ReadInt(), reader.ReadFloat())
    return original_scalar(reader, field)


def trial_check(field):
    return None


SchemaModule.PropertyModel = trial_model
ScalarModule.DecodeScalar = trial_scalar
ValueModule.DecodeScalar = trial_scalar
BuildModule.CheckProperty = trial_check
