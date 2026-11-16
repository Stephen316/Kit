from struct import pack as Pack

from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the installed standard's default Swift lengths, limits and precisions
def WriteSwiftDefaults(Writer: ArchiveWriter) -> None:
    Writer.raw(Pack("<d2i", 0.00005, 2, 2))
    for Tolerance in (0.0001, 0.0002, 0.0002, 0.0005, 0.00025):
        Writer.raw(Pack("<di", Tolerance, 2))
    Writer.raw(Pack("<d2idid", 0.0005, 2, 2, 0.0001, 2, -0.00025))
    for Limit in (0.0005, 0.0005, 0.00025, 0.0002):
        Writer.raw(Pack("<3i2d", 2, 2, 2, Limit, -Limit))

    Writer.raw(Pack("<7i", 2, 2, 2, 2, 2, 2, 2))
    Writer.raw(Pack("<2d2i2d", 0.0005, -0.0005, 2, 2, 0.00025, -0.00025))
    Writer.raw(Pack("<4i2d", 2, 2, 2, 2, 0.01, 1.0))
    for _ in range(9):
        Writer.i32(2)
    for _ in range(9):
        Writer.i32(0)
    Writer.i32(1)

    Writer.raw(Pack("<5d2i", 0.0001, 0.00025, 0.00025, 0.0005, -0.0005, 2, 0))
    for _ in range(4):
        Writer.raw(Pack("<2d4i", 0.0005, -0.0005, 2, 2, 1, 2))
    for _ in range(15):  # enabled default tolerance flags
        Writer.i32(1)
    AngleLimit = 0.00872664625997
    Writer.raw(Pack("<4d", 0.0005, -0.0005, AngleLimit, -AngleLimit))
    Writer.raw(Pack("<10i", 2, 2, 2, 2, 1, 1, 2, 2, 1, 1))
    Writer.raw(Pack("<4d", 2.0 * AngleLimit, -2.0 * AngleLimit, AngleLimit, -AngleLimit))
    Writer.raw(Pack("<12i", 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0))
    Writer.raw(Pack("<6i", 0, 0, 5, -1, 1, 0))
