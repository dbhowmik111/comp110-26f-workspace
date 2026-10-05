import { DEFAULT_MASTER_VOLUME, TRACK_GAIN, VOICE_PEAK_GAIN, frequency, renderDrum, renderTrack, stepSeconds } from "./audio.js";
import {
  HAT, HOLD, KICK, REST, SNARE, Take, canHold, compileEvents, deleteStep, formatList, hasSound, maxSteps,
  mergeDrumTake, padLanes, pitchName, repairHolds, stepLabel, transposeStep,
} from "./studio-lists.js";

const STORAGE_KEY = "daftcomp-studio-v1";
const HISTORY_LIMIT = 200;
const BEATS_PER_BAR = 4;
// Physical key positions, so the layout is the same on QWERTY, AZERTY, and QWERTZ keyboards.
export const PIANO_KEYS = [
  ["KeyA", 0, "A"], ["KeyW", 1, "W"], ["KeyS", 2, "S"], ["KeyE", 3, "E"], ["KeyD", 4, "D"], ["KeyF", 5, "F"],
  ["KeyT", 6, "T"], ["KeyG", 7, "G"], ["KeyY", 8, "Y"], ["KeyH", 9, "H"], ["KeyU", 10, "U"], ["KeyJ", 11, "J"],
  ["KeyK", 12, "K"], ["KeyO", 13, "O"], ["KeyL", 14, "L"], ["KeyP", 15, "P"], ["Semicolon", 16, ";"], ["Quote", 17, "'"],
];
export const DRUM_PADS = [
  { value: KICK, name: "Kick", keys: ["KeyA", "KeyJ"], labels: "A / J" },
  { value: SNARE, name: "Snare", keys: ["KeyS", "KeyK"], labels: "S / K" },
  { value: HAT, name: "Hat", keys: ["KeyD", "KeyL"], labels: "D / L" },
];
// The pitched voices the player already renders; melody and harmony can switch between them.
const VOICES = [["pulse", "Pulse"], ["triangle", "Triangle"]];
const PIANO_OFFSETS = new Map(PIANO_KEYS.map(([code, offset]) => [code, offset]));
const DRUM_CODES = new Map(DRUM_PADS.flatMap((pad) => pad.keys.map((code) => [code, pad.value])));

function newParts() {
  return [
    // cursor is the selected index; null follows the end of the list, where new steps are added.
    { id: "melody", name: "Melody", voice: "pulse", voices: VOICES, base: 60, cursor: null, lanes: [{ name: "Melody", variable: "melody", steps: [] }] },
    { id: "harmony", name: "Harmony", voice: "pulse", voices: VOICES, base: 60, cursor: null, lanes: [{ name: "Harmony", variable: "harmony", steps: [] }] },
    { id: "bass", name: "Bass", voice: "triangle", base: 48, cursor: null, lanes: [{ name: "Bass", variable: "bass", steps: [] }] },
    {
      id: "drums", name: "Drums", voice: "drums", base: 0, cursor: null,
      lanes: DRUM_PADS.map((pad) => ({ name: pad.name, variable: pad.name.toLowerCase(), hit: pad.value, steps: [] })),
    },
  ];
}

const state = {
  mode: "step",
  bpm: 120,
  stepsPerBeat: 2,
  takeBars: 4,
  click: true,
  masterVolume: DEFAULT_MASTER_VOLUME,
  parts: newParts(),
  active: 0,
};
const history = new Map(state.parts.map((part) => [part.id, []]));

const $ = (selector) => document.querySelector(selector);
let audio = null;
let sounding = null;
const heldDrumKeys = new Set();
const pendingDrums = new Set();
const pressedCodes = new Set();
let transport = null;
let take = null;
let drumSeed = 1;
let laneCells = [];
let highlighted = -1;

// ---------- persistence ----------

function save() {
  try {
    const parts = Object.fromEntries(state.parts.map((part) => [part.id, { base: part.base, voice: part.voice, lanes: part.lanes.map((lane) => lane.steps) }]));
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      mode: state.mode, bpm: state.bpm, stepsPerBeat: state.stepsPerBeat, takeBars: state.takeBars,
      click: state.click, active: state.active, parts,
    }));
  } catch {
    // Storage can be unavailable in private windows; the studio still works for this visit.
  }
}

function validSteps(steps, voice) {
  if (!Array.isArray(steps) || steps.length > maxSteps(300, 4)) return false;
  let active = false;
  return steps.every((value) => {
    if (!Number.isInteger(value)) return false;
    if (voice === "drums") return [KICK, SNARE, HAT, REST].includes(value);
    if (value === HOLD) return active;
    active = value !== REST;
    return value === REST || (value >= 0 && value <= 127);
  });
}

function restore() {
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "null");
  } catch {
    return;
  }
  if (!saved || typeof saved !== "object") return;
  if (["step", "live"].includes(saved.mode)) state.mode = saved.mode;
  if (Number.isInteger(saved.bpm) && saved.bpm >= 30 && saved.bpm <= 300) state.bpm = saved.bpm;
  if ([1, 2, 4].includes(saved.stepsPerBeat)) state.stepsPerBeat = saved.stepsPerBeat;
  if ([0, 1, 2, 4, 8, 16].includes(saved.takeBars)) state.takeBars = saved.takeBars;
  if (typeof saved.click === "boolean") state.click = saved.click;
  if (Number.isInteger(saved.active) && saved.active >= 0 && saved.active < state.parts.length) state.active = saved.active;
  for (const part of state.parts) {
    const stored = saved.parts?.[part.id];
    if (!stored) continue;
    if (Number.isInteger(stored.base) && stored.base >= 12 && stored.base <= 108) part.base = stored.base;
    if (part.voices?.some(([voice]) => voice === stored.voice)) part.voice = stored.voice;
    if (Array.isArray(stored.lanes) && stored.lanes.length === part.lanes.length && stored.lanes.every((steps) => validSteps(steps, part.voice))) {
      const lanes = part.voice === "drums" ? padLanes(stored.lanes) : stored.lanes;
      part.lanes.forEach((lane, index) => { lane.steps = lanes[index].slice(); });
    }
  }
}

// ---------- audio ----------

function ensureAudio() {
  if (!audio) {
    const context = new AudioContext({ latencyHint: "interactive" });
    const master = context.createGain();
    master.gain.value = state.masterVolume;
    master.connect(context.destination);
    const live = context.createGain();
    live.gain.value = TRACK_GAIN;
    live.connect(master);
    audio = { context, master, live };
  }
  void audio.context.resume().catch(() => {});
  return audio;
}

/**
 * The audio time reaching the speakers now. Students play along with what they hear, which
 * lags the audio clock by the output latency (often 100 ms or more on Bluetooth), so key
 * presses, the playhead, and the count-in all use this clock.
 */
function heardTime() {
  const { context } = audio;
  return context.currentTime - (context.outputLatency || 0) - (context.baseLatency || 0);
}

function startTone(pitch, voice) {
  const { context, live } = audio;
  const now = context.currentTime;
  const oscillator = context.createOscillator();
  oscillator.type = voice === "triangle" ? "triangle" : "square";
  oscillator.frequency.value = frequency(pitch);
  const gain = context.createGain();
  gain.gain.setValueAtTime(0, now);
  gain.gain.linearRampToValueAtTime(VOICE_PEAK_GAIN, now + 0.005);
  oscillator.connect(gain);
  gain.connect(live);
  oscillator.start(now);
  return { oscillator, gain };
}

function stopTone(tone) {
  const now = audio.context.currentTime;
  tone.gain.gain.cancelScheduledValues(now);
  tone.gain.gain.setValueAtTime(tone.gain.gain.value, now);
  tone.gain.gain.linearRampToValueAtTime(0, now + 0.01);
  tone.oscillator.stop(now + 0.02);
}

function playDrum(value) {
  const now = audio.context.currentTime;
  renderDrum(audio.context, { pitch: value, start_step: drumSeed++ }, now, now + 1, audio.live);
}

function click(time, accent) {
  const { context, master } = audio;
  const oscillator = context.createOscillator();
  oscillator.frequency.value = accent ? 1760 : 1175;
  const gain = context.createGain();
  gain.gain.setValueAtTime(0, time);
  gain.gain.linearRampToValueAtTime(accent ? 0.28 : 0.16, time + 0.002);
  gain.gain.exponentialRampToValueAtTime(0.0001, time + 0.05);
  oscillator.connect(gain);
  gain.connect(master);
  oscillator.start(time);
  oscillator.stop(time + 0.06);
}

function songTracks(skipPart = null) {
  const tracks = [];
  for (const part of state.parts) {
    if (part === skipPart) continue;
    for (const lane of part.lanes) {
      if (hasSound(lane.steps)) tracks.push({ name: lane.name, variable: lane.variable, voice: part.voice, steps: lane.steps });
    }
  }
  return tracks;
}

async function renderBuffers(tracks, songSteps) {
  const song = { bpm: state.bpm, steps_per_beat: state.stepsPerBeat, song_steps: songSteps };
  const buffers = [];
  for (const track of tracks) buffers.push(await renderTrack(song, { ...track, events: compileEvents(track.steps, track.voice) }));
  return buffers;
}

function startBuffers(buffers, start) {
  const { context, master } = audio;
  return buffers.map((buffer) => {
    const source = context.createBufferSource();
    const gain = context.createGain();
    gain.gain.value = TRACK_GAIN;
    source.buffer = buffer;
    source.connect(gain);
    gain.connect(master);
    source.start(start);
    // Kept so an overdub can silence the old recording of a drum once it is replayed.
    source.trackGain = gain;
    return source;
  });
}

// ---------- transport: play all and live takes ----------

function stopTransport() {
  if (!transport) return;
  transport.cancelled = true;
  clearInterval(transport.timer);
  cancelAnimationFrame(transport.frame);
  for (const source of transport.sources) {
    source.onended = null;
    try { source.stop(); } catch { /* not started yet */ }
    source.disconnect();
  }
  transport = null;
  setHighlight(-1);
  document.body.dataset.state = "idle";
  updateControls();
}

async function playAll() {
  finishTake(true);
  stopTransport();
  const tracks = songTracks();
  if (tracks.length === 0) {
    announce("Record something first, then Play all.");
    return;
  }
  ensureAudio();
  const own = { cancelled: false, sources: [], timer: 0, frame: 0, kind: "play" };
  transport = own;
  document.body.dataset.state = "rendering";
  updateControls();
  announce("Preparing playback…");
  const songSteps = Math.max(...tracks.map((track) => track.steps.length));
  const buffers = await renderBuffers(tracks, songSteps);
  if (own.cancelled) return;
  own.start = audio.context.currentTime + 0.05;
  own.sources = startBuffers(buffers, own.start);
  own.sources[0].onended = () => { if (transport === own) { stopTransport(); announce("Playback finished."); } };
  document.body.dataset.state = "playing";
  updateControls();
  announce(`Playing ${tracks.length} list${tracks.length === 1 ? "" : "s"} together.`);
  const secondsPerStep = stepSeconds(state.bpm, state.stepsPerBeat);
  const follow = () => {
    if (transport !== own) return;
    setHighlight(Math.floor((heardTime() - own.start) / secondsPerStep));
    own.frame = requestAnimationFrame(follow);
  };
  follow();
}

async function startTake() {
  if (take) return finishTake(true);
  stopTransport();
  releaseAll();
  ensureAudio();
  const part = activePart();
  const secondsPerStep = stepSeconds(state.bpm, state.stepsPerBeat);
  const stepsPerBar = state.stepsPerBeat * BEATS_PER_BAR;
  const limit = maxSteps(state.bpm, state.stepsPerBeat);
  const fixed = state.takeBars > 0;
  const length = fixed ? Math.min(limit, state.takeBars * stepsPerBar) : limit;
  const own = { cancelled: false, sources: [], timer: 0, frame: 0, kind: "take" };
  transport = own;
  document.body.dataset.state = "rendering";
  updateControls();
  announce("Preparing the other parts to play along…");
  // Drum takes overdub: the part's existing drums play along too, so hat, kick, and snare
  // can be recorded one at a time. Each drum's old version goes quiet once it is played again.
  const drums = part.voice === "drums";
  const others = songTracks(drums ? null : part);
  const buffers = others.length ? await renderBuffers(others, Math.max(...others.map((track) => track.steps.length))) : [];
  if (own.cancelled) return;
  const beat = secondsPerStep * state.stepsPerBeat;
  const start = audio.context.currentTime + 0.1 + beat * BEATS_PER_BAR;
  take = new Take({ laneCount: part.lanes.length, length, fixed, start, secondsPerStep, stepsPerBar });
  take.part = part;
  own.sources = startBuffers(buffers, start);
  own.drumGains = new Map();
  if (drums) {
    others.forEach((track, index) => {
      const lane = part.lanes.findIndex((candidate) => candidate.steps === track.steps);
      if (lane >= 0) own.drumGains.set(lane, own.sources[index].trackGain);
    });
  }
  let nextBeat = -BEATS_PER_BAR;
  const schedule = () => {
    const now = audio.context.currentTime;
    while (start + nextBeat * beat < now + 0.12) {
      if (nextBeat < 0 || state.click) click(start + nextBeat * beat, nextBeat % BEATS_PER_BAR === 0);
      nextBeat += 1;
    }
    if (heardTime() >= start + length * secondsPerStep) finishTake(true);
  };
  schedule();
  own.timer = setInterval(schedule, 25);
  document.body.dataset.state = "recording";
  updateControls();
  renderLanes();
  const follow = () => {
    if (transport !== own) return;
    const now = heardTime();
    if (now < start) {
      announce(`Count-in: ${Math.ceil((start - now) / beat)}…`);
    } else {
      const index = Math.floor((now - start) / secondsPerStep);
      const bar = Math.floor(index / stepsPerBar) + 1;
      const total = fixed ? ` of ${Math.ceil(length / stepsPerBar)}` : "";
      announce(`● Recording ${part.name} · bar ${bar}${total}. Press Enter to stop.`, false);
      setHighlight(index);
    }
    own.frame = requestAnimationFrame(follow);
  };
  follow();
}

/** Keep the take when commit is true; Escape discards it. */
function finishTake(commit) {
  if (!take) return;
  const current = take;
  take = null;
  const lanes = commit ? current.finish(heardTime()) : null;
  releaseAll();
  stopTransport();
  if (lanes) {
    const part = current.part;
    remember(part);
    if (part.voice === "drums") {
      const merged = mergeDrumTake(part.lanes.map((lane) => lane.steps), lanes, current.touched);
      part.lanes.forEach((lane, index) => { lane.steps = merged[index]; });
      const names = part.lanes.filter((_, index) => current.touched.has(index)).map((lane) => lane.name.toLowerCase());
      const kept = part.lanes.filter((lane, index) => !current.touched.has(index) && hasSound(lane.steps)).map((lane) => lane.name.toLowerCase());
      announce(`Recorded ${names.join(" and ")}${kept.length ? `; kept your ${kept.join(" and ")}` : ""}. Undo brings back the previous version.`);
    } else {
      part.lanes.forEach((lane, index) => { lane.steps = lanes[index]; });
      announce(`Saved a ${lanes[0].length}-step take for ${part.name}. Undo brings back the previous version.`);
    }
    part.cursor = null;
  } else {
    announce(commit ? "Nothing was played, so the take was not kept." : "Take cancelled; your list is unchanged.");
  }
  changed();
}

// ---------- editing ----------

function activePart() {
  return state.parts[state.active];
}

function remember(part) {
  const stack = history.get(part.id);
  stack.push(part.lanes.map((lane) => lane.steps.slice()));
  if (stack.length > HISTORY_LIMIT) stack.shift();
}

function undo() {
  if (take) return;
  const part = activePart();
  const previous = history.get(part.id).pop();
  if (!previous) return announce(`Nothing to undo for ${part.name}.`);
  part.lanes.forEach((lane, index) => { lane.steps = previous[index]; });
  announce(`Undid the last change to ${part.name}.`);
  changed();
}

function clearPart() {
  const part = activePart();
  if (take || part.lanes.every((lane) => lane.steps.length === 0)) return;
  remember(part);
  for (const lane of part.lanes) lane.steps = [];
  announce(`Cleared ${part.name}. Undo brings it back.`);
  changed();
}

function stepCount(part) {
  return part.lanes[0].steps.length;
}

/** The selected index; the list's length means the empty slot after the end. */
function cursorOf(part) {
  const length = stepCount(part);
  return part.cursor === null || part.cursor >= length ? length : Math.max(0, part.cursor);
}

function setCursor(part, index) {
  part.cursor = index >= stepCount(part) ? null : Math.max(0, index);
}

function repairNote(part) {
  if (part.voice === "drums") return "";
  const repaired = repairHolds(part.lanes[0].steps);
  return repaired ? ` ${repaired} HOLD step${repaired === 1 ? "" : "s"} after it no longer followed a note, so ${repaired === 1 ? "it became" : "they became"} REST.` : "";
}

/**
 * Write one step at the cursor: past the end it appends, like list.append(); on a selected
 * step it replaces that index, like melody[3] = 67. Either way the cursor moves on.
 */
function writeStep(values, message) {
  const part = activePart();
  const index = cursorOf(part);
  const length = stepCount(part);
  if (index === length) {
    const limit = maxSteps(state.bpm, state.stepsPerBeat);
    if (length >= limit) {
      showError(`${part.name} already has ${limit} steps, the longest list the player can play at this tempo.`);
      return false;
    }
    remember(part);
    part.lanes.forEach((lane, laneIndex) => lane.steps.push(values[laneIndex]));
    announce(`${message} → index ${index}`);
  } else {
    remember(part);
    part.lanes.forEach((lane, laneIndex) => { lane.steps[index] = values[laneIndex]; });
    setCursor(part, index + 1);
    announce(`${message} replaced index ${index}.${repairNote(part)}`);
  }
  changed();
  return true;
}

function addHold() {
  const part = activePart();
  if (part.voice === "drums") return showError("Drums can't HOLD. Press Space for a REST instead.");
  if (!canHold(part.lanes[0].steps, cursorOf(part))) return showError("HOLD continues a note, so the step before it must be a note or HOLD.");
  writeStep([HOLD], "HOLD");
}

function addRest() {
  writeStep(activePart().lanes.map(() => REST), "REST");
}

function removeStep() {
  const part = activePart();
  const length = stepCount(part);
  if (length === 0) return announce(`${part.name} is empty; there is nothing to delete.`);
  // At the end, delete the last step, like list.pop(); otherwise pop the selected index.
  const index = Math.min(cursorOf(part), length - 1);
  remember(part);
  const repaired = part.lanes.map((lane) => deleteStep(lane.steps, index)).reduce((total, count) => total + count, 0);
  if (cursorOf(part) > index) setCursor(part, index);
  const note = repaired ? ` ${repaired} HOLD step${repaired === 1 ? "" : "s"} no longer followed a note, so ${repaired === 1 ? "it became" : "they became"} REST.` : "";
  announce(`Deleted index ${index}; later steps moved left.${note}`);
  changed();
}

function commitDrumStep() {
  const part = activePart();
  if (pendingDrums.size === 0 || part.voice !== "drums") return;
  const index = cursorOf(part);
  const appending = index === stepCount(part);
  // On an existing step, each drum pressed toggles, so a hat can be added beside a kick.
  const values = part.lanes.map((lane) => {
    if (!pendingDrums.has(lane.hit)) return appending ? REST : lane.steps[index];
    return !appending && lane.steps[index] === lane.hit ? REST : lane.hit;
  });
  const names = part.lanes.filter((lane) => pendingDrums.has(lane.hit)).map((lane) => lane.name.toUpperCase());
  pendingDrums.clear();
  writeStep(values, names.join(" + "));
}

function audition(part, index) {
  const now = audio.context.currentTime;
  if (part.voice === "drums") {
    for (const lane of part.lanes) if (lane.steps[index] === lane.hit) playDrum(lane.hit);
    return;
  }
  const value = part.lanes[0].steps[index];
  if (value === undefined || value < 0) return;
  const tone = startTone(value, part.voice);
  tone.gain.gain.setValueAtTime(VOICE_PEAK_GAIN, now + 0.16);
  tone.gain.gain.linearRampToValueAtTime(0, now + 0.18);
  tone.oscillator.stop(now + 0.2);
}

function moveCursor(index) {
  const part = activePart();
  setCursor(part, Math.min(Math.max(0, index), stepCount(part)));
  ensureAudio();
  audition(part, cursorOf(part));
  hideError();
  renderLanes();
  renderStepDetail();
}

function transposeSelected(semitones) {
  const part = activePart();
  const index = cursorOf(part);
  if (part.voice === "drums" || index >= stepCount(part)) return false;
  const steps = part.lanes[0].steps;
  if (steps[index] < 0) return false;
  remember(part);
  const pitch = transposeStep(steps, index, semitones);
  ensureAudio();
  audition(part, index);
  announce(`${part.lanes[0].variable}[${index}] is now ${pitch} (${pitchName(pitch)}).`);
  changed();
  return true;
}

function setVoice(voice) {
  const part = activePart();
  if (!part.voices?.some(([name]) => name === voice) || voice === part.voice) return;
  releaseAll();
  part.voice = voice;
  renderInstrument();
  announce(`${part.name} now plays the ${voice} voice. Your list is unchanged; only add_track's voice changes.`);
  changed();
}

// ---------- keyboard ----------

const KEY_CODES = { " ": "Space", "-": "Minus", "_": "Minus", ";": "Semicolon", ":": "Semicolon", "'": "Quote", '"': "Quote" };

/** Some remote desktops and on-screen keyboards leave event.code empty; recover it from the key. */
export function keyCode(event) {
  if (event.code) return event.code;
  const { key } = event;
  if (/^[a-z]$/i.test(key)) return `Key${key.toUpperCase()}`;
  if (/^\d$/.test(key)) return `Digit${key}`;
  return KEY_CODES[key] ?? key;
}

function isTextField(target) {
  if (target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement) return true;
  return target instanceof HTMLInputElement && !["checkbox", "radio", "range", "button"].includes(target.type);
}

function pianoPitch(code) {
  const offset = PIANO_OFFSETS.get(code);
  if (offset === undefined) return null;
  const pitch = activePart().base + offset;
  return pitch <= 127 ? pitch : null;
}

function noteDown(code) {
  const part = activePart();
  if (part.voice === "drums") {
    const value = DRUM_CODES.get(code);
    if (value === undefined) return false;
    ensureAudio();
    playDrum(value);
    lightKey(code, true);
    if (take && take.part === part) {
      const lane = part.lanes.findIndex((candidate) => candidate.hit === value);
      const index = take.hit(lane, value, heardTime());
      if (index >= 0) {
        transport?.drumGains?.get(lane)?.gain.setTargetAtTime(0, audio.context.currentTime, 0.01);
        renderLanes();
      }
    } else if (state.mode === "step") {
      heldDrumKeys.add(code);
      pendingDrums.add(value);
    }
    return true;
  }
  const pitch = pianoPitch(code);
  if (pitch === null) return false;
  ensureAudio();
  if (sounding) {
    stopTone(sounding.tone);
    lightKey(sounding.code, false);
  }
  sounding = { code, tone: startTone(pitch, part.voice) };
  lightKey(code, true);
  if (take && take.part === part) {
    if (take.noteOn(code, pitch, heardTime()) >= 0) renderLanes();
  } else if (state.mode === "step") {
    writeStep([pitch], `${pitch} (${pitchName(pitch)})`);
  } else {
    announce(`${pitch} · ${pitchName(pitch)} — press Record to capture a take.`);
  }
  return true;
}

function noteUp(code) {
  lightKey(code, false);
  if (heldDrumKeys.delete(code) && heldDrumKeys.size === 0) commitDrumStep();
  if (sounding?.code === code) {
    stopTone(sounding.tone);
    sounding = null;
    if (take) {
      take.noteOff(code, heardTime());
      renderLanes();
    }
  }
}

function releaseAll() {
  for (const code of pressedCodes) noteUp(code);
  pressedCodes.clear();
  heldDrumKeys.clear();
  pendingDrums.clear();
}

function shiftOctave(direction) {
  const part = activePart();
  if (part.voice === "drums") return;
  const base = part.base + 12 * direction;
  if (base < 12 || base > 108) return announce("That's as far as the keyboard goes.");
  releaseAll();
  part.base = base;
  renderInstrument();
  announce(`${part.name} keyboard now starts at ${base} (${pitchName(base)}).`);
  save();
}

function selectPart(index) {
  if (index === state.active || index < 0 || index >= state.parts.length) return;
  if (take) finishTake(true);
  releaseAll();
  state.active = index;
  changed();
  renderInstrument();
  announce(`Now playing ${activePart().name}.`);
}

function onKeyDown(event) {
  if (isTextField(event.target)) return;
  if ((event.metaKey || event.ctrlKey) && keyCode(event) === "KeyZ" && !event.shiftKey) {
    event.preventDefault();
    undo();
    return;
  }
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const handled = handleKey(event);
  if (handled) event.preventDefault();
}

function handleKey(event) {
  const code = keyCode(event);
  if (event.repeat && !["ArrowLeft", "ArrowRight"].includes(code)) {
    return PIANO_OFFSETS.has(code) || DRUM_CODES.has(code) || ["Space", "Minus", "Backspace", "Delete"].includes(code);
  }
  if (/^Digit[1-4]$/.test(code)) {
    selectPart(Number(code.slice(5)) - 1);
    return true;
  }
  if (code === "KeyZ" || code === "KeyX") {
    shiftOctave(code === "KeyZ" ? -1 : 1);
    return true;
  }
  if (code === "Enter" && state.mode === "live") {
    void startTake();
    return true;
  }
  if (code === "Escape" && take) {
    finishTake(false);
    return true;
  }
  if (!take) {
    const part = activePart();
    if (code === "Space") { addRest(); return true; }
    if (code === "Minus") { addHold(); return true; }
    if (code === "Backspace" || code === "Delete") { removeStep(); return true; }
    if (code === "ArrowLeft") { moveCursor(cursorOf(part) - 1); return true; }
    if (code === "ArrowRight") { moveCursor(cursorOf(part) + 1); return true; }
    if (code === "Home") { moveCursor(0); return true; }
    if (code === "End") { moveCursor(stepCount(part)); return true; }
    if (code === "ArrowUp" || code === "ArrowDown") return transposeSelected((code === "ArrowUp" ? 1 : -1) * (event.shiftKey ? 12 : 1));
    if (code === "KeyV" && part.voices) {
      const names = part.voices.map(([name]) => name);
      setVoice(names[(names.indexOf(part.voice) + 1) % names.length]);
      return true;
    }
  }
  if (pressedCodes.has(code)) return true;
  if (noteDown(code)) {
    pressedCodes.add(code);
    return true;
  }
  return false;
}

function onKeyUp(event) {
  const code = keyCode(event);
  if (!pressedCodes.delete(code)) {
    // Stop Space from also clicking a focused button after it wrote a REST.
    if (code === "Space" && !isTextField(event.target)) event.preventDefault();
    return;
  }
  event.preventDefault();
  noteUp(code);
}

// ---------- rendering ----------

function announce(message, clearError = true) {
  $("#studio-status").textContent = message;
  if (clearError) hideError();
}

function showError(message) {
  const error = $("#studio-error");
  error.textContent = message;
  error.hidden = false;
}

function hideError() {
  $("#studio-error").hidden = true;
}

function lightKey(code, on) {
  document.querySelectorAll(`[data-code="${code}"], [data-alt="${code}"]`).forEach((key) => key.classList.toggle("is-down", on));
}

function renderInstrument() {
  const part = activePart();
  const drums = part.voice === "drums";
  $("#instrument-title").textContent = part.name;
  $("#voice-switch").hidden = !part.voices;
  $("#voice-switch").replaceChildren(...(part.voices ?? []).map(([voice, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(voice === part.voice));
    button.textContent = label;
    button.addEventListener("click", () => setVoice(voice));
    return button;
  }));
  $("#piano").hidden = drums;
  $("#pads").hidden = !drums;
  if (drums) {
    $("#instrument-detail").textContent = "Drums voice · each drum records into its own list, so hits can land on the same step.";
    $("#pads").replaceChildren(...DRUM_PADS.map((pad) => {
      const element = document.createElement("div");
      element.className = "pad";
      element.dataset.code = pad.keys[0];
      element.innerHTML = `<strong>${pad.name}</strong><span>${pad.name.toUpperCase()} = ${pad.value}</span><kbd>${pad.labels}</kbd>`;
      return element;
    }));
    // Both hands light the same pad.
    for (const pad of DRUM_PADS) $("#pads").querySelector(`[data-code="${pad.keys[0]}"]`).dataset.alt = pad.keys[1];
  } else {
    const voiceHelp = part.voices ? "V switches the instrument. " : `${part.voice === "triangle" ? "Triangle" : "Pulse"} voice · `;
    $("#instrument-detail").textContent = `${voiceHelp}Keys play ${part.base} (${pitchName(part.base)}) to ${part.base + 17} (${pitchName(part.base + 17)}). Z / X shift an octave.`;
    $("#piano").replaceChildren(...PIANO_KEYS.map(([code, offset, label]) => {
      const pitch = part.base + offset;
      const key = document.createElement("div");
      key.className = [1, 3, 6, 8, 10].includes(offset % 12) ? "key black" : "key white";
      key.dataset.code = code;
      key.innerHTML = `<kbd>${label}</kbd><span>${pitch}</span><small>${pitchName(pitch)}</small>`;
      return key;
    }));
  }
  const keys = drums
    ? "A / J kick · S / K snare · D / L hat."
    : "Play A W S E D F T G Y H U J K O L P ; ' like a piano.";
  const extra = state.mode === "step"
    ? (drums
      ? "Drums pressed together share one step; on a selected step, each drum toggles on or off."
      : "Each note fills the selected index, then moves on.")
    : (drums
      ? "Enter records after a one-bar count-in. Record one drum at a time: drums you don't play keep their earlier recording."
      : "Enter records after a one-bar count-in; Enter again stops, Esc cancels. Notes snap to the nearest step.");
  const editing = "← → select a step" + (drums ? "" : ", ↑ ↓ change its pitch (Shift for an octave)") + "; Space sets REST" + (drums ? "" : ", - sets HOLD") + ", Backspace deletes.";
  $("#key-help").textContent = `${keys} ${extra} ${editing} 1–4 choose a part; ⌘/Ctrl+Z undoes.`;
}

function renderParts() {
  $("#parts").replaceChildren(...state.parts.map((part, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("role", "radio");
    button.className = "part-tab";
    button.setAttribute("aria-checked", String(index === state.active));
    const length = part.lanes[0].steps.length;
    button.innerHTML = `<kbd>${index + 1}</kbd> <strong>${part.name}</strong> <span>${part.voice} · ${length} step${length === 1 ? "" : "s"}</span>`;
    button.dataset.part = part.id;
    button.addEventListener("click", () => selectPart(index));
    return button;
  }));
}

function renderLanes() {
  const stepsPerBar = state.stepsPerBeat * BEATS_PER_BAR;
  laneCells = [];
  const groups = state.parts.map((part, partIndex) => {
    const group = document.createElement("div");
    const active = partIndex === state.active;
    group.className = `lane-group${active ? " is-active" : ""}`;
    group.dataset.part = part.id;
    const recording = take && take.part === part;
    const selected = active && !recording ? cursorOf(part) : -1;
    part.lanes.forEach((lane, laneIndex) => {
      // In a drum overdub, drums not yet played show the recording they will keep.
      const replaced = recording && (part.voice !== "drums" || take.touched.has(laneIndex));
      const steps = replaced ? take.lanes[laneIndex] : lane.steps;
      const row = document.createElement("div");
      row.className = "lane";
      const label = document.createElement("div");
      label.className = "lane-label";
      label.innerHTML = `<code>${lane.variable}</code><span>${recording ? (replaced ? "recording…" : "kept") : `len ${steps.length}`}</span>`;
      const cells = document.createElement("div");
      cells.className = "lane-cells";
      cells.setAttribute("aria-label", `${lane.variable}, ${steps.length} steps`);
      const views = steps.map((value, index) => {
        const cell = document.createElement("span");
        const kind = value === REST ? "rest" : value === HOLD ? "hold" : "note";
        cell.className = `cell ${kind}${index % stepsPerBar === 0 ? " bar-start" : ""}${index === selected ? " is-selected" : ""}`;
        cell.title = `${lane.variable}[${index}] = ${value} (${stepLabel(value, part.voice)})`;
        cell.dataset.index = String(index);
        const text = value === REST ? "·" : value === HOLD ? "—" : part.voice === "drums" ? stepLabel(value, "drums")[0] : String(value);
        cell.innerHTML = `<small>${index}</small>${text}`;
        return cell;
      });
      if (active && !recording && laneIndex === 0) {
        const cursor = document.createElement("span");
        cursor.className = `cell cursor${selected === steps.length ? " is-selected" : ""}`;
        cursor.dataset.index = String(steps.length);
        cursor.innerHTML = `<small>${steps.length}</small>▮`;
        cursor.title = "Select this empty slot to add new steps at the end.";
        views.push(cursor);
      }
      cells.replaceChildren(...views);
      laneCells.push(views);
      row.append(label, cells);
      group.append(row);
    });
    group.addEventListener("click", (event) => {
      const cell = event.target.closest(".cell");
      if (partIndex !== state.active) selectPart(partIndex);
      if (cell && !take) moveCursor(Number(cell.dataset.index));
    });
    return group;
  });
  $("#lanes").replaceChildren(...groups);
  // Keep the selected step in view sideways without scrolling the page away from the keyboard.
  for (const cell of document.querySelectorAll("#lanes .lane-group.is-active .is-selected")) {
    const cells = cell.parentElement;
    if (cell.offsetLeft < cells.scrollLeft || cell.offsetLeft + cell.offsetWidth > cells.scrollLeft + cells.clientWidth) {
      cells.scrollLeft = cell.offsetLeft - cells.clientWidth / 2;
    }
  }
  const previous = highlighted;
  highlighted = -1;
  setHighlight(previous);
}

function renderStepDetail() {
  const part = activePart();
  const index = cursorOf(part);
  const length = stepCount(part);
  const drums = part.voice === "drums";
  let text;
  if (take) {
    text = "Recording… editing resumes when the take ends.";
  } else if (index === length) {
    text = `index ${index} · end of the list: the next ${drums ? "hit" : "note"} is added here.`;
  } else if (drums) {
    const hits = part.lanes.filter((lane) => lane.steps[index] === lane.hit).map((lane) => `${lane.variable}[${index}] = ${lane.name.toUpperCase()}`);
    text = hits.length ? hits.join(" · ") : `index ${index} · REST in every drum list`;
  } else {
    const value = part.lanes[0].steps[index];
    text = `${part.lanes[0].variable}[${index}] = ${value >= 0 ? `${value} (${pitchName(value)})` : stepLabel(value, part.voice)}`;
  }
  $("#step-detail").textContent = text;
  $("#step-hold").hidden = drums;
  $("#step-prev").disabled = Boolean(take) || index === 0;
  $("#step-next").disabled = Boolean(take) || index === length;
  $("#step-delete").disabled = Boolean(take) || length === 0;
  $("#step-rest").disabled = Boolean(take);
  $("#step-hold").disabled = Boolean(take);
}

function setHighlight(index) {
  if (index === highlighted) return;
  for (const cells of laneCells) {
    cells[highlighted]?.classList.remove("is-playing");
    cells[index]?.classList.add("is-playing");
  }
  highlighted = index;
}

function renderCode() {
  const part = activePart();
  const stepsPerBar = state.stepsPerBeat * BEATS_PER_BAR;
  const lanes = part.lanes.filter((lane) => (part.voice === "drums" ? hasSound(lane.steps) : lane.steps.length > 0));
  const partCode = lanes.map((lane) => formatList(lane.variable, lane.steps, part.voice, stepsPerBar)).join("\n");
  // Only the lists are copied; the heading says which voice to pass to add_track().
  $("#part-code-label").textContent = `${part.name} ${part.voice === "drums" ? "lists" : "list"} · voice="${part.voice}"`;
  $("#part-code").textContent = partCode || `# Play some ${part.voice === "drums" ? "drums" : "notes"} to build this list.`;
  $("#copy-part").disabled = !partCode;
}

function updateControls() {
  const busy = Boolean(transport);
  $("#stop").disabled = !busy;
  $("#undo").disabled = Boolean(take) || history.get(activePart().id).length === 0;
  $("#clear-part").disabled = Boolean(take);
  $("#record").textContent = take ? "■ Stop recording" : "● Record";
  $("#record").classList.toggle("is-recording", Boolean(take));
  for (const input of ["#tempo", "#steps-per-beat", "#take-length"]) $(input).disabled = busy;
  document.querySelectorAll('input[name="mode"]').forEach((input) => { input.disabled = busy; });
  renderStepDetail();
}

function changed() {
  document.body.dataset.mode = state.mode;
  renderParts();
  renderLanes();
  renderCode();
  updateControls();
  save();
}

async function copy(text, label) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.append(area);
    area.select();
    const copied = document.execCommand("copy");
    area.remove();
    if (!copied) {
      $("#copy-status").textContent = "Copying is blocked here; select the code and copy it yourself.";
      return;
    }
  }
  $("#copy-status").textContent = `Copied the ${label}. Paste it into your Python file.`;
}

// ---------- setup ----------

function setTiming(bpm, stepsPerBeat) {
  const limit = maxSteps(bpm, stepsPerBeat);
  const tooLong = state.parts.find((part) => part.lanes.some((lane) => lane.steps.length > limit));
  if (tooLong) {
    $("#tempo").value = String(state.bpm);
    $("#steps-per-beat").value = String(state.stepsPerBeat);
    showError(`${tooLong.name} would exceed the player's 120-second limit. Shorten that part, choose a faster tempo, or use more steps per beat.`);
    return;
  }
  state.bpm = bpm;
  state.stepsPerBeat = stepsPerBeat;
  hideError();
  changed();
}

function setup() {
  restore();
  $(`input[name="mode"][value="${state.mode}"]`).checked = true;
  $("#tempo").value = String(state.bpm);
  $("#steps-per-beat").value = String(state.stepsPerBeat);
  $("#take-length").value = String(state.takeBars);
  $("#click-track").checked = state.click;

  document.querySelectorAll('input[name="mode"]').forEach((input) => input.addEventListener("change", () => {
    state.mode = input.value;
    releaseAll();
    renderInstrument();
    changed();
    announce(state.mode === "step" ? "Step entry: each key fills the next index." : "Live record: press Enter or Record, wait for the count-in, then play.");
  }));
  $("#tempo").addEventListener("change", () => {
    const bpm = Number($("#tempo").value);
    if (!Number.isInteger(bpm) || bpm < 30 || bpm > 300) {
      $("#tempo").value = String(state.bpm);
      return showError("Use a whole-number tempo from 30 through 300 BPM.");
    }
    setTiming(bpm, state.stepsPerBeat);
  });
  $("#steps-per-beat").addEventListener("change", () => {
    setTiming(state.bpm, Number($("#steps-per-beat").value));
  });
  $("#take-length").addEventListener("change", () => {
    state.takeBars = Number($("#take-length").value);
    save();
  });
  $("#click-track").addEventListener("change", () => {
    state.click = $("#click-track").checked;
    save();
  });
  $("#master-volume").addEventListener("input", () => {
    state.masterVolume = Number($("#master-volume").value) / 100;
    $("#master-volume-value").textContent = `${$("#master-volume").value}%`;
    if (audio) audio.master.gain.setTargetAtTime(state.masterVolume, audio.context.currentTime, 0.01);
  });
  $("#record").addEventListener("click", () => void startTake());
  $("#play-all").addEventListener("click", () => void playAll());
  $("#stop").addEventListener("click", () => {
    if (take) finishTake(true);
    else {
      stopTransport();
      announce("Stopped.");
    }
  });
  $("#undo").addEventListener("click", undo);
  $("#step-prev").addEventListener("click", () => moveCursor(cursorOf(activePart()) - 1));
  $("#step-next").addEventListener("click", () => moveCursor(cursorOf(activePart()) + 1));
  $("#step-rest").addEventListener("click", addRest);
  $("#step-hold").addEventListener("click", addHold);
  $("#step-delete").addEventListener("click", removeStep);
  $("#clear-part").addEventListener("click", clearPart);
  $("#copy-part").addEventListener("click", () => void copy($("#part-code").textContent, `${activePart().name} list`));
  // Hand the keyboard back to the instrument once a setting is chosen.
  for (const input of ["#tempo", "#steps-per-beat", "#take-length"]) $(input).addEventListener("change", () => $(input).blur());
  document.addEventListener("keydown", onKeyDown);
  document.addEventListener("keyup", onKeyUp);
  window.addEventListener("blur", releaseAll);

  renderInstrument();
  changed();
  document.body.dataset.ready = "true";
}

setup();
