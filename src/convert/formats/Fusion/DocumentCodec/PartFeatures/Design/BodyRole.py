from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def BodyRole(Ordinal: int, RoleName: str) -> str:
    return RoleName if Ordinal == 1 else RoleName + str(Ordinal)


def FocusRole(Author: AuthorState, RoleName: str) -> str:
    return BodyRole(Author.FocusOrdinal, RoleName)
