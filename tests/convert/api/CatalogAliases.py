from convert.adapters import AdapterRegistry


def AssertAliases(Registry: AdapterRegistry) -> None:
    for ReaderData in Registry.readers():
        for FormatId in (ReaderData.info.format_id, *ReaderData.info.aliases):
            assert Registry.reader(FormatId) is ReaderData
    for WriterData in Registry.writers():
        for FormatId in (WriterData.info.format_id, *WriterData.info.aliases):
            assert Registry.writer(FormatId) is WriterData
