from math import isfinite as IsFinite
from re import fullmatch as FullMatch


def InchDecimal(TextValue: str) -> tuple[float, int] | None:
    Match = FullMatch(
        r"(?:<MOD-DIAM>|R)?\s*([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))",
        TextValue.strip(),
    )
    if Match is None:
        return None
    Displayed = float(Match[1])
    Fraction = Match[1].partition(".")[2].rstrip("0")
    return (Displayed, len(Fraction)) if IsFinite(Displayed) else None
