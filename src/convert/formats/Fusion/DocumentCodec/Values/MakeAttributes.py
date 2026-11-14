def MakeAttributes(**Fields: int) -> list[dict[str, object]]:
    return [
        {"name": NameValue, "metatype": "IntrinsicMetaTypeuint64", "value": Value}
        for NameValue, Value in Fields.items()
    ]
