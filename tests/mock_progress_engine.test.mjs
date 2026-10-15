import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const enginePath = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "exitwise-output",
  "mock-progress-engine.js",
);

const {
  MockProgressEngine,
  totalMockDurationMs,
  computeMockProgressState,
  MOCK_ANALYSIS_STAGES,
  WAITING_MESSAGE,
} = require(enginePath);

test("mock timeline completes near 95% in 8–12 seconds", () => {
  const total = totalMockDurationMs();
  assert.ok(total >= 8000 && total <= 12000, `expected 8–12s, got ${total}ms`);
  const atEnd = computeMockProgressState(total);
  assert.equal(atEnd.percent, 95);
  assert.equal(atEnd.stageIndex, 8);
  assert.equal(atEnd.atCap, true);
});

test("progress increases monotonically over time", () => {
  let last = -1;
  for (let t = 0; t <= totalMockDurationMs(); t += 200) {
    const p = computeMockProgressState(t).percent;
    assert.ok(p >= last, `percent regressed at t=${t}`);
    last = p;
  }
});

test("engine reaches cap and invokes onCapReached once", () => {
  let capCalls = 0;
  let lastPercent = 0;
  const now = { t: 0 };
  const engine = new MockProgressEngine({
    now: () => now.t,
    schedule: (cb) => setTimeout(cb, 0),
    cancel: clearTimeout,
    onUpdate: (s) => {
      lastPercent = s.percent;
    },
    onCapReached: () => {
      capCalls += 1;
    },
  });

  engine.start();
  now.t = totalMockDurationMs() + 50;
  return new Promise((resolve) => {
    setTimeout(() => {
      engine.stop();
      assert.equal(capCalls, 1);
      assert.ok(lastPercent >= 95);
      resolve();
    }, 30);
  });
});

test("finishTo100 runs completion callback", () => {
  let completed = false;
  const now = { t: 0 };
  const engine = new MockProgressEngine({
    now: () => now.t,
    schedule: (cb) => setTimeout(() => cb(now.t), 0),
    cancel: clearTimeout,
    finishDurationMs: 20,
    onComplete100: () => {
      completed = true;
    },
  });

  engine.start();
  now.t = totalMockDurationMs();
  engine.finishTo100();
  return new Promise((resolve) => {
    setTimeout(() => {
      assert.equal(completed, true);
      assert.equal(engine.isRunning(), false);
      resolve();
    }, 100);
  });
});

test("stop clears running state (timer cleanup)", () => {
  let updates = 0;
  const engine = new MockProgressEngine({
    schedule: (cb) => setTimeout(cb, 5),
    cancel: clearTimeout,
    onUpdate: () => {
      updates += 1;
    },
  });
  engine.start();
  engine.stop();
  return new Promise((resolve) => {
    setTimeout(() => {
      assert.equal(engine.isRunning(), false);
      resolve();
    }, 40);
  });
});

test("waiting message constant is defined", () => {
  assert.match(WAITING_MESSAGE, /longer than expected/i);
  assert.equal(MOCK_ANALYSIS_STAGES.length, 8);
});
