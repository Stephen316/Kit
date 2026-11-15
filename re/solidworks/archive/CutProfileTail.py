"""Keep the existing cut profile report shape on the packaged reader."""

from convert.adapters.solidworks.resolved.CutProfileSeal import ReadCutSeal


def read_cut_profile_tail(cursor, cut, boss):
    return ReadCutSeal(cursor, cut, boss["file_ref_object"])
