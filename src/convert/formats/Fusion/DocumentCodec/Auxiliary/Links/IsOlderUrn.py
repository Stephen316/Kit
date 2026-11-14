from re import fullmatch as FullMatch

KVersionUrn = r"(urn:[^?]+)\?version=([1-9][0-9]{0,8})"


def IsOlderUrn(LinkUrn: str, ContextUrn: str) -> bool:
    LinkMatch = FullMatch(KVersionUrn, LinkUrn)
    ContextMatch = FullMatch(KVersionUrn, ContextUrn)
    return (
        LinkMatch is not None
        and ContextMatch is not None
        and LinkMatch.group(1) == ContextMatch.group(1)
        and int(ContextMatch.group(2)) < int(LinkMatch.group(2))
    )
