import os as OsModule
import tempfile as TempFiles
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path as FilePath

from tests.Research.FusionChecks import ReportCensus, VerifyChunk
from tests.Research.FusionClient import FusionAssets, KControlAsset, ReadChunk


def CheckFusionSet() -> None:
    AssetMap = {str(Asset["path"]): Asset for Asset in FusionAssets()}
    assert len(AssetMap) == 714
    PathList = sorted(AssetMap)
    ChunkCount = max(1, min(8, OsModule.cpu_count() or 1))
    ChunkList = [PathList[Index::ChunkCount] for Index in range(ChunkCount)]
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetList = [FilePath(TempPath) / str(Index) for Index in range(ChunkCount)]
        with ThreadPoolExecutor(max_workers=ChunkCount) as WorkerPool:
            Results = list(WorkerPool.map(ReadChunk, TargetList, ChunkList))
        Entries: list[dict[str, str]] = []
        for TargetPath, ResultInfo in Results:
            assert ResultInfo.returncode in (0, 3), ResultInfo.stderr
            Entries += VerifyChunk(TargetPath, AssetMap)
    assert sorted(Entry["path"] for Entry in Entries) == PathList
    Control = next(Entry for Entry in Entries if Entry["path"] == KControlAsset)
    assert Control["outcome"] == "decoded"
    assert Control["reader_mode"] == "strict"
    ReportCensus(Entries)
