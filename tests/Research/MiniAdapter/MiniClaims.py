import secrets as Secrets
from pathlib import Path as FilePath

from tests.Research.MiniAdapter.ClaimFile import WriteClaim
from tests.Research.MiniAdapter.ClaimPayload import BuildClaim
from tests.Research.MiniAdapter.JobReadiness import IsJobReady
from tests.Research.MiniAdapter.LeaseStart import StartLeaseMut
from tests.Research.MiniAdapter.MiniState import MiniState


# the supervisor claim contract needs a small persistent adapter for controller independent coverage
class MiniClaims(MiniState):

    # the fixture must give the supervisor one eligible claim with the same fenced protocol
    def ClaimJob(
        self, PoolName: str, Worker: str, ClaimPath: FilePath
    ) -> dict[str, object] | None:
        with self.OpenState() as Current:
            if PoolName not in Current.Pools.values():
                raise ValueError("pool has no registered job kinds")
            Running = [
                Entry
                for Entry in Current.JobMap.values()
                if Entry.JobState == "running"
            ]

            # original submission order keeps equivalent claim attempts deterministic across controller processes
            for JobName, Entry in sorted(
                Current.JobMap.items(), key=lambda JobPair: JobPair[1].Order
            ):
                if not IsJobReady(Entry, Current, PoolName, Running):
                    continue
                if Entry.Attempts >= Entry.MaxAttempts:
                    Entry.JobState = "failed"
                    continue
                Token = Secrets.token_hex(32)
                StartLeaseMut(Entry, Worker, Token)
                ClaimInfo = BuildClaim(JobName, Entry, Current)
                WriteClaim(ClaimPath, ClaimInfo, Token)
                return ClaimInfo
        return None
