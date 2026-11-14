import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { readFile, writeFile, unlink, mkdir, rm, stat } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const scriptPath = resolve(process.argv[2]);
const timeoutIndex = process.argv.indexOf('--timeout');
const waitSeconds = timeoutIndex > 0 ? Number(process.argv[timeoutIndex + 1]) : 1800;
const lockPath = join(tmpdir(), 'kit-fusion-oracle.lock');
const ownerPath = join(lockPath, 'owner.json');

async function acquire() {
  for (;;) {
    try {
      await mkdir(lockPath);
      await writeFile(ownerPath, JSON.stringify({ pid: process.pid, script: scriptPath, since: Date.now(), waitSeconds }));
      return;
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      try {
        const owner = JSON.parse(await readFile(ownerPath, 'utf8'));
        let alive = true;
        try { process.kill(owner.pid, 0); } catch { alive = false; }
        const expired = Date.now() - owner.since > (owner.waitSeconds + 120) * 1000;
        if (!alive || expired) await rm(lockPath, { recursive: true, force: true });
      } catch {
        try {
          const info = await stat(lockPath);
          if (Date.now() - info.mtimeMs > 60000) await rm(lockPath, { recursive: true, force: true });
        } catch {}
      }
      await delay(2000);
    }
  }
}

async function release() {
  await rm(lockPath, { recursive: true, force: true });
}

await acquire();
process.on('SIGINT', async () => { await release(); process.exit(130); });
process.on('SIGTERM', async () => { await release(); process.exit(143); });

const dispatchPath = join(tmpdir(), `kit-fusion-${randomUUID()}.py`);
const resultPath = `${dispatchPath}.json`;
try {
  await writeFile(dispatchPath, `import json, runpy, traceback\nfrom pathlib import Path\ndef _kit_dispatch():\n    try:\n        runpy.run_path(${JSON.stringify(scriptPath)}, run_name="__kit_fusion_oracle__")\n        result = {"status": "completed"}\n    except Exception:\n        result = {"status": "failed", "traceback": traceback.format_exc()}\n    Path(${JSON.stringify(resultPath)}).write_text(json.dumps(result))\n_kit_dispatch()\n`);
  const targets = await (await fetch('http://127.0.0.1:9766/json/list', { signal: AbortSignal.timeout(10000) })).json();
  const target = targets.find(value => value.title === 'Fusion Home Tab (HomeTab)');
  if (!target) throw new Error('Fusion home tab is unavailable');
  await new Promise((done, fail) => {
    const socket = new WebSocket(target.webSocketDebuggerUrl);
    const timer = setTimeout(() => { socket.close(); fail(new Error('Fusion bridge did not answer')); }, 15000);
    socket.onopen = () => socket.send(JSON.stringify({
      id: 1,
      method: 'Runtime.evaluate',
      params: {
        expression: `window.neutronJavaScriptObject.executeCommand("RunScriptCommand", ${JSON.stringify(JSON.stringify({ Path: dispatchPath }))})`,
        returnByValue: true,
      },
    }));
    socket.onmessage = event => {
      const message = JSON.parse(event.data);
      if (message.id !== 1) return;
      clearTimeout(timer);
      socket.close();
      done();
    };
    socket.onerror = event => { clearTimeout(timer); socket.close(); fail(new Error(String(event))); };
  });
  let finished = false;
  for (let attempt = 0; attempt < waitSeconds; attempt += 1) {
    try {
      const result = JSON.parse(await readFile(resultPath, 'utf8'));
      console.log(JSON.stringify(result));
      if (result.status !== 'completed') process.exitCode = 1;
      finished = true;
      break;
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    await delay(1000);
  }
  if (!finished) {
    console.error(`Fusion script did not report completion within ${waitSeconds} s: ${resultPath}`);
    process.exitCode = 1;
  }
} finally {
  await unlink(dispatchPath).catch(() => {});
  await unlink(resultPath).catch(() => {});
  await release();
}
