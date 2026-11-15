# Verify the application handoff between two supervised jobs

The hosted process fixture queues two jobs on one counted installation resource in a private A03 store. The second job receives the first job's accepted result through its declared dependency. It verifies that result before entering the existing restart wait.

The fixture holds the original worker process alive while the second claim waits. By then the controller has accepted the first result, the supervisor has acknowledged its spool, and the fence still names the original host. The second job has published no requests. The fixture stops the original host and starts a replacement under the same private installation. It verifies both attempt numbers, event order, the replacement identity in the accepted result and successful acknowledgement of both spools.

The witness uses disposable operating-system processes. It exercises the existing controller, supervisor, acknowledgement and restart admission paths. Scheduled resets of a reused native installation and native healthy controls have separate evidence requirements. Hosted verification of this change is pending.
