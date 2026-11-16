# Allow the macOS supervisor suite to finish

The hosted `macOS research supervisor` job has a 20-minute job timeout. It keeps the same macOS runner, setup and process verification selections. The job timeout covers checkout, dependency setup and the complete suite. The application, queue and fixture deadlines retain their existing values.

At PR head `3cd136ad`, the successful pytest step took 13 minutes 29 seconds. The next run at `7e8e98b8` reached the previous 15-minute job limit and was cancelled before publishing the new lifecycle verdicts. The extended job budget applies to the next hosted run. [Successful suite](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019772047) · [Cancelled suite](https://github.com/TryUniCAD/Kit/actions/runs/43784421558/job/133028849064)
