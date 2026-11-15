from json import dumps as JsonText

# the json value variants need one shared contract so drawing view authoring cannot omit a supported value shape
KJsonValue = (
    None | bool | int | float | str | list["KJsonValue"] | dict[str, "KJsonValue"]
)


# the hole data contract needs a shared interpretation so projected geometry retains its paper and model relationships
def HoleData(BodyId: int) -> str:
    BodyInfo: dict[str, KJsonValue] = {
        "BodyInDirectModeling": False,
        "ComponentOccurencePaths": [None],
        "FeatureSetIndex": 0,
        "bodyId": BodyId,
    }
    Features: dict[str, KJsonValue] = {"Features": None, "LocalModifiers": None}
    Document: dict[str, KJsonValue] = {
        "BodyInfos": [BodyInfo],
        "FeatureSets": [Features],
        "IdenticalFeatures": None,
    }
    return StyledJson(Document, 0)


# the styled json contract needs a shared interpretation so projected geometry retains its paper and model relationships
def StyledJson(Value: KJsonValue, Depth: int) -> str:
    Margin = "\t" * Depth
    if isinstance(Value, dict) and Value:
        Members = [
            f"{Margin}\t{JsonText(KeyText)} : {NestedJson(Value[KeyText], Depth + 1)}"
            for KeyText in sorted(Value)
        ]
        return "{\n" + ",\n".join(Members) + "\n" + Margin + "}"
    if isinstance(Value, list) and Value:
        Members = [f"{Margin}\t{StyledJson(Entry, Depth + 1)}" for Entry in Value]
        return "[\n" + ",\n".join(Members) + "\n" + Margin + "]"
    return JsonText(Value)


# the nested json contract needs a shared interpretation so projected geometry retains its paper and model relationships
def NestedJson(Value: KJsonValue, Depth: int) -> str:
    if isinstance(Value, dict | list) and Value:
        return "\n" + "\t" * Depth + StyledJson(Value, Depth)
    return StyledJson(Value, Depth)
