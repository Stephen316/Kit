from convert.api.ApiContext import GetRegistry


# users need adapter discovery to distinguish available readers from supported output writers
def FormatReport() -> list[dict[str, object]]:
    Registry = GetRegistry()
    Readers = {Adapter.info.FormatId: Adapter.info for Adapter in Registry.GetReaders()}
    Writers = {Adapter.info.FormatId: Adapter.info for Adapter in Registry.GetWriters()}
    return [
        {
            "format": FormatId,
            "name": (Readers.get(FormatId) or Writers[FormatId]).DisplayName,
            "extensions": (Readers.get(FormatId) or Writers[FormatId]).Extensions,
            "aliases": (Readers.get(FormatId) or Writers[FormatId]).AliasNames,
            "read": FormatId in Readers,
            "write": FormatId in Writers,
        }
        for FormatId in sorted(Readers.keys() | Writers.keys())
    ]
