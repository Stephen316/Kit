# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters import AdapterRegistry


def AssertAliases(Registry: AdapterRegistry) -> None:
    for ReaderData in Registry.readers():
        for FormatId in (ReaderData.info.format_id, *ReaderData.info.aliases):
            assert Registry.reader(FormatId) is ReaderData
    for WriterData in Registry.writers():
        for FormatId in (WriterData.info.format_id, *WriterData.info.aliases):
            assert Registry.writer(FormatId) is WriterData
