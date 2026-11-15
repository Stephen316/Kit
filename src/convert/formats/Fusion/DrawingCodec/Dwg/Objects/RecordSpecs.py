from convert.formats.Fusion.DrawingCodec.Dwg.Objects.StandardSpecs import (
    KStandardSpecs,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.StyleSpecs import KStyleSpecs
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ViewSpecs import KViewSpecs

# the record specifications vocabulary must stay centralized so native drawing reconstruction agrees on supported native identities
KRecordSpecs = {**KStandardSpecs, **KStyleSpecs, **KViewSpecs}
