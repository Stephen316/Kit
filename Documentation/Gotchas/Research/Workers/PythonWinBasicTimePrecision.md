# Pywin32 basic time precision

## Expectation

Reading a Windows `FILE_BASIC_INFO` dictionary and writing it back with only
`ChangeTime` altered preserves every other timestamp bit.

## Actual behavior

The pinned [b312 file API](https://github.com/mhammond/pywin32/blob/b312/win32/src/win32file.i)
converts these timestamps with `PyWinObject_FromTimeStamp`. The pinned
[time conversion implementation](https://github.com/mhammond/pywin32/blob/b312/win32/src/PyTime.cpp)
converts through `FILETIME`, `SYSTEMTIME` and Python datetime. `SYSTEMTIME` retains
milliseconds; the reverse conversion divides datetime microseconds by 1000.
Sub-millisecond timestamp bits are not retained. This is a source inspection
finding, not a measured Windows run.

Consequently, reconstructing all fields to change only `ChangeTime` can also
change the modification timestamp. Such a fixture cannot independently establish
that the reader retained its handle change-time guard.

## Workaround

The real Windows record fixture pins access and modification timestamps to exact
seconds before taking its baseline. After changing only `ChangeTime`, it asserts
that every shared path/handle identity field remains equal and that descriptor
change time differs. Only then does it require the protected reader to reject the
mutation. Production comparisons continue to use CPython nanosecond fields;
they do not round values through pywin32 datetime.

The new process case requires remote Windows verification. No local Windows
imports, execution or tests were performed.
