# Archive report digests depend on stdout line endings

Fusion evidence commands write JSON through a text stream. Windows emits CRLF and Linux emits LF. The SOLIDWORKS commands write UTF-8 directly to the binary stream and emit LF on both systems.

At `94d54e06`, the hosted gate rejected five Fusion digests originally captured on Windows. Replacing CRLF with LF in the original reports reproduced all five hosted digests exactly. The hosted gate now canonicalizes only line endings, so every other report byte still participates in the comparison. [Initial hosted run](https://github.com/TryUniCAD/Kit/actions/runs/43721308138/job/132833762444)
