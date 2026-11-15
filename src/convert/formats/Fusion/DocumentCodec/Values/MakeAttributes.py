# the attributes operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def MakeAttributes(**Fields: int) -> list[dict[str, object]]:
    return [
        {"name": NameValue, "metatype": "IntrinsicMetaTypeuint64", "value": Value}
        for NameValue, Value in Fields.items()
    ]
