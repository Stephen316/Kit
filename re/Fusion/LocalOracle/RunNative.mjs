import { resolve } from 'node:path';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { readFile, writeFile, unlink } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const scriptPath = resolve(process.argv[2]);
const dispatchPath = join(tmpdir(), `kit-fusion-${randomUUID()}.py`);
const resultPath = `${dispatchPath}.json`;
await writeFile(dispatchPath, `import json, runpy, traceback\nfrom pathlib import Path\ndef _kit_dispatch():\n    try:\n        runpy.run_path(${JSON.stringify(scriptPath)}, run_name="__kit_fusion_oracle__")\n        result = {"status": "completed"}\n    except Exception:\n        result = {"status": "failed", "traceback": traceback.format_exc()}\n    Path(${JSON.stringify(resultPath)}).write_text(json.dumps(result))\n_kit_dispatch()\n`);
const targets = await (await fetch('http://127.0.0.1:9766/json/list', {signal: AbortSignal.timeout(10000)})).json();
const target = targets.find(value => value.title === 'Fusion Home Tab (HomeTab)');
if (!target) throw new Error('Fusion home tab is unavailable');
const socket = new WebSocket(target.webSocketDebuggerUrl);
const timeout = setTimeout(() => {
  socket.close();
  process.exitCode = 1;
}, 15000);
socket.onopen = () => socket.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {
    expression: `window.neutronJavaScriptObject.executeCommand("RunScriptCommand", ${JSON.stringify(JSON.stringify({Path:dispatchPath}))})`,
    returnByValue: true,
  },
}));
socket.onmessage = event => {
  const message = JSON.parse(event.data);
  if (message.id !== 1) return;
  console.log(JSON.stringify(message));
  clearTimeout(timeout);
  socket.close();
};
socket.onerror = event => {
  console.error(String(event));
  clearTimeout(timeout);
  socket.close();
  process.exitCode = 1;
};
for (let attempt = 0; attempt < 180; attempt += 1) {
  try {
    const result = JSON.parse(await readFile(resultPath, 'utf8'));
    console.log(JSON.stringify(result));
    if (result.status !== 'completed') process.exitCode = 1;
    await unlink(dispatchPath);
    await unlink(resultPath);
    process.exit(process.exitCode ?? 0);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  await delay(1000);
}
throw new Error(`Fusion script did not report completion: ${resultPath}`);
