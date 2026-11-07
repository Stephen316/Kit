# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.AdapterInfo import KReaderInfo
from convert.adapters.Fusion.ArchiveProbe import ProbeFusion
from convert.adapters.Fusion.ReaderOptions import GetFusionOpts
from convert.adapters.Fusion.StreamRead import ReadSourceMut
from convert.formats.Fusion.DocumentRead import ReadFusionDoc
from interchange.document.models.DocumentFilter import FilterDocument
from interchange.document.models.DocumentModel import CadDocument


# the structural reader exposes the qualified projection through adapter discovery
class FusionReader:

    # the registry needs format metadata without opening a source document
    @property
    def Info(self) -> AdapterInfo:
        return KReaderInfo

    info = Info

    # the reader can rank native archives without consuming stream content
    def Probe(self, SourceData: KSourceType) -> ProbeResult:
        return ProbeFusion(SourceData)

    # public probe keywords match the registry reader protocol
    def probe(self, source: KSourceType) -> ProbeResult:
        return self.Probe(source)

    # explicit options allow callers to select and filter one native history
    def Read(
        self, SourceData: KSourceType, Options: ReadOptions | None = None
    ) -> CadDocument:
        Settings = Options if Options is not None else ReadOptions()
        HistoryId, Inflate = GetFusionOpts(Settings)
        Document = ReadFusionDoc(
            ReadSourceMut(SourceData),
            HistoryId=HistoryId,
            InflateZstd=Inflate,
        )
        return FilterDocument(
            Document,
            IncludeBrep=Settings.include_brep,
            IncludeMesh=Settings.include_tessellation,
        )

    # public read keywords match the registry reader protocol
    def read(
        self, source: KSourceType, options: ReadOptions | None = None
    ) -> CadDocument:
        return self.Read(source, options)
