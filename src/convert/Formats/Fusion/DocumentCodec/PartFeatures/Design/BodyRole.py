from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


# the body role contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def BodyRole(Ordinal: int, RoleName: str) -> str:
    return RoleName if Ordinal == 1 else RoleName + str(Ordinal)


# the focus role contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def FocusRole(Author: AuthorState, RoleName: str) -> str:
    return BodyRole(Author.FocusOrdinal, RoleName)
