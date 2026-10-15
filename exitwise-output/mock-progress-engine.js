/**
 * Smooth mock analysis progress engine for the Exitwise dashboard.
 * Browser: attaches to globalThis.MockProgressEngine. Node: module.exports.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.MockProgressEngine = api.MockProgressEngine;
    root.MOCK_ANALYSIS_STAGES = api.MOCK_ANALYSIS_STAGES;
    root.totalMockDurationMs = api.totalMockDurationMs;
    root.computeMockProgressState = api.computeMockProgressState;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const MOCK_ANALYSIS_STAGES = [
    {
      index: 1,
      name: "Validating repository",
      message: "Validating repository URL...",
      durationMs: 1000,
    },
    {
      index: 2,
      name: "Retrieving repository",
      message: "Retrieving repository metadata...",
      durationMs: 1000,
    },
    {
      index: 3,
      name: "Detecting manifests",
      message: "Detecting dependency manifests...",
      durationMs: 1000,
    },
    {
      index: 4,
      name: "Inspecting dependencies",
      message: "Inspecting package dependencies...",
      durationMs: 1500,
    },
    {
      index: 5,
      name: "Gathering risk evidence",
      message: "Gathering dependency risk evidence...",
      durationMs: 1500,
    },
    {
      index: 6,
      name: "Mapping dependency usage",
      message: "Mapping imports and usage references...",
      durationMs: 2000,
    },
    {
      index: 7,
      name: "Evaluating replacements",
      message: "Evaluating replacement candidates...",
      durationMs: 2000,
    },
    {
      index: 8,
      name: "Preparing Exit Capsules",
      message: "Preparing dependency Exit Capsules...",
      durationMs: 1000,
    },
  ];

  const WAITING_MESSAGE =
    "Analysis is taking longer than expected. Finalizing results...";

  function totalMockDurationMs(stages = MOCK_ANALYSIS_STAGES) {
    return stages.reduce((sum, s) => sum + s.durationMs, 0);
  }

  function buildTimeline(stages, maxPercent) {
    const total = totalMockDurationMs(stages);
    let elapsedCap = 0;
    return stages.map((stage) => {
      const startMs = elapsedCap;
      elapsedCap += stage.durationMs;
      const endPercent = Math.round((elapsedCap / total) * maxPercent);
      const startPercent =
        startMs === 0 ? 0 : Math.round((startMs / total) * maxPercent);
      return { ...stage, startMs, endMs: elapsedCap, startPercent, endPercent };
    });
  }

  function easeInOut(t) {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  /**
   * Pure function: elapsed ms -> visual progress state (for tests and rAF loop).
   */
  function computeMockProgressState(elapsedMs, options = {}) {
    const stages = options.stages || MOCK_ANALYSIS_STAGES;
    const maxPercent = options.maxPercent ?? 95;
    const timeline = buildTimeline(stages, maxPercent);
    const total = totalMockDurationMs(stages);

    if (elapsedMs >= total) {
      const last = timeline[timeline.length - 1];
      return {
        stageIndex: last.index,
        stageName: last.name,
        message: last.message,
        percent: maxPercent,
        totalStages: stages.length,
        atCap: true,
        waitingMessage: WAITING_MESSAGE,
      };
    }

    let current = timeline[0];
    for (const row of timeline) {
      if (elapsedMs < row.endMs) {
        current = row;
        break;
      }
    }

    const localT = (elapsedMs - current.startMs) / current.durationMs;
    const eased = easeInOut(Math.min(1, Math.max(0, localT)));
    const span = current.endPercent - current.startPercent;
    const percent = Math.min(
      maxPercent,
      Math.round(current.startPercent + eased * span),
    );

    return {
      stageIndex: current.index,
      stageName: current.name,
      message: current.message,
      percent,
      totalStages: stages.length,
      atCap: false,
      waitingMessage: WAITING_MESSAGE,
    };
  }

  class MockProgressEngine {
    constructor(options = {}) {
      this.stages = options.stages || MOCK_ANALYSIS_STAGES;
      this.maxPercent = options.maxPercent ?? 95;
      this.onUpdate = options.onUpdate || (() => {});
      this.onCapReached = options.onCapReached || (() => {});
      this.onComplete100 = options.onComplete100 || (() => {});
      this.reducedMotion = Boolean(options.reducedMotion);
      this._schedule =
        typeof options.schedule === "function"
          ? options.schedule
          : (cb) =>
              typeof requestAnimationFrame === "function"
                ? requestAnimationFrame(cb)
                : setTimeout(() => cb(Date.now()), 16);
      this._cancel =
        typeof options.cancel === "function"
          ? options.cancel
          : (id) => {
              if (typeof cancelAnimationFrame === "function") {
                cancelAnimationFrame(id);
              } else {
                clearTimeout(id);
              }
            };
      this._now =
        typeof options.now === "function"
          ? options.now
          : () =>
              typeof performance !== "undefined" && performance.now
                ? performance.now()
                : Date.now();

      this._running = false;
      this._generation = 0;
      this._frameId = null;
      this._startTs = 0;
      this._capReached = false;
      this._finishing = false;
      this._finishFrom = 0;
      this._finishStartTs = 0;
      this._finishDurationMs = options.finishDurationMs ?? 450;
    }

    start() {
      this.stop(false);
      this._running = true;
      this._generation += 1;
      const gen = this._generation;
      this._startTs = this._now();
      this._capReached = false;
      this._finishing = false;

      if (this.reducedMotion) {
        this._runReducedMotion(gen);
        return;
      }

      const tick = () => {
        if (!this._running || gen !== this._generation) return;

        if (this._finishing) {
          const t = Math.min(
            1,
            (this._now() - this._finishStartTs) / this._finishDurationMs,
          );
          const percent = Math.round(
            this._finishFrom + (100 - this._finishFrom) * easeInOut(t),
          );
          this.onUpdate({
            ...computeMockProgressState(totalMockDurationMs(this.stages), {
              stages: this.stages,
              maxPercent: this.maxPercent,
            }),
            percent,
            message: "Analysis complete.",
            atCap: false,
          });
          if (t >= 1) {
            this.stop(false);
            this.onComplete100({ percent: 100 });
            return;
          }
          this._frameId = this._schedule(tick);
          return;
        }

        const elapsed = this._now() - this._startTs;
        const state = computeMockProgressState(elapsed, {
          stages: this.stages,
          maxPercent: this.maxPercent,
        });
        this.onUpdate(state);

        if (state.atCap && !this._capReached) {
          this._capReached = true;
          this.onCapReached(state);
        }

        if (this._finishing || !state.atCap) {
          this._frameId = this._schedule(tick);
        }
      };

      this._frameId = this._schedule(tick);
    }

    _runReducedMotion(gen) {
      let i = 0;
      const runStage = () => {
        if (!this._running || gen !== this._generation) return;
        const stage = this.stages[i];
        if (!stage) {
          const cap = computeMockProgressState(totalMockDurationMs(this.stages), {
            stages: this.stages,
            maxPercent: this.maxPercent,
          });
          this.onUpdate(cap);
          if (!this._capReached) {
            this._capReached = true;
            this.onCapReached(cap);
          }
          return;
        }
        const elapsed = this.stages.slice(0, i + 1).reduce((s, x) => s + x.durationMs, 0);
        const state = computeMockProgressState(elapsed - 1, {
          stages: this.stages,
          maxPercent: this.maxPercent,
        });
        this.onUpdate({
          ...state,
          stageIndex: stage.index,
          stageName: stage.name,
          message: stage.message,
        });
        i += 1;
        setTimeout(runStage, stage.durationMs);
      };
      runStage();
    }

    /** Smoothly animate displayed progress to 100% (real backend success or demo finish). */
    finishTo100() {
      if (!this._running) return;
      this._finishing = true;
      this._finishStartTs = this._now();
      const elapsed = this._now() - this._startTs;
      const state = computeMockProgressState(elapsed, {
        stages: this.stages,
        maxPercent: this.maxPercent,
      });
      this._finishFrom = Math.min(99, state.percent);
    }

    stop(resetGeneration = true) {
      this._running = false;
      if (resetGeneration) this._generation += 1;
      if (this._frameId != null) {
        this._cancel(this._frameId);
        this._frameId = null;
      }
      this._finishing = false;
      this._capReached = false;
    }

    isRunning() {
      return this._running;
    }
  }

  return {
    MockProgressEngine,
    MOCK_ANALYSIS_STAGES,
    totalMockDurationMs,
    computeMockProgressState,
    WAITING_MESSAGE,
  };
});
