/* Tests for planProgress() in docs/javascripts/progress.js.
 *
 * Run:  node scripts/test_progress.js
 *
 * The function decides two things the front page gets wrong easily: where the
 * 接着读 button points, and whether the course counts as finished. Those are
 * separate questions -- "nothing unmarked after the lesson I last opened" is
 * not the same as "every lesson is marked" -- and an earlier version answered
 * the second with the first, so a reader who marked only the last lesson was
 * told 27 课全部标记完成.
 *
 * No DOM, no localStorage, no test framework: the function is pure, so plain
 * asserts are enough and this runs anywhere Node does.
 */

"use strict";

const assert = require("node:assert");
const path = require("node:path");

const { planProgress } = require(path.join(__dirname, "..", "docs", "javascripts", "progress.js"));

const ORDER = ["setup", "how-llms-work", "model-api", "prompt", "embeddings"];
const LAST = ORDER[ORDER.length - 1];

let failed = 0;
function test(name, fn) {
  try {
    fn();
    console.log(`  ok    ${name}`);
  } catch (e) {
    failed++;
    console.log(`  FAIL  ${name}\n        ${e.message}`);
  }
}

test("a new reader has nothing to resume and is not finished", () => {
  const p = planProgress(ORDER, [], null);
  assert.strictEqual(p.resume, null);
  assert.strictEqual(p.allDone, false);
  assert.strictEqual(p.doneCount, 0);
  assert.strictEqual(p.total, 5);
});

test("the lesson last opened but not marked is where we resume", () => {
  const p = planProgress(ORDER, ["setup"], "how-llms-work");
  assert.strictEqual(p.resume, "how-llms-work");
  assert.strictEqual(p.allDone, false);
});

test("a marked anchor moves on to the next unmarked lesson", () => {
  const p = planProgress(ORDER, ["setup", "how-llms-work"], "how-llms-work");
  assert.strictEqual(p.resume, "model-api");
});

test("marking only the last lesson is not finishing the course", () => {
  // The regression: firstUndone past the anchor returns nothing, and the old
  // code read that as "all done".
  const p = planProgress(ORDER, [LAST], LAST);
  assert.strictEqual(p.allDone, false, "four lessons are still unmarked");
  assert.strictEqual(p.resume, "setup", "resume wraps back to the first gap");
  assert.strictEqual(p.doneCount, 1);
});

test("a gap earlier in the course is found when the tail is all marked", () => {
  const done = ["setup", "model-api", "prompt", "embeddings"];   // how-llms-work missing
  const p = planProgress(ORDER, done, "embeddings");
  assert.strictEqual(p.resume, "how-llms-work");
  assert.strictEqual(p.allDone, false);
  assert.strictEqual(p.doneCount, 4);
});

test("every lesson marked is finished, with nothing to resume", () => {
  const p = planProgress(ORDER, ORDER.slice(), "prompt");
  assert.strictEqual(p.allDone, true);
  assert.strictEqual(p.resume, null);
  assert.strictEqual(p.doneCount, 5);
});

test("marks without a visit on record resume at the first gap", () => {
  const p = planProgress(ORDER, ["setup", "how-llms-work"], null);
  assert.strictEqual(p.resume, "model-api");
});

test("marks for lessons no longer listed do not count towards done", () => {
  const p = planProgress(ORDER, ["setup", "a-lesson-that-was-renamed"], null);
  assert.strictEqual(p.doneCount, 1);
  assert.strictEqual(p.allDone, false);
  assert.strictEqual(p.resume, "how-llms-work");
});

test("an anchor that is the only mark still reports the right count", () => {
  const p = planProgress(ORDER, ["prompt"], "prompt");
  assert.strictEqual(p.doneCount, 1);
  assert.strictEqual(p.resume, "embeddings");
});

test("an empty course is not a finished course", () => {
  const p = planProgress([], [], null);
  assert.strictEqual(p.allDone, false);
  assert.strictEqual(p.resume, null);
  assert.strictEqual(p.total, 0);
});

console.log(failed ? `\n${failed} failing` : "\nall passing");
process.exit(failed ? 1 : 0);
