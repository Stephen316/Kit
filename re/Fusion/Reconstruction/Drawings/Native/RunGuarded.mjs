// Run one Fusion script under the shared oracle lock, and restart Fusion under that same lock when a watched
// drawing open stalls, shows the "Fusion Drawings Message" or "Fusion" message dialog, or Fusion exits.
//
// Usage: node RunGuarded.mjs <script.py> [--timeout S] [--watch <checkpoint.json>] [--stage <text>]
//                            [--stall S] [--events <events.json>] [--label <name>]
//
// The lock protocol is the one of re/Fusion/LocalOracle/RunLocked.mjs, so the agents that share Fusion keep
// taking turns. The checkpoint file is the Inspect<tag>.json report that InspectUploads.py writes before each open.
import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { readFile, writeFile, unlink, mkdir, rm, stat } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const argv = process.argv.slice(2);
const option = (name, fallback) => {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : fallback;
};
const scriptPath = resolve(argv[0]);
const waitSeconds = Number(option('--timeout', 1800));
const watchPath = option('--watch', null);
const stageText = option('--stage', 'opening drawing');
const stallSeconds = Number(option('--stall', 60));
const eventsPath = option('--events', null);
const label = option('--label', scriptPath);
const lockPath = join(tmpdir(), 'kit-fusion-oracle.lock');
const ownerPath = join(lockPath, 'owner.json');
const bridge = 'http://127.0.0.1:9766/json/list';

async function acquire() {
  for (;;) {
    try {
      await mkdir(lockPath);
      await writeFile(ownerPath, JSON.stringify({ pid: process.pid, script: scriptPath, since: Date.now(), waitSeconds: waitSeconds + 900 }));
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

function pids(args) {
  const out = spawnSync('pgrep', args, { encoding: 'utf8' }).stdout || '';
  return out.split(/\s+/).filter(Boolean).map(Number);
}

const fusionPids = () => pids(['-x', 'Autodesk Fusion']);
const enginePids = () => pids(['-f', 'AcCoreConsole.app/Contents/MacOS/AcCoreConsole']);

function alive(pid) {
  try { process.kill(pid, 0); return true; } catch { return false; }
}

function dialogText() {
  const main = fusionPids();
  if (!main.length) return null;
  const script = `tell application "System Events" to tell (first process whose unix id is ${main[0]}) to get value of static texts of (every window whose name is "Fusion Drawings Message" or name is "Fusion")`;
  const out = spawnSync('osascript', ['-e', script], { encoding: 'utf8', timeout: 20000 }).stdout || '';
  return out.trim() || null;
}

function windowTitles() {
  const main = fusionPids();
  if (!main.length) return null;
  const script = `tell application "System Events" to tell (first process whose unix id is ${main[0]}) to get title of every window`;
  const out = spawnSync('osascript', ['-e', script], { encoding: 'utf8', timeout: 20000 }).stdout || '';
  return out.trim() || null;
}

async function targets() {
  try {
    return await (await fetch(bridge, { signal: AbortSignal.timeout(5000) })).json();
  } catch {
    return [];
  }
}

async function dispatch(path, resultPath) {
  const dispatchPath = `${resultPath}.py`;
  await writeFile(dispatchPath, `import json, runpy, traceback\nfrom pathlib import Path\ndef _kit_dispatch():\n    try:\n        runpy.run_path(${JSON.stringify(path)}, run_name="__kit_fusion_oracle__")\n        result = {"status": "completed"}\n    except Exception:\n        result = {"status": "failed", "traceback": traceback.format_exc()}\n    Path(${JSON.stringify(resultPath)}).write_text(json.dumps(result))\n_kit_dispatch()\n`);
  const target = (await targets()).find(value => value.title === 'Fusion Home Tab (HomeTab)');
  if (!target) throw new Error('Fusion home tab is unavailable');
  await new Promise((done, fail) => {
    const socket = new WebSocket(target.webSocketDebuggerUrl);
    let sent = false;
    const timer = setTimeout(() => { socket.close(); if (sent) done(); else fail(new Error('Fusion bridge did not answer')); }, 15000);
    socket.onopen = () => {
      sent = true;
      socket.send(JSON.stringify({
      id: 1,
      method: 'Runtime.evaluate',
      params: {
        expression: `window.neutronJavaScriptObject.executeCommand("RunScriptCommand", ${JSON.stringify(JSON.stringify({ Path: dispatchPath }))})`,
        returnByValue: true,
      },
    }));
    };
    socket.onmessage = event => {
      const message = JSON.parse(event.data);
      if (message.id !== 1) return;
      clearTimeout(timer);
      socket.close();
      done();
    };
    socket.onerror = event => { clearTimeout(timer); socket.close(); fail(new Error(String(event))); };
  });
  return dispatchPath;
}

async function onlineProbe() {
  const resultPath = join(tmpdir(), `kit-fusion-${randomUUID()}.json`);
  const probePath = `${resultPath}.probe.py`;
  await writeFile(probePath, `import json, adsk.core\napp = adsk.core.Application.get()\nhub = app.data.activeHub\nimport pathlib\npathlib.Path(${JSON.stringify(resultPath + '.state')}).write_text(json.dumps({"offline": app.isOffLine, "hub": hub is not None}))\n`);
  try {
    const dispatchPath = await dispatch(probePath, resultPath);
    for (let attempt = 0; attempt < 60; attempt += 1) {
      try {
        const state = JSON.parse(await readFile(`${resultPath}.state`, 'utf8'));
        await unlink(dispatchPath).catch(() => {});
        return state;
      } catch {}
      await delay(1000);
    }
  } catch {}
  return null;
}

async function restartFusion(reason) {
  const started = Date.now();
  const before = { fusion: fusionPids(), engines: enginePids() };
  for (const pid of [...before.engines, ...before.fusion]) { try { process.kill(pid, 'SIGTERM'); } catch {} }
  for (let attempt = 0; attempt < 30 && [...before.engines, ...before.fusion].some(alive); attempt += 1) await delay(1000);
  for (const pid of [...before.engines, ...before.fusion]) { if (alive(pid)) { try { process.kill(pid, 'SIGKILL'); } catch {} } }
  await delay(2000);
  const holders = (spawnSync('lsof', ['-nP', '-iTCP:9766', '-sTCP:LISTEN', '-t'], { encoding: 'utf8' }).stdout || '').split(/\s+/).filter(Boolean).map(Number);
  for (const pid of holders) { try { process.kill(pid, 'SIGKILL'); } catch {} }
  for (const pid of pids(['-f', 'CER/dialog/cer_dialog'])) { try { process.kill(pid, 'SIGKILL'); } catch {} }
  for (const pid of pids(['-f', 'CER/service/cer_service'])) { try { process.kill(pid, 'SIGKILL'); } catch {} }
  await delay(2000);
  execFileSync('open', ['-a', 'Autodesk Fusion']);
  let bridgeUp = false;
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if ((await targets()).some(value => value.title === 'Fusion Home Tab (HomeTab)')) { bridgeUp = true; break; }
    await delay(5000);
  }
  let state = null;
  if (bridgeUp) {
    await delay(10000);
    for (let attempt = 0; attempt < 20; attempt += 1) {
      state = await onlineProbe();
      if (state && !state.offline && state.hub) break;
      await delay(10000);
    }
  }
  return { reason, before, bridge: bridgeUp, state, seconds: Math.round((Date.now() - started) / 1000) };
}

async function note(entry) {
  if (!eventsPath) return;
  let rows = [];
  try { rows = JSON.parse(await readFile(eventsPath, 'utf8')); } catch {}
  rows.push(entry);
  await writeFile(eventsPath, JSON.stringify(rows, null, 1) + '\n');
}

async function watchedStage() {
  if (!watchPath) return null;
  try {
    const info = await stat(watchPath);
    const report = JSON.parse(await readFile(watchPath, 'utf8'));
    return { stage: report.stage || '', age: (Date.now() - info.mtimeMs) / 1000 };
  } catch {
    return null;
  }
}

await acquire();
process.on('SIGINT', async () => { await release(); process.exit(130); });
process.on('SIGTERM', async () => { await release(); process.exit(143); });

const resultPath = join(tmpdir(), `kit-fusion-${randomUUID()}.py.json`);
let dispatchPath = null;
let outcome = { label, status: 'unknown', time: new Date().toISOString() };
try {
  if (!fusionPids().length || !(await targets()).some(value => value.title === 'Fusion Home Tab (HomeTab)')) {
    outcome.preflight = await restartFusion('bridge unavailable before run');
  }
  dispatchPath = await dispatch(scriptPath, resultPath);
  const started = Date.now();
  for (;;) {
    try {
      const result = JSON.parse(await readFile(resultPath, 'utf8'));
      outcome.status = result.status;
      if (result.traceback) outcome.traceback = result.traceback.split('\n').slice(-4).join('\n');
      break;
    } catch (error) {
      if (error.code !== 'ENOENT' && !(error instanceof SyntaxError)) throw error;
    }
    const watched = await watchedStage();
    const opening = watched && watched.stage.includes(stageText);
    const text = opening && watched.age > 5 ? dialogText() : null;
    if (text || (opening && watched.age > stallSeconds)) {
      outcome.status = text ? 'dialog' : 'stalled';
      outcome.stage = watched.stage;
      outcome.age = Math.round(watched.age);
      outcome.dialog = text;
      if (!text) outcome.windows = windowTitles();
      outcome.restart = await restartFusion(outcome.status);
      break;
    }
    if (!fusionPids().length) {
      outcome.status = 'fusion exited';
      outcome.stage = watched ? watched.stage : null;
      outcome.restart = await restartFusion('fusion exited');
      break;
    }
    if (Date.now() - started > waitSeconds * 1000) {
      outcome.status = 'timeout';
      outcome.stage = watched ? watched.stage : null;
      outcome.restart = await restartFusion('timeout');
      break;
    }
    await delay(1000);
  }
} catch (error) {
  outcome.status = 'error';
  outcome.error = String(error);
} finally {
  outcome.finished = new Date().toISOString();
  await note(outcome);
  if (dispatchPath) await unlink(dispatchPath).catch(() => {});
  await unlink(resultPath).catch(() => {});
  await release();
  console.log(JSON.stringify(outcome));
  if (outcome.status !== 'completed') process.exitCode = 1;
}
