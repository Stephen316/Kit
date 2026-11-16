# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace

from PairedCaptureIntake import require
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed


# Preserve the native continuation records while changing only one typed field.
def mutation_archive(model, node, name, value):
    segments = []
    changes = 0
    for segment in model.Segments:
        if segment.Metadata.Header.SegmentId != node.SegmentId:
            segments.append(segment)
            continue
        records = []
        for record in segment.Records:
            if record.ObjectId != node.ObjectId:
                records.append(record)
                continue
            groups = []
            for group in record.Groups:
                fields = []
                for field in group.Fields:
                    if field.FieldName == name:
                        field = replace(field, Value=value)
                        changes += 1
                    fields.append(field)
                groups.append(replace(group, Fields=tuple(fields)))
            records.append(replace(record, Groups=tuple(groups)))
        segments.append(replace(segment, Records=tuple(records)))
    require(changes == 1, f"Expected one typed field {node.ClassName}.{name}")
    return EmitParsed(replace(model, Segments=tuple(segments)))
