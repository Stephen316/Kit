from types import MappingProxyType

KVectorFields = MappingProxyType(
    {
        ("cone-surface", 3): (19, 10),
        ("cone-surface", 4): (20, 1),
        ("cone-surface", 5): (20, 10),
        ("plane-surface", 3): (19, 10),
        ("plane-surface", 4): (20, 1),
        ("plane-surface", 5): (20, 1),
        ("ellipse-curve", 3): (19, 10),
        ("ellipse-curve", 4): (20, 1),
        ("ellipse-curve", 5): (20, 10),
        ("point", 3): (19, 10),
    }
)
KLengthScalars = frozenset({("cone-surface", 11)})
