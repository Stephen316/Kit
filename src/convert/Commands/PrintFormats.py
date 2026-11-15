from json import dumps as DumpJson


# terminal users need a compact capability overview before selecting conversion formats
def PrintFormats(Formats: list[dict[str, object]]) -> None:
    print("format\tread\twrite\textensions")
    for Format in Formats:
        print(
            "\t".join(
                DumpJson(Format[FieldName], ensure_ascii=True)
                for FieldName in ("format", "read", "write", "extensions")
            )
        )
