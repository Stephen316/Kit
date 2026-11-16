# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Preserve the sampled report schema for packaged chooser records."""


# The original private evidence report names the one side alias in singular form.
def report_choices(choices):
    return {
        **choices,
        "caps": [
            {
                key: value
                for key, value in record.items()
                if key not in ("body", "classifier")
            }
            for record in choices["caps"]
        ],
        "cap_aliases": [
            {
                **{
                    key: value
                    for key, value in record.items()
                    if key not in ("body", "classifier", "edge_objects")
                },
                "edge_object": record["edge_objects"][0],
            }
            for record in choices["cap_aliases"]
        ],
    }
