from convert.formats.Fusion.DrawingCodec.Dwg.Objects.StandardSpecs import (
    KStandardSpecs,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.StyleSpecs import KStyleSpecs
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ViewSpecs import KViewSpecs

KRecordSpecs = {**KStandardSpecs, **KStyleSpecs, **KViewSpecs}
