from json import dumps as DumpJson


# human conversion reports must expose writer evidence and unresolved application acceptance
def PrintReport(Report: dict[str, object]) -> None:
    print("Wrote " + DumpJson(Report["path"], ensure_ascii=True))
    for FieldName in (
        "source_format",
        "destination_format",
        "bytes_written",
        "application_usable",
        "vendor_loadable",
        "dropped",
        "requirements",
        "transfers",
        "diagnostics",
    ):
        print(FieldName + ": " + DumpJson(Report[FieldName], ensure_ascii=True))
    print(str(Report["acceptance"]))
