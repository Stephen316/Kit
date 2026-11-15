from tests.Research.MiniAdapter.MiniState import MiniState


# controller independent coverage still needs the pool and capacity contract used by the supervisor
class MiniResources(MiniState):

    # the fixture must reject changes that would make a job kind eligible in conflicting pools
    def DefinePool(self, PoolName: str, KindList: list[str]) -> dict[str, object]:
        with self.OpenState() as Current:
            for KindName in KindList:
                if Current.Pools.get(KindName, PoolName) != PoolName:
                    raise ValueError("job kind already belongs to another pool")
            for KindName in [
                KindKey
                for KindKey, PoolKey in Current.Pools.items()
                if PoolKey == PoolName
            ]:
                del Current.Pools[KindName]
            Current.Pools.update({KindName: PoolName for KindName in KindList})
        return {"pool": PoolName, "kinds": sorted(KindList)}

    # admission tests need counted resource capacity persisted alongside queue state
    def DefineResource(self, ResName: str, Capacity: int) -> dict[str, object]:
        with self.OpenState() as Current:
            Current.Capacity[ResName] = Capacity
        return {"name": ResName, "capacity": Capacity}
