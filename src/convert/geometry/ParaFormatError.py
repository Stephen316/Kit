# para format error needs a distinct failure contract so geometry translation can report invalid state without losing context
class ParaFormatError(ValueError):
    locals()["__slots__"] = ()
