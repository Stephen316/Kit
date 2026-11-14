import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from TrySchema import CATALOG


def owners(field_name):
    for guid, schemas in CATALOG.Classes.items():
        for schema in schemas:
            for member in schema.Members:
                if member.FieldName == field_name:
                    yield guid, schema.SchemaVersion, member.ValueType


def show(guid):
    for schema in sorted(CATALOG.Classes.get(guid.upper(), ()), key=lambda item: item.SchemaVersion):
        members = ', '.join(f'{member.FieldName}:{member.ValueType.KindValue}{"" if member.IsSaved else "(unsaved)"}' for member in schema.Members)
        print(f'  v{schema.SchemaVersion} base {schema.BaseGuid[:8]} value={schema.IsValue}: {members}')


def main():
    field_name = sys.argv[1]
    seen = set()
    for guid, version, value_type in owners(field_name):
        print(f'owner {guid[:8]} v{version} {field_name}: {value_type.KindValue} {value_type.ClassGuid}')
        target = value_type.ClassGuid or next((argument.ClassGuid for argument in value_type.Arguments if argument.ClassGuid), '')
        if target and target not in seen:
            seen.add(target)
            print(f' class {target}')
            show(target)


if __name__ == '__main__':
    main()
