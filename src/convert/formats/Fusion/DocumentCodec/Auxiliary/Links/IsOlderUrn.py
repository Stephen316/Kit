from re import fullmatch as FullMatch

# version urn must remain consistent across callers so supporting records retain their owning document relationships
KVersionUrn = r"(urn:[^?]+)\?version=([1-9][0-9]{0,8})"


# the older urn decision must stay consistent so supporting records retain their owning document relationships
def IsOlderUrn(LinkUrn: str, ContextUrn: str) -> bool:
    LinkMatch = FullMatch(KVersionUrn, LinkUrn)
    ContextMatch = FullMatch(KVersionUrn, ContextUrn)
    return (
        LinkMatch is not None
        and ContextMatch is not None
        and LinkMatch.group(1) == ContextMatch.group(1)
        and int(ContextMatch.group(2)) < int(LinkMatch.group(2))
    )
