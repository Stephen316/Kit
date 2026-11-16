# Darwin exit observation precedes reaping the child

A Darwin process exit event can establish that the exact peer exited while its
parent still retains the unreaped child. The Darwin process table can still
return the child's PID to `ps`. The Fusion replacement fence waits for that
process table entry to disappear.

In the disposable two-pair witness, the parent must collect the child's exit
while the acknowledgement marker is pending. Waiting until fixture teardown
can make the parent wait for Phase B while Phase B waits for the old PID to
disappear. Keep the real replacement fence and reap the child through the
fixture process that launched it.
In the owner process, an explicit bounded wait after the exact exit event
also avoids depending on the opportunistic poll when Python starts another
subprocess.
[Darwin exit event implementation](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_exit.c)
[Darwin process table implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c#L3685-L3687)
[CPython subprocess cleanup](https://github.com/python/cpython/blob/v3.14.6/Lib/subprocess.py)
