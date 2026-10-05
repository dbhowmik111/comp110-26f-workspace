/** Pure list building for the keyboard studio: no DOM and no audio. */
export const REST = -1;
export const HOLD = -2;
export const KICK = 36;
export const SNARE = 38;
export const HAT = 42;
export const MAX_STEPS = 1024;
export const MAX_SECONDS = 120;
const DRUM_NAMES = { 36: "KICK", 38: "SNARE", 42: "HAT" };

export function pitchName(pitch) {
  const names = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];
  return `${names[pitch % 12]}${Math.floor(pitch / 12) - 1}`;
}

export function stepLabel(value, voice) {
  if (value === REST) return "REST";
  if (value === HOLD) return "HOLD";
  return voice === "drums" ? DRUM_NAMES[value] : pitchName(value);
}

export function hasSound(steps) {
  return steps.some((value) => value !== REST);
}

/** The longest list the player accepts at this tempo: 1024 steps and 120 seconds. */
export function maxSteps(bpm, stepsPerBeat) {
  return Math.min(MAX_STEPS, Math.floor((MAX_SECONDS * bpm * stepsPerBeat) / 60));
}

/** Mirror the Python compiler so studio previews sound exactly like run(). */
export function compileEvents(steps, voice) {
  const events = [];
  let active = false;
  steps.forEach((value, index) => {
    if (voice === "drums") {
      if (value !== REST) events.push({ pitch: value, start_step: index, duration_steps: 1 });
      return;
    }
    if (value === REST) active = false;
    else if (value === HOLD) {
      if (active) events[events.length - 1].duration_steps += 1;
    } else {
      events.push({ pitch: value, start_step: index, duration_steps: 1 });
      active = true;
    }
  });
  return events;
}

export function formatValue(value, voice) {
  if (value === REST) return "REST";
  if (value === HOLD) return "HOLD";
  return voice === "drums" ? DRUM_NAMES[value] : String(value);
}

export const LINE_LENGTH = 88;

/**
 * One bar per line once a list is too long for a single line; half or quarter bars when a whole
 * bar would pass the formatter's default 88 characters, so line starts always fall on the beat.
 */
export function formatList(variable, steps, voice, stepsPerBar, indent = "") {
  const values = steps.map((value) => formatValue(value, voice));
  const head = `${indent}${variable}: list[int] = [`;
  const oneLine = `${head}${values.join(", ")}]`;
  if (oneLine.length <= LINE_LENGTH) return oneLine;
  const rows = (size) => {
    const lines = [];
    for (let index = 0; index < values.length; index += size) {
      lines.push(`${indent}    ${values.slice(index, index + size).join(", ")},`);
    }
    return lines;
  };
  let size = stepsPerBar;
  while (size > 1 && rows(size).some((line) => line.length > LINE_LENGTH)) size = Math.ceil(size / 2);
  return [head, ...rows(size), `${indent}]`].join("\n");
}

/**
 * Turn any HOLD that no longer continues a note into REST, as run() would reject it.
 * Editing a step in the middle of a list can orphan the HOLDs after it. Returns how many changed.
 */
export function repairHolds(steps) {
  let active = false;
  let repaired = 0;
  steps.forEach((value, index) => {
    if (value === HOLD && !active) {
      steps[index] = REST;
      repaired += 1;
    } else {
      active = value !== REST;
    }
  });
  return repaired;
}

/** HOLD is valid only right after a note or another HOLD. */
export function canHold(steps, index) {
  return index > 0 && steps[index - 1] !== REST;
}

/** Remove one index, like list.pop(index); later steps shift left. Returns repaired HOLDs. */
export function deleteStep(steps, index) {
  steps.splice(index, 1);
  return repairHolds(steps);
}

/** Change a note's pitch in place; HOLD and REST have no pitch to change. */
export function transposeStep(steps, index, semitones) {
  const value = steps[index];
  if (value === undefined || value < 0) return null;
  const pitch = Math.min(127, Math.max(0, value + semitones));
  steps[index] = pitch;
  return pitch;
}

/** Drum lanes share one index cursor, so pad the shorter ones with trailing REST. */
export function padLanes(lanes) {
  const length = Math.max(0, ...lanes.map((steps) => steps.length));
  return lanes.map((steps) => [...steps, ...new Array(length - steps.length).fill(REST)]);
}

/**
 * Overdub a drum take: drums played in the take replace their lists, and every drum left
 * untouched keeps its earlier recording. Record hat, then kick, then snare, one at a time.
 */
export function mergeDrumTake(existing, recorded, touched) {
  return padLanes(existing.map((steps, lane) => (touched.has(lane) ? recorded[lane] : steps.slice())));
}

/**
 * Snap live key presses to the nearest list index.
 * Pitched takes are monophonic like one Python list: a new note ends the previous one.
 * Drum takes write each hit into its own lane, so simultaneous hits never collide.
 */
export class Take {
  constructor({ laneCount, length, fixed, start, secondsPerStep, stepsPerBar }) {
    this.lanes = Array.from({ length: laneCount }, () => new Array(length).fill(REST));
    this.length = length;
    this.fixed = fixed;
    this.start = start;
    this.secondsPerStep = secondsPerStep;
    this.stepsPerBar = stepsPerBar;
    this.current = null;
    this.lastIndex = -1;
    this.touched = new Set();
  }

  step(time) {
    return Math.round((time - this.start) / this.secondsPerStep);
  }

  inRange(index) {
    return index >= 0 && index < this.length;
  }

  write(lane, index, value) {
    this.lanes[lane][index] = value;
    this.touched.add(lane);
    this.lastIndex = Math.max(this.lastIndex, index);
  }

  endNote(end) {
    const stop = Math.min(end, this.length);
    for (let index = this.current.start + 1; index < stop; index += 1) this.write(0, index, HOLD);
    this.current = null;
  }

  /** Returns the written index, or -1 when the press falls outside the take. */
  noteOn(key, pitch, time) {
    const index = this.step(time);
    if (!this.inRange(index)) return -1;
    if (this.current) this.endNote(index);
    this.write(0, index, pitch);
    this.current = { key, start: index };
    return index;
  }

  noteOff(key, time) {
    if (this.current?.key !== key) return;
    this.endNote(Math.max(this.current.start + 1, this.step(time)));
  }

  hit(lane, value, time) {
    const index = this.step(time);
    if (!this.inRange(index)) return -1;
    this.write(lane, index, value);
    return index;
  }

  elapsedSteps(time) {
    return Math.ceil((time - this.start) / this.secondsPerStep);
  }

  /** Close any held note and trim a free take to whole bars; null means nothing was played. */
  finish(time) {
    if (this.current) this.endNote(Math.max(this.current.start + 1, this.step(time)));
    if (this.lastIndex < 0) return null;
    let length = this.length;
    if (!this.fixed) {
      const played = Math.max(this.elapsedSteps(time), this.lastIndex + 1);
      length = Math.min(this.length, Math.ceil(played / this.stepsPerBar) * this.stepsPerBar);
    }
    return this.lanes.map((lane) => lane.slice(0, length));
  }
}
