import { AudioPlayer, stepSeconds } from "./audio.js";

const play = document.querySelector("#play");
const stop = document.querySelector("#stop");
const errorMessage = document.querySelector("#error");
const tempo = document.querySelector("#tempo");
const loop = document.querySelector("#loop");
const masterVolume = document.querySelector("#master-volume");
let song = null;
let player = null;
let animation = 0;
let highlightedIndex = -1;
let trackViews = [];
let indexHeaders = [];
let selectedTrack = 0;
let selectedIndex = 0;
let scoreScroll = null;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const waveformSamples = new Float32Array(2048);
let waveformCanvas = null;
let waveformContext = null;
let waveformEnabled = !reducedMotion.matches;
let waveformPreferenceOverridden = false;
let waveformGain = 8;
let initialLoading = true;
let healthChecking = false;
let healthRequested = false;
let healthTimer = 0;
let reloadEnabled = false;
let launchId = null;
let loadedRevision = -1;
let latestRevision = -1;
let scoreGeneration = 0;

export function pitchName(pitch) {
  const names = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];
  return `${names[pitch % 12]}${Math.floor(pitch / 12) - 1}`;
}

export function stepLabel(value, voice = "pulse") {
  if (value === -1) return "REST";
  if (value === -2) return "HOLD";
  if (voice === "drums") return { 36: "KICK", 38: "SNARE", 42: "HAT" }[value];
  return pitchName(value);
}

function resetPlayhead() {
  cancelAnimationFrame(animation);
  for (const view of trackViews) {
    view.buttons[highlightedIndex]?.parentElement.classList.remove("is-playing");
    view.tail?.classList.remove("is-current");
  }
  indexHeaders[highlightedIndex]?.classList.remove("is-playing");
  highlightedIndex = -1;
  document.querySelector("#playhead").textContent = "Playback starts at index 0.";
  drawWaveform(false);
}

function updatePlayhead() {
  if (player?.state !== "playing") return;
  if (waveformEnabled) drawWaveform(true);
  const seconds = player.elapsedSeconds;
  const index = Math.min(song.song_steps - 1, Math.floor(seconds / stepSeconds(player.bpm, song.steps_per_beat)));
  if (index !== highlightedIndex) {
    for (const view of trackViews) {
      view.buttons[highlightedIndex]?.parentElement.classList.remove("is-playing");
      const button = view.buttons[index];
      button?.parentElement.classList.add("is-playing");
      view.tail?.classList.toggle("is-current", index >= view.track.steps.length);
    }
    indexHeaders[highlightedIndex]?.classList.remove("is-playing");
    indexHeaders[index]?.classList.add("is-playing");
    if (!reducedMotion.matches) revealStep(indexHeaders[index]);
    document.querySelector("#playhead").textContent = `Now playing · index ${index} · ${seconds.toFixed(2)} seconds`;
    highlightedIndex = index;
  }
  animation = requestAnimationFrame(updatePlayhead);
}

function initializeWaveform() {
  let panel = document.querySelector("#signal-panel");
  if (panel && ["#waveform", "#motion-toggle", "#signal-status", "#waveform-gain"].some((selector) => !panel.querySelector(selector))) {
    panel.remove();
    panel = null;
  }
  if (!panel) {
    panel = textElement("section", "", "signal-panel");
    panel.id = "signal-panel";
    panel.setAttribute("aria-label", "Live master waveform");
    const heading = textElement("div", "", "signal-heading");
    const title = textElement("span", "Live signal", "signal-title");
    title.append(textElement("span", "Master output"));
    const status = textElement("span", "Ready · no signal");
    status.id = "signal-status";
    const motion = textElement("button", "Motion on");
    motion.id = "motion-toggle";
    motion.type = "button";
    motion.setAttribute("aria-label", "Animate waveform");
    heading.append(title, status, motion);
    const canvas = document.createElement("canvas");
    canvas.id = "waveform";
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "Live waveform of the combined audio output");
    canvas.setAttribute("aria-describedby", "waveform-description");
    canvas.textContent = "A waveform displays the combined sound. Playback also works without this visual.";
    const axis = textElement("div", "", "signal-axis");
    const gainLabel = textElement("label", "Fixed view gain ");
    const gain = document.createElement("select");
    gain.id = "waveform-gain";
    gain.setAttribute("aria-label", "Waveform display gain");
    for (const amount of [1, 2, 4, 8]) {
      const option = textElement("option", `×${amount}`);
      option.value = String(amount);
      option.selected = amount === 8;
      gain.append(option);
    }
    gainLabel.append(gain);
    axis.append(textElement("span", "TIME →"), gainLabel);
    const description = textElement("p", "The waveform follows the actual combined audio after mute and volume controls. Display gain is fixed at the selected scale, initially eight times. It does not change the sound. Animation can be turned off.", "sr-only");
    description.id = "waveform-description";
    panel.append(heading, canvas, axis, description);
    document.querySelector("#tracks").before(panel);
  }
  waveformCanvas = document.querySelector("#waveform");
  waveformContext = waveformCanvas?.getContext("2d");
  const toggle = document.querySelector("#motion-toggle");
  document.querySelector("#waveform-gain").addEventListener("change", (event) => {
    waveformGain = Number(event.target.value);
    drawWaveform(waveformEnabled);
  });
  toggle.addEventListener("click", () => {
    waveformEnabled = !waveformEnabled;
    waveformPreferenceOverridden = true;
    updateWaveformStatus();
    drawWaveform(waveformEnabled);
  });
  reducedMotion.addEventListener("change", () => {
    if (!waveformPreferenceOverridden) waveformEnabled = !reducedMotion.matches;
    updateWaveformStatus();
    drawWaveform(waveformEnabled);
  });
  new ResizeObserver(() => drawWaveform(waveformEnabled)).observe(waveformCanvas);
  window.addEventListener("resize", () => drawWaveform(waveformEnabled));
  updateWaveformStatus();
  drawWaveform(false);
}

function updateWaveformStatus() {
  const toggle = document.querySelector("#motion-toggle");
  if (!toggle) return;
  toggle.setAttribute("aria-pressed", String(waveformEnabled));
  toggle.textContent = waveformEnabled ? "Motion on" : "Enable motion";
  const state = player?.state;
  let label = state === "playing" ? "Live · follows your mix" : state === "rendering" ? "Preparing audio" : state === "suspended" ? "Audio paused" : "Ready · no signal";
  if (!waveformEnabled) label = "Motion paused · audio still available";
  if (!waveformContext) label = "Visual unavailable · audio still available";
  document.querySelector("#signal-status").textContent = label;
}

function drawWaveform(readLive) {
  if (!waveformCanvas || !waveformContext) return;
  const bounds = waveformCanvas.getBoundingClientRect();
  if (!bounds.width || !bounds.height) return;
  const density = window.devicePixelRatio || 1;
  const width = Math.round(bounds.width * density);
  const height = Math.round(bounds.height * density);
  if (waveformCanvas.width !== width || waveformCanvas.height !== height) {
    waveformCanvas.width = width;
    waveformCanvas.height = height;
  }
  const context = waveformContext;
  context.setTransform(density, 0, 0, density, 0, 0);
  const w = bounds.width;
  const h = bounds.height;
  const center = h / 2;
  context.clearRect(0, 0, w, h);
  context.fillStyle = "#090f1b";
  context.fillRect(0, 0, w, h);
  context.strokeStyle = "#243244";
  context.lineWidth = 0.5;
  context.beginPath();
  for (let line = 1; line < 16; line += 1) {
    const x = w * line / 16;
    context.moveTo(x, 0);
    context.lineTo(x, h);
  }
  for (let line = 1; line < 4; line += 1) {
    const y = h * line / 4;
    context.moveTo(0, y);
    context.lineTo(w, y);
  }
  context.stroke();
  waveformSamples.fill(0);
  const live = readLive && waveformEnabled && player?.state === "playing" && player?.readWaveform?.(waveformSamples) === true;
  waveformCanvas.dataset.signal = live ? "live" : waveformEnabled ? "idle" : "paused";
  const color = context.createLinearGradient(0, 0, w, 0);
  color.addColorStop(0, "#ed6cff");
  color.addColorStop(0.45, "#58e9f0");
  color.addColorStop(1, "#ceff69");
  context.strokeStyle = live ? color : "#537681";
  context.lineWidth = live ? 1.5 : 1;
  context.shadowColor = "#58e9f0";
  context.shadowBlur = live ? 5 : 0;
  context.beginPath();
  // Fixed gain only: quiet and muted mixes stay visibly quiet.
  const scale = (h / 2 - 7) * waveformGain;
  for (let index = 0; index < waveformSamples.length; index += 1) {
    const x = index * w / (waveformSamples.length - 1);
    const y = center - waveformSamples[index] * scale;
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  }
  context.stroke();
  context.shadowBlur = 0;
}

function revealStep(element) {
  if (!element || !scoreScroll) return;
  const card = element.getBoundingClientRect();
  const viewport = scoreScroll.getBoundingClientRect();
  const labelWidth = scoreScroll.querySelector(".track-column").getBoundingClientRect().width;
  if (card.right > viewport.right - 8) scoreScroll.scrollLeft += card.right - viewport.right + 8;
  else if (card.left < viewport.left + labelWidth + 8) scoreScroll.scrollLeft += card.left - viewport.left - labelWidth - 8;
}

function textElement(tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = text;
  element.className = className;
  return element;
}

function freezeSnapshot(value) {
  if (value && typeof value === "object") {
    Object.values(value).forEach(freezeSnapshot);
    Object.freeze(value);
  }
  return value;
}

function showState(state, message = "") {
  const labels = {
    loading: "Loading score",
    ready: "Ready · click Play to listen",
    rendering: "Rendering audio…",
    playing: "Playing",
    stopped: "Stopped · ready to play again",
    error: "Playback error",
    suspended: "Audio paused by the browser · click Resume audio",
  };
  document.querySelector("#playback-status").textContent = labels[state];
  document.body.dataset.state = state;
  play.disabled = !player || state === "loading" || state === "rendering" || state === "playing";
  stop.disabled = !player;
  play.textContent = state === "suspended" ? "▶ Resume audio" : "▶ Play";
  tempo.disabled = !player;
  loop.disabled = !player || ["playing", "rendering", "suspended"].includes(state);
  masterVolume.disabled = !player;
  errorMessage.hidden = !message;
  errorMessage.textContent = message;
  resetPlayhead();
  if (state === "playing") updatePlayhead();
  updateWaveformStatus();
}

function describeStep(track, index, snapshot, bpm = snapshot.bpm) {
  const value = track.steps[index];
  const secondsPerStep = stepSeconds(bpm, snapshot.steps_per_beat);
  const event = track.events.find((item) => item.start_step <= index && index < item.start_step + item.duration_steps);
  let action = value === -1 ? "REST · silence" : value === -2 ? `HOLD · continues ${pitchName(event.pitch)} (${event.pitch})` : track.voice === "drums" ? `${stepLabel(value, track.voice)} · starts a drum hit` : `${pitchName(value)} · starts a note`;
  if (event) action += `; ${track.voice === "drums" ? "hit slot" : "note duration"} ${event.duration_steps} steps (${(event.duration_steps * secondsPerStep).toFixed(2)} seconds)`;
  const measure = Math.floor(index / (4 * snapshot.steps_per_beat)) + 1;
  const beat = Math.floor(index / snapshot.steps_per_beat) % 4 + 1;
  const subdivision = index % snapshot.steps_per_beat + 1;
  return `Index ${index} · raw value ${value} · ${action}. Starts at ${(index * secondsPerStep).toFixed(2)} seconds; measure ${measure}, beat ${beat}, step ${subdivision} of the beat. Each list entry lasts ${secondsPerStep.toFixed(2)} seconds.`;
}

function refreshTiming() {
  if (!song || !player) return;
  const secondsPerStep = stepSeconds(player.bpm, song.steps_per_beat);
  const changed = player.bpm !== song.bpm ? ` (Python: ${song.bpm} BPM)` : "";
  document.querySelector("#song-summary").textContent = `${player.bpm} BPM${changed} · ${song.steps_per_beat} steps per beat · ${song.song_steps} steps · ${(song.song_steps * secondsPerStep).toFixed(2)} seconds`;
  for (const view of trackViews) view.meta.textContent = `${view.track.voice} · ${view.track.steps.length} steps · ${(view.track.steps.length * secondsPerStep).toFixed(2)} s`;
  updateInspector();
}

function updateInspector(bpm = player?.bpm ?? song.bpm) {
  const track = trackViews[selectedTrack]?.track;
  if (!track) return;
  document.querySelector("#step-details").textContent = `${track.name} · ${describeStep(track, selectedIndex, song, bpm)}`;
}

function selectStep(trackIndex, index, focus = false) {
  const previous = trackViews[selectedTrack]?.buttons[selectedIndex];
  previous?.setAttribute("aria-pressed", "false");
  if (previous) previous.tabIndex = -1;
  selectedTrack = trackIndex;
  selectedIndex = index;
  const button = trackViews[trackIndex].buttons[index];
  button.setAttribute("aria-pressed", "true");
  button.tabIndex = 0;
  updateInspector();
  if (focus) {
    button.focus({ preventScroll: true });
    button.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "auto" });
    revealStep(button);
  }
}

function speakerIcon(muted) {
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.7");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  const speaker = document.createElementNS(namespace, "path");
  speaker.setAttribute("d", "M11 4 5 9H2v6h3l6 5V4Z");
  const sound = document.createElementNS(namespace, "path");
  sound.setAttribute("d", muted ? "m16 9 6 6m0-6-6 6" : "M15 8c3 2 3 6 0 8m3-11c5 4 5 10 0 14");
  svg.append(speaker, sound);
  return svg;
}

function volumePopover(track, host) {
  const trigger = textElement("button", "⋯", "volume-trigger icon-button");
  trigger.type = "button";
  trigger.setAttribute("aria-label", `Volume settings for ${track.name}`);
  trigger.setAttribute("aria-haspopup", "dialog");
  trigger.setAttribute("aria-expanded", "false");
  const panel = textElement("div", "", "volume-popover");
  panel.id = `volume-${track.id}`;
  panel.setAttribute("popover", "auto");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", `Volume for ${track.name}`);
  trigger.setAttribute("popovertarget", panel.id);
  const value = textElement("output", "100%", "volume-value");
  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = "0";
  slider.max = "100";
  slider.value = "100";
  slider.autofocus = true;
  slider.setAttribute("aria-label", `Volume ${track.name}`);
  slider.setAttribute("aria-valuetext", "100 percent");
  slider.addEventListener("input", () => {
    player?.setVolume(track.id, Number(slider.value) / 100);
    value.textContent = `${slider.value}%`;
    slider.setAttribute("aria-valuetext", `${slider.value} percent`);
  });
  panel.append(textElement("strong", track.name), slider, value);
  panel.addEventListener("beforetoggle", (event) => {
    if (event.newState !== "open") return;
    const rectangle = trigger.getBoundingClientRect();
    panel.style.left = `${Math.max(8, Math.min(rectangle.left, innerWidth - 228))}px`;
    panel.style.top = `${Math.max(8, Math.min(rectangle.bottom + 6, innerHeight - 112))}px`;
  });
  panel.addEventListener("toggle", () => trigger.setAttribute("aria-expanded", String(panel.matches(":popover-open"))));
  host.append(panel);
  return trigger;
}

function showScore(snapshot) {
  document.title = `${snapshot.title} · daft comp`;
  document.querySelector("#song-title").textContent = snapshot.title;
  document.querySelector("#session-label").textContent = `Session ${snapshot.session_id.slice(0, 8)} · latest Python run`;
  const seconds = snapshot.song_steps * stepSeconds(snapshot.bpm, snapshot.steps_per_beat);
  document.querySelector("#song-summary").textContent = `${snapshot.bpm} BPM · ${snapshot.steps_per_beat} steps per beat · ${snapshot.song_steps} steps · ${seconds.toFixed(2)} seconds`;
  const tracks = document.querySelector("#tracks");
  tracks.replaceChildren();
  // A tab can briefly combine an older HTML response with freshly updated assets.
  let popovers = document.querySelector("#volume-popovers");
  if (!popovers) {
    popovers = textElement("div", "");
    popovers.id = "volume-popovers";
    tracks.after(popovers);
  }
  if (!document.querySelector("#step-details")) {
    const inspector = textElement("section", "", "inspector");
    inspector.setAttribute("aria-label", "Selected step");
    const details = textElement("p", "");
    details.id = "step-details";
    inspector.append(details, textElement("p", "Select a value to inspect it. Arrow keys move between steps and tracks; Home/End jump within a track.", "keyboard-hint"));
    popovers.after(inspector);
  }
  popovers.replaceChildren();
  trackViews = [];
  indexHeaders = [];
  selectedTrack = 0;
  selectedIndex = 0;
  scoreScroll = textElement("div", "", "score-scroll");
  const table = textElement("table", "", "score-table");
  table.style.width = `calc(var(--track-width) + ${snapshot.song_steps * 44}px)`;
  table.append(textElement("caption", "Composition score. Rows are tracks; column headings are zero-based list indices.", "sr-only"));
  const thead = document.createElement("thead");
  const indices = document.createElement("tr");
  const corner = textElement("th", "Track / index", "track-column");
  corner.scope = "col";
  indices.append(corner);
  for (let index = 0; index < snapshot.song_steps; index += 1) {
    const cell = textElement("th", String(index), "step-index");
    cell.scope = "col";
    cell.dataset.index = String(index);
    if (index % (4 * snapshot.steps_per_beat) === 0) cell.classList.add("measure-start");
    indices.append(cell);
    indexHeaders.push(cell);
  }
  thead.append(indices);
  table.append(thead);
  const tbody = document.createElement("tbody");
  for (const [trackIndex, track] of snapshot.tracks.entries()) {
    const row = textElement("tr", "", "track");
    row.dataset.trackId = track.id;
    const label = textElement("th", "", "track-label-cell");
    label.scope = "row";
    const labelContent = textElement("div", "", "track-label-content");
    const mute = textElement("button", "", "mute-button icon-button");
    mute.type = "button";
    mute.setAttribute("aria-label", `Mute ${track.name}`);
    mute.setAttribute("aria-pressed", "false");
    mute.append(speakerIcon(false));
    mute.addEventListener("click", () => {
      const muted = mute.getAttribute("aria-pressed") !== "true";
      player?.setMuted(track.id, muted);
      mute.setAttribute("aria-pressed", String(muted));
      mute.replaceChildren(speakerIcon(muted));
      row.classList.toggle("is-muted", muted);
    });
    const name = textElement("span", "", "track-name");
    const duration = track.steps.length * stepSeconds(snapshot.bpm, snapshot.steps_per_beat);
    const meta = textElement("span", `${track.voice} · ${track.steps.length} steps · ${duration.toFixed(2)} s`, "track-voice");
    name.append(textElement("strong", track.name), meta);
    labelContent.append(mute, name, volumePopover(track, popovers));
    label.append(labelContent);
    row.append(label);
    const view = { track, buttons: [], tail: null, meta };
    trackViews.push(view);
    track.steps.forEach((value, index) => {
      const cell = textElement("td", "", "step");
      if (index % (4 * snapshot.steps_per_beat) === 0) cell.classList.add("measure-start");
      const button = textElement("button", "", "step-button");
      button.type = "button";
      button.dataset.index = String(index);
      button.tabIndex = trackIndex === 0 && index === 0 ? 0 : -1;
      button.setAttribute("aria-pressed", String(trackIndex === 0 && index === 0));
      button.setAttribute("aria-describedby", "step-details");
      button.setAttribute("aria-label", `${track.name}, index ${index}, raw value ${value}, ${stepLabel(value, track.voice)}`);
      button.append(textElement("span", String(value), "step-value"), textElement("span", stepLabel(value, track.voice), "step-name"));
      button.addEventListener("click", () => selectStep(trackIndex, index));
      button.addEventListener("keydown", (event) => {
        let nextTrack = trackIndex;
        let nextIndex = index;
        if (event.key === "ArrowRight") nextIndex = Math.min(index + 1, track.steps.length - 1);
        else if (event.key === "ArrowLeft") nextIndex = Math.max(index - 1, 0);
        else if (event.key === "ArrowDown") nextTrack = Math.min(trackIndex + 1, snapshot.tracks.length - 1);
        else if (event.key === "ArrowUp") nextTrack = Math.max(trackIndex - 1, 0);
        else if (event.key === "Home") nextIndex = 0;
        else if (event.key === "End") nextIndex = track.steps.length - 1;
        else return;
        event.preventDefault();
        nextIndex = Math.min(nextIndex, snapshot.tracks[nextTrack].steps.length - 1);
        selectStep(nextTrack, nextIndex, true);
      });
      view.buttons.push(button);
      cell.append(button);
      row.append(cell);
    });
    if (track.steps.length < snapshot.song_steps) {
      const tail = textElement("td", "", "track-ended");
      tail.colSpan = snapshot.song_steps - track.steps.length;
      tail.dataset.end = String(track.steps.length);
      tail.append(textElement("span", `Track ended · ${tail.colSpan} absent steps`, "ended-label"));
      tail.setAttribute("aria-label", `Track ended. ${tail.colSpan} absent steps outside ${track.name}'s list; not REST entries.`);
      view.tail = tail;
      row.append(tail);
    }
    tbody.append(row);
  }
  table.append(tbody);
  scoreScroll.append(table);
  tracks.append(scoreScroll);
  updateInspector(snapshot.bpm);
  const groups = document.querySelector("#source-groups");
  groups.replaceChildren();
  const trackNames = new Map(snapshot.tracks.map((track) => [track.id, track.name]));
  for (const group of snapshot.source_groups) {
    const item = textElement("li", "", "source-group");
    const names = group.track_ids.map((id) => trackNames.get(id));
    const relationship = names.length === 1
      ? `${names[0]} used this source list during the latest Python run.`
      : `${names.join(" and ")} used the same source list during the latest Python run.`;
    item.append(textElement("strong", group.id, "source-group-label"), textElement("p", relationship));
    groups.append(item);
  }
}

function showReloadStatus(health, updated = false) {
  const status = document.querySelector("#reload-status");
  status.hidden = !health.reload_enabled;
  status.classList.toggle("reload-error", Boolean(health.reload_error));
  if (!health.reload_enabled) return;
  const filename = health.score_filename || "your Python file";
  document.querySelector("#edit-instructions").textContent = `Save ${filename} to update this player, then click Play. The previous score stays available if an edit needs fixing.`;
  if (health.reload_error) {
    status.textContent = `Saved changes to ${filename} could not load: ${health.reload_error} Your previous composition is still available. Fix the file and save again.`;
  } else if (health.reloading) {
    status.textContent = `Loading saved changes to ${filename}…`;
  } else if (updated || loadedRevision > 0) {
    status.textContent = `Updated from ${filename}. Click Play to hear your saved changes. Save again to update this player.`;
  } else {
    status.textContent = `Save ${filename} to update this player. Playback stops when a new score is ready.`;
  }
}

async function fetchHealth() {
  const response = await fetch("/api/health", { cache: "no-store", signal: AbortSignal.timeout(3000) });
  if (!response.ok) throw new Error("Server unavailable");
  const health = await response.json();
  if (health.schema_version !== 1) throw new Error("Unsupported player version");
  const owner = health.launch_id ?? health.session_id;
  if (launchId !== null && owner !== launchId) throw new Error("A different player server owns this address");
  launchId = owner;
  return health;
}

function installScore(snapshot) {
  player?.dispose();
  player = null;
  song = freezeSnapshot(snapshot);
  showScore(song);
  player = new AudioPlayer(song, showState);
  tempo.value = String(song.bpm);
  tempo.removeAttribute("aria-invalid");
  loop.checked = false;
  masterVolume.value = String(player.masterVolume * 100);
  masterVolume.setAttribute("aria-valuetext", `${masterVolume.value} percent`);
  document.querySelector("#master-volume-value").textContent = `${masterVolume.value}%`;
  document.querySelector("#tempo-error").hidden = true;
  document.querySelector("#tempo-error").textContent = "";
  showState("ready");
}

async function refreshScore(health) {
  const generation = ++scoreGeneration;
  player?.stop();
  // Keep an initial schema/load error visible while background recovery retries.
  if (player) showState("loading");
  try {
    const response = await fetch("/api/song", { cache: "no-store", signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error("The saved score could not be loaded. Trying again shortly.");
    const snapshot = await response.json();
    if (snapshot.schema_version !== 1) throw new Error("This player cannot read the saved score version.");
    // A second save may finish while the score request is in flight.
    const current = await fetchHealth();
    if (generation !== scoreGeneration) return;
    latestRevision = Math.max(latestRevision, current.revision ?? 0);
    if (snapshot.session_id !== current.session_id || (current.revision ?? 0) < latestRevision || (current.revision ?? 0) < health.revision) {
      healthRequested = true;
      showState(player ? "stopped" : "loading");
      return;
    }
    installScore(snapshot);
    loadedRevision = current.revision ?? 0;
    showReloadStatus(current, true);
  } catch (error) {
    if (generation !== scoreGeneration) return;
    showState(player ? "stopped" : "error", player ? "" : error.message);
    const status = document.querySelector("#reload-status");
    status.hidden = false;
    status.classList.add("reload-error");
    status.textContent = `${error.message} ${player ? "The previous composition is still available." : "The score could not be displayed. Trying again shortly."}`;
  }
}

async function checkHealth() {
  if (initialLoading) return;
  if (healthChecking) {
    healthRequested = true;
    return;
  }
  healthChecking = true;
  clearTimeout(healthTimer);
  try {
    const health = await fetchHealth();
    reloadEnabled = health.reload_enabled === true;
    latestRevision = Math.max(latestRevision, health.revision ?? 0);
    if (song && health.session_id !== song.session_id && !reloadEnabled) throw new Error("Session changed");
    document.querySelector("#connection-status").textContent = "Player server connected";
    if (player && song?.session_id === health.session_id) loadedRevision = health.revision ?? 0;
    showReloadStatus(health);
    if (reloadEnabled && (!player || health.session_id !== song?.session_id) && (health.revision ?? 0) >= loadedRevision) {
      await refreshScore(health);
    }
  } catch {
    document.querySelector("#connection-status").textContent = "Server unavailable; this page contains the previous composition.";
  } finally {
    healthChecking = false;
    const delay = healthRequested ? 0 : reloadEnabled ? 1000 : 5000;
    healthRequested = false;
    healthTimer = window.setTimeout(() => void checkHealth(), delay);
  }
}

play.addEventListener("click", () => { if (player) void player.play(); });
stop.addEventListener("click", () => player?.stop());
tempo.addEventListener("change", () => {
  const message = document.querySelector("#tempo-error");
  try {
    player.setTempo(Number(tempo.value));
    message.hidden = true;
    message.textContent = "";
    tempo.removeAttribute("aria-invalid");
    refreshTiming();
  } catch (error) {
    tempo.value = String(player.bpm);
    tempo.setAttribute("aria-invalid", "true");
    message.hidden = false;
    message.textContent = error.message;
  }
});
loop.addEventListener("change", () => player?.setLoop(loop.checked));
masterVolume.addEventListener("input", () => {
  player?.setMasterVolume(Number(masterVolume.value) / 100);
  masterVolume.setAttribute("aria-valuetext", `${masterVolume.value} percent`);
  document.querySelector("#master-volume-value").textContent = `${masterVolume.value}%`;
});
window.addEventListener("focus", () => void checkHealth());

async function load() {
  try {
    initializeWaveform();
  } catch {
    // A graphics failure must not block score loading or listening.
    waveformCanvas = null;
    waveformContext = null;
    const panel = document.querySelector("#signal-panel");
    if (panel) panel.replaceChildren(textElement("p", "Waveform unavailable · audio still available", "signal-fallback"));
  }
  try {
    const response = await fetch("/api/song", { cache: "no-store", signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error("The score could not be loaded. Run your Python program again.");
    const snapshot = await response.json();
    if (snapshot.schema_version !== 1) throw new Error("This player cannot read this score version. Run your Python program again to open a matching player.");
    installScore(snapshot);
  } catch (error) {
    showState("error", error.message || "The score could not be loaded. Run your Python program again.");
  }
  initialLoading = false;
  void checkHealth();
}

void load();
