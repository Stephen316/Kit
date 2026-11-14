from typing import TypeAlias

KJsonValue: TypeAlias = (  # lgtm[py/unused-global-variable]
    None | bool | int | float | str | list["KJsonValue"] | dict[str, "KJsonValue"]
)
