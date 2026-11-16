from typing import TypeAlias

# the json value variants need one shared contract so bundle reconstruction cannot omit a supported value shape
KJsonValue: TypeAlias = (  # lgtm[py/unused-global-variable]
    None | bool | int | float | str | list["KJsonValue"] | dict[str, "KJsonValue"]
)
