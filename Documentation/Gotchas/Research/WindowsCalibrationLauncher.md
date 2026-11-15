# Windows virtual environments can add a launcher process

On Windows, a virtual environment's `python.exe` can start the actual Python interpreter in a child process. The PID returned by launching that executable may belong to the launcher. The launcher's peak working set can therefore differ from the decoder's peak. The supervisor interpreter can also appear in the same job roster as the workers.

Calibration records the exact supervisor interpreter's creation time and verifies its membership before excluding it from active worker samples. The decoder reports its own peak working set while the supervisor receipt still records the owned launcher peak. [Windows offline calibration](../../Changes/Research/Supervisor/WindowsOfflineCalibration.md)
