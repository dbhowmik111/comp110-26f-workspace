/** Audio-clock scheduling shared by the player and browser acceptance tests. */
export const SAMPLE_RATE = 48000;
export const TRACK_GAIN = 1 / 8;
export const DEFAULT_MASTER_VOLUME = 0.8;
// Fixed headroom also covers the browser's band-limited square-wave overshoot.
export const VOICE_PEAK_GAIN = 0.7;
// Share the queue across score replacements as well as rapid transport clicks.
let sharedRenderQueue = Promise.resolve();

export function stepSeconds(bpm, stepsPerBeat) {
  return 60 / bpm / stepsPerBeat;
}

export function frequency(pitch) {
  return 440 * 2 ** ((pitch - 69) / 12);
}

/** All buffers use this same nearest-sample rounding rule. */
export function sampleLength(song, bpm = song.bpm) {
  return Math.max(1, Math.round(song.song_steps * stepSeconds(bpm, song.steps_per_beat) * SAMPLE_RATE));
}

export function eventTimes(event, secondsPerStep) {
  return {
    start: event.start_step * secondsPerStep,
    end: (event.start_step + event.duration_steps) * secondsPerStep,
  };
}

function envelope(context, start, end) {
  const gain = context.createGain();
  const attack = Math.min(0.005, (end - start) / 4);
  const release = Math.min(0.008, (end - start) / 4);
  gain.gain.setValueAtTime(0, start);
  gain.gain.linearRampToValueAtTime(VOICE_PEAK_GAIN, start + attack);
  gain.gain.setValueAtTime(VOICE_PEAK_GAIN, end - release);
  gain.gain.linearRampToValueAtTime(0, end);
  gain.connect(context.destination);
  return gain;
}

/** A local, repeatable noise source; no recorded samples or network assets. */
export function deterministicNoise(length, seed = 1) {
  const samples = new Float32Array(length);
  let state = seed || 1;
  for (let index = 0; index < length; index += 1) {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    samples[index] = (state >>> 0) / 2147483648 - 1;
  }
  return samples;
}

function drumEnvelope(context, start, end, peak, destination) {
  const gain = context.createGain();
  const attack = Math.min(0.002, (end - start) / 4);
  gain.gain.setValueAtTime(0, start);
  gain.gain.linearRampToValueAtTime(peak, start + attack);
  gain.gain.exponentialRampToValueAtTime(0.0001, end - 0.001);
  gain.gain.linearRampToValueAtTime(0, end);
  gain.connect(destination);
  return gain;
}

/** Schedule one preset drum hit; the studio passes its own live destination. */
export function renderDrum(context, event, start, trackEnd, destination = context.destination) {
  const duration = event.pitch === 36 ? 0.2 : event.pitch === 38 ? 0.14 : 0.045;
  const end = Math.min(start + duration, trackEnd);
  if (event.pitch === 36) {
    const oscillator = context.createOscillator();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(160, start);
    oscillator.frequency.exponentialRampToValueAtTime(45, Math.min(start + 0.11, end));
    oscillator.connect(drumEnvelope(context, start, end, 0.7, destination));
    oscillator.start(start);
    oscillator.stop(end);
    return;
  }
  const frames = Math.max(1, Math.ceil((end - start) * SAMPLE_RATE));
  const noise = context.createBuffer(1, frames, SAMPLE_RATE);
  noise.copyToChannel(deterministicNoise(frames, event.pitch * 65537 + event.start_step + 1), 0);
  const source = context.createBufferSource();
  source.buffer = noise;
  const filter = context.createBiquadFilter();
  filter.type = "highpass";
  filter.frequency.value = event.pitch === 38 ? 1000 : 7000;
  filter.Q.value = 0.5;
  source.connect(filter);
  filter.connect(drumEnvelope(context, start, end, event.pitch === 38 ? 0.42 : 0.32, destination));
  source.start(start);
  source.stop(end);
  if (event.pitch === 38) {
    const body = context.createOscillator();
    body.type = "triangle";
    body.frequency.value = 175;
    body.connect(drumEnvelope(context, start, end, 0.16, destination));
    body.start(start);
    body.stop(end);
  }
}

export async function renderTrack(song, track, bpm = song.bpm) {
  const context = new OfflineAudioContext(1, sampleLength(song, bpm), SAMPLE_RATE);
  const secondsPerStep = stepSeconds(bpm, song.steps_per_beat);
  const trackEnd = track.steps.length * secondsPerStep;
  for (const event of track.events) {
    const { start, end } = eventTimes(event, secondsPerStep);
    if (track.voice === "drums") {
      // Preset decays may overlap steps, but never outlive the source list.
      renderDrum(context, event, start, trackEnd);
      continue;
    }
    const oscillator = context.createOscillator();
    oscillator.type = track.voice === "triangle" ? "triangle" : "square";
    oscillator.frequency.setValueAtTime(frequency(event.pitch), start);
    oscillator.connect(envelope(context, start, end));
    oscillator.start(start);
    oscillator.stop(end);
  }
  return context.startRendering();
}

export class AudioPlayer {
  constructor(song, onState) {
    this.song = song;
    this.onState = onState;
    this.context = null;
    this.master = null;
    this.analyser = null;
    this.buffers = null;
    this.sources = [];
    this.gains = [];
    this.generation = 0;
    this.state = "ready";
    this.startedAt = 0;
    this.muted = new Set();
    this.volumes = new Map();
    this.masterVolume = DEFAULT_MASTER_VOLUME;
    this.bpm = song.bpm;
    this.loop = false;
    // Offline rendering cannot be aborted. Even abandoned generations wait here.
    this.renderQueue = sharedRenderQueue;
  }

  setState(state, message = "") {
    this.state = state;
    this.onState(state, message);
  }

  get elapsedSeconds() {
    if (!this.context || !["playing", "suspended"].includes(this.state)) return 0;
    const elapsed = Math.max(0, this.context.currentTime - this.startedAt);
    return this.loop ? elapsed % this.duration : Math.min(elapsed, this.duration);
  }

  get duration() {
    return sampleLength(this.song, this.bpm) / SAMPLE_RATE;
  }

  /**
   * Read the live combined signal after track and master listening gains.
   * @param {Float32Array} samples Reuse a 2048-sample array between frames.
   * @returns {boolean} Whether a running performance supplied these samples.
   */
  readWaveform(samples) {
    samples.fill(0);
    if (this.state !== "playing" || this.context?.state !== "running" || !this.analyser) return false;
    this.analyser.getFloatTimeDomainData(samples);
    return true;
  }

  setTempo(bpm) {
    if (!Number.isInteger(bpm) || bpm < 30 || bpm > 300) {
      throw new RangeError("Use a whole-number tempo from 30 through 300 BPM.");
    }
    if (this.song.song_steps * stepSeconds(bpm, this.song.steps_per_beat) > 120) {
      const minimum = Math.max(30, Math.ceil(this.song.song_steps * 60 / this.song.steps_per_beat / 120));
      throw new RangeError(`This score needs at least ${minimum} BPM to stay within 120 seconds. The previous tempo is unchanged.`);
    }
    if (bpm === this.bpm) return;
    this.bpm = bpm;
    this.buffers = null;
    this.stop();
  }

  setLoop(loop) {
    if (["playing", "rendering", "suspended"].includes(this.state)) {
      throw new Error("Stop playback before changing whole-song looping.");
    }
    this.loop = Boolean(loop);
  }

  setMasterVolume(volume) {
    if (!Number.isFinite(volume) || volume < 0 || volume > 1) throw new RangeError("Volume must be between 0 and 1.");
    this.masterVolume = volume;
    if (this.master && this.context) this.master.gain.setTargetAtTime(volume, this.context.currentTime, 0.01);
  }

  setVolume(trackId, volume) {
    if (!Number.isFinite(volume) || volume < 0 || volume > 1) throw new RangeError("Volume must be between 0 and 1.");
    this.volumes.set(trackId, volume);
    this.updateGain(trackId);
  }

  trackGain(trackId) {
    return this.muted.has(trackId) ? 0 : TRACK_GAIN * (this.volumes.get(trackId) ?? 1);
  }

  updateGain(trackId) {
    const index = this.song.tracks.findIndex((track) => track.id === trackId);
    if (this.gains[index] && this.context) {
      this.gains[index].gain.setTargetAtTime(this.trackGain(trackId), this.context.currentTime, 0.01);
    }
  }

  setMuted(trackId, muted) {
    if (muted) this.muted.add(trackId);
    else this.muted.delete(trackId);
    this.updateGain(trackId);
  }

  releaseSources() {
    for (const source of this.sources) {
      source.onended = null;
      source.stop();
      source.disconnect();
    }
    for (const gain of this.gains) gain.disconnect();
    this.sources = [];
    this.gains = [];
  }

  stop() {
    this.generation += 1;
    this.releaseSources();
    this.startedAt = 0;
    this.setState("stopped");
  }

  dispose() {
    this.stop();
    this.buffers = null;
    if (this.context) {
      this.context.onstatechange = null;
      void this.context.close().catch(() => {});
      this.context = null;
    }
    this.master?.disconnect();
    this.master = null;
    this.analyser?.disconnect();
    this.analyser = null;
  }

  async resumePerformance() {
    const generation = this.generation;
    try {
      // This call still happens synchronously within the new user gesture.
      await this.context.resume();
      if (generation === this.generation) this.setState("playing");
    } catch {
      if (generation === this.generation) this.setState("suspended", "Audio is paused by the browser. Click Resume audio to try again, or Stop.");
    }
  }

  /** Called directly by the click handler: activate audio before the first await. */
  async play() {
    if (this.state === "playing" || this.state === "rendering") return;
    if (this.state === "suspended") return this.resumePerformance();
    const generation = ++this.generation;
    const bpm = this.bpm;
    try {
      if (!this.context) {
        this.context = new AudioContext();
        this.context.onstatechange = () => {
          if (this.state === "playing" && this.context.state !== "running") this.setState("suspended");
          else if (this.state === "suspended" && this.context.state === "running") this.setState("playing");
        };
      }
      const activation = this.context.resume();
      this.master ??= this.context.createGain();
      if (!this.analyser) {
        this.analyser = this.context.createAnalyser();
        this.analyser.fftSize = 2048;
        this.analyser.connect(this.context.destination);
      }
      this.master.gain.value = this.masterVolume;
      this.master.disconnect();
      this.master.connect(this.analyser);
      this.setState("rendering");
      await activation;
      if (generation !== this.generation) return;
      if (!this.buffers) {
        const buffers = [];
        for (const track of this.song.tracks) {
          const pending = sharedRenderQueue.then(() => generation === this.generation ? renderTrack(this.song, track, bpm) : null);
          // A rendering rejection must not poison the next playback's queue.
          sharedRenderQueue = pending.then(() => undefined, () => undefined);
          this.renderQueue = sharedRenderQueue;
          const buffer = await pending;
          if (generation !== this.generation) return;
          buffers.push(buffer);
        }
        this.buffers = buffers;
      }
      if (generation !== this.generation) return;
      this.startedAt = this.context.currentTime + 0.05;
      for (const [index, buffer] of this.buffers.entries()) {
        const source = this.context.createBufferSource();
        const gain = this.context.createGain();
        source.buffer = buffer;
        source.loop = this.loop;
        source.loopStart = 0;
        source.loopEnd = buffer.duration;
        gain.gain.value = this.trackGain(this.song.tracks[index].id);
        source.connect(gain);
        gain.connect(this.master);
        this.sources.push(source);
        this.gains.push(gain);
        source.start(this.startedAt);
      }
      this.sources[0].onended = () => {
        if (generation === this.generation && !this.loop) this.stop();
      };
      this.setState(this.context.state === "running" ? "playing" : "suspended");
    } catch (error) {
      if (generation !== this.generation) return;
      this.releaseSources();
      this.setState("error", `Audio could not start. ${error.message || "Click Play to try again."}`);
    }
  }
}
