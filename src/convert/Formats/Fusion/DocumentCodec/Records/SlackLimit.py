from convert.Formats.Fusion.MetaIndex import SegmentKind

# max design slack must remain consistent across callers so model state retains its native feature and ownership relationships
KMaxDesignSlack = 16

# the slack kinds order must stay explicit so model state retains its native feature and ownership relationships
KSlackKinds = (SegmentKind.KAct, SegmentKind.KDesign, SegmentKind.KBrowser)
