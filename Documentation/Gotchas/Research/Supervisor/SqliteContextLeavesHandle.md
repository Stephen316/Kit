# SQLite context leaves the Windows store handle open

## Expectation

The grouped crash fixture reads the recovered job metadata and removes its private controller store when the case exits.

## Actual behavior

The SQLite connection context manager finishes the transaction and leaves the connection open. Windows rejects removing the ledger while a reader still holds its handle. The hosted crash case reached temporary directory cleanup and failed with `WinError 32` on `ledger.sqlite3`. [Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43715564751/job/132816225586)

## Workaround

Wrap read-only fixture connections with `contextlib.closing`. Materialize the selected rows inside that scope so the database handle closes before temporary store cleanup.
