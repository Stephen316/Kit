from convert.formats.Fusion.MetaIndex import SegmentKind

# the meta index types order must stay explicit so public document claims remain grounded in native records
KMetaIndexTypes: tuple[type[object], ...] = (SegmentKind,)
