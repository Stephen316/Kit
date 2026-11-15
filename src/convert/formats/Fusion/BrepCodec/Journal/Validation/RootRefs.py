# root references needs a stable location so journal validation resolves inputs independently of the caller working directory
KRootRefs: dict[str, int] = {
    "body": 3,
    "face": 5,
    "edge": 7,
}
