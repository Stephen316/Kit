from struct import pack as PackFields

from BlindDepth import WriteDepthMut
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# logical dimensions have no scalar, while each driving distance owns its named value
def WriteDimBase(
    Writer: ArchiveWriter,
    Identity: int,
    DcmType: int,
    Parameter: tuple[bytes, bytes] | None = None,
) -> None:
    NullValue = EncodeNull()
    Writer.i32(0)
    if Parameter is None:
        Writer.raw(NullValue)
    else:
        WriteDepthMut(Writer, *Parameter)
    Writer.raw(NullValue)
    Writer.raw(PackFields("<4i", Identity, 0, 0, 0))
    Writer.raw(NullValue)
    # the last three shorts are constraint status, invalidation and dangling state
    Writer.raw(PackFields("<HBi3H", 0, 0, DcmType, 2, 0, 0))
