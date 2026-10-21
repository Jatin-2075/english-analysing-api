import { useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import "./results.css";
import {
  AlertCircle,
  AudioLines,
  Check,
  FileText,
  Gauge,
  ListChecks,
  Mic,
  Pause,
  RotateCcw,
  Send,
  ShieldCheck,
  Square,
  Upload,
  Volume2,
} from "lucide-react";

const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type GrammarError = {
  message: string;
  mistake: string;
  suggestions: string[];
  category: string;
};

type Analysis = {
  grammar?: {
    word_count?: number;
    grammar_error_count?: number;
    grammar_score?: number;
    errors?: GrammarError[];
  };
  fluency?: {
    fluency_score?: number;
    fluency_level?: string;
    pauses_per_100_words?: number;
  };
  pace?: {
    word_count?: number;
    audio_duration_seconds?: number;
    words_per_minute?: number;
  };
  pauses?: {
    pause_count?: number;
    average_pause_duration_seconds?: number;
    pause_durations_seconds?: number[];
  };
  filler_words?: {
    filler_count?: number;
    filler_words?: Record<string, number>;
    filler_rate_percent?: number;
  };
};

type Data = {
  transcript?: string;
  text?: string;
  analysis?: Analysis;
  detail?: string;
};

const numberOr = (value: number | undefined, fallback = 0) => value ?? fallback;
const formatLabel = (value: string) => value.replace(/_/g, " ");

function Metric({
  label,
  value,
  detail,
  icon,
  accent = "",
}: {
  label: string;
  value: string;
  detail: string;
  icon: ReactNode;
  accent?: string;
}) {
  return (
    <article className={`metric ${accent}`}>
      <div className="metric-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  );
}

function ScoreRing({ score, label }: { score: number; label: string }) {
  const safeScore = Math.max(0, Math.min(100, score));
  return (
    <div className="score-ring" style={{ "--score": `${safeScore * 3.6}deg` } as CSSProperties}>
      <div>
        <strong>{safeScore.toFixed(0)}</strong>
        <span>/ 100</span>
      </div>
      <small>{label}</small>
    </div>
  );
}

function GrammarPanel({ grammar }: { grammar: NonNullable<Analysis["grammar"]> }) {
  const errors = grammar.errors || [];
  return (
    <section className="detail-card grammar-card">
      <div className="detail-title">
        <div>
          <span className="eyebrow">LANGUAGE QUALITY</span>
          <h3>Grammar & writing</h3>
        </div>
        <ScoreRing score={numberOr(grammar.grammar_score)} label="grammar score" />
      </div>
      <div className="detail-stats">
        <div><b>{numberOr(grammar.word_count)}</b><span>words checked</span></div>
        <div><b>{numberOr(grammar.grammar_error_count)}</b><span>items to review</span></div>
      </div>
      {errors.length > 0 ? (
        <div className="issue-list">
          <h4>Suggestions for improvement</h4>
          {errors.map((error, index) => (
            <article className="issue" key={`${error.mistake}-${index}`}>
              <div className="issue-mark">{index + 1}</div>
              <div className="issue-content">
                <div className="issue-heading">
                  <b>{error.mistake || "Review this phrase"}</b>
                  <span>{formatLabel(error.category || "suggestion")}</span>
                </div>
                <p>{error.message}</p>
                {error.suggestions.length > 0 && (
                  <div className="suggestions">
                    {error.suggestions.map((suggestion) => <span key={suggestion}>{suggestion}</span>)}
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state"><Check size={16} /> No grammar issues found.</div>
      )}
    </section>
  );
}

function ResultsView({ data }: { data: Data }) {
  const analysis = data.analysis || {};
  const grammar = analysis.grammar;
  const fluency = analysis.fluency;
  const pace = analysis.pace;
  const pauses = analysis.pauses;
  const fillers = analysis.filler_words;
  const fillerEntries = Object.entries(fillers?.filler_words || {});

  return (
    <section className="results">
      <div className="resultshead">
        <div><small>YOUR RESULTS</small><h2>Assessment overview</h2></div>
      </div>
      {(data.transcript || data.text) && (
        <article className="transcript">
          <b><AudioLines size={15} /> Transcript / text</b>
          <p>{data.transcript || data.text}</p>
        </article>
      )}
      <div className="metrics">
        {grammar && <Metric label="Grammar" value={`${numberOr(grammar.grammar_score).toFixed(0)}%`} detail={`${numberOr(grammar.grammar_error_count)} suggestions`} icon={<ListChecks size={17} />} accent="lime" />}
        {fluency && <Metric label="Fluency" value={`${numberOr(fluency.fluency_score).toFixed(0)}%`} detail={fluency.fluency_level || "Speaking flow"} icon={<Volume2 size={17} />} accent="blue" />}
        {pace && <Metric label="Speaking pace" value={`${numberOr(pace.words_per_minute).toFixed(0)} WPM`} detail={`${numberOr(pace.audio_duration_seconds).toFixed(1)} seconds`} icon={<Gauge size={17} />} accent="violet" />}
        {pauses && <Metric label="Pauses" value={`${numberOr(pauses.pause_count)}`} detail={`${numberOr(pauses.average_pause_duration_seconds).toFixed(2)} sec average`} icon={<Pause size={17} />} accent="amber" />}
        {fillers && <Metric label="Filler words" value={`${numberOr(fillers.filler_count)}`} detail={`${numberOr(fillers.filler_rate_percent).toFixed(1)}% of words`} icon={<AudioLines size={17} />} accent="rose" />}
      </div>
      <div className="detail-grid">
        {grammar && <GrammarPanel grammar={grammar} />}
        <div className="side-details">
          {fluency && (
            <section className="detail-card compact-card">
              <div className="compact-heading"><Volume2 size={17} /><div><span className="eyebrow">DELIVERY</span><h3>Fluency level</h3></div></div>
              <div className="big-value">{fluency.fluency_level || "Not available"}</div>
              <p>{numberOr(fluency.pauses_per_100_words).toFixed(1)} pauses per 100 words</p>
            </section>
          )}
          {fillers && (
            <section className="detail-card compact-card">
              <div className="compact-heading"><AudioLines size={17} /><div><span className="eyebrow">HABITS</span><h3>Filler word breakdown</h3></div></div>
              {fillerEntries.length ? <div className="filler-list">{fillerEntries.map(([word, count]) => <div key={word}><span>{word}</span><b>{count}</b></div>)}</div> : <div className="empty-state"><Check size={16} /> No filler words detected.</div>}
            </section>
          )}
          {pauses && (
            <section className="detail-card compact-card">
              <div className="compact-heading"><Pause size={17} /><div><span className="eyebrow">RHYTHM</span><h3>Pause details</h3></div></div>
              <p className="pause-summary">{pauses.pause_count ? `We found ${pauses.pause_count} silent interval${pauses.pause_count === 1 ? "" : "s"}.` : "No significant pauses detected."}</p>
              {pauses.pause_durations_seconds?.length ? <div className="pause-bars">{pauses.pause_durations_seconds.map((duration, index) => <div key={`${duration}-${index}`}><span>Pause {index + 1}</span><i style={{ width: `${Math.min(100, duration * 25)}%` }} /><b>{duration.toFixed(2)}s</b></div>)}</div> : null}
            </section>
          )}
        </div>
      </div>
      <p className="disclaimer"><ShieldCheck size={14} /> Automated feedback is guidance, not an official proficiency score.</p>
    </section>
  );
}

export default function App() {
  const [mode, setMode] = useState<"audio" | "text">("audio");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [preview, setPreview] = useState("");
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<BlobPart[]>([]);
  const start = useRef(0);
  const timer = useRef<number | null>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => () => {
    if (timer.current) clearInterval(timer.current);
    stream.current?.getTracks().forEach((track) => track.stop());
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);

  async function startRec() {
    setError(""); setData(null);
    try {
      const currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.current = currentStream;
      const type = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find((item) => MediaRecorder.isTypeSupported(item));
      const mediaRecorder = type ? new MediaRecorder(currentStream, { mimeType: type }) : new MediaRecorder(currentStream);
      chunks.current = [];
      mediaRecorder.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data); };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks.current, { type: mediaRecorder.mimeType || "audio/webm" });
        const extension = blob.type.includes("mp4") ? "m4a" : "webm";
        setFile(new File([blob], `recording.${extension}`, { type: blob.type }));
        setPreview(URL.createObjectURL(blob));
        currentStream.getTracks().forEach((track) => track.stop());
        stream.current = null;
      };
      recorder.current = mediaRecorder;
      mediaRecorder.start();
      start.current = Date.now(); setElapsed(0); setRecording(true);
      timer.current = window.setInterval(() => setElapsed(Math.floor((Date.now() - start.current) / 1000)), 250);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Microphone permission failed"); }
  }

  function stopRec() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null; recorder.current?.stop(); setRecording(false);
  }

  async function sendAudio() {
    if (!file) return;
    setBusy(true); setError(""); setData(null);
    try {
      const form = new FormData(); form.append("file", file, file.name);
      const response = await fetch(`${API}/transcribe`, { method: "POST", body: form });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
      setData(result);
    } catch (caught) { setError(`${caught instanceof Error ? caught.message : "Request failed"}. API: ${API}`); }
    finally { setBusy(false); }
  }

  async function sendText() {
    setBusy(true); setError(""); setData(null);
    try {
      const response = await fetch(`${API}/analyze-text`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
      setData(result);
    } catch (caught) { setError(`${caught instanceof Error ? caught.message : "Request failed"}. Check the API URL and CORS.`); }
    finally { setBusy(false); }
  }

  function reset() {
    setText(""); setFile(null); setData(null); setError("");
    if (preview) URL.revokeObjectURL(preview);
    setPreview("");
  }

  return <div className="app">
    <header><div className="brand"><span><AudioLines /></span>verba<span className="green">.</span></div><small><i /> API WORKSPACE</small></header>
    <main>
      <section className="hero"><label>YOUR PERSONAL SPEECH LAB</label><h1>Say it. Write it.<br /><em>Understand it.</em></h1><p>Practical feedback on your English: grammar, fluency, pace, pauses and filler words.</p></section>
      <section className="workspace">
        <div className="heading"><div><small>ASSESSMENT WORKSPACE</small><h2>What would you like to analyze?</h2></div><b>01 <span>/ INPUT</span></b></div>
        <nav><button className={mode === "audio" ? "active" : ""} onClick={() => { setMode("audio"); setError(""); setData(null); }}><Mic size={16} /> Voice & audio</button><button className={mode === "text" ? "active" : ""} onClick={() => { setMode("text"); setError(""); setData(null); }}><FileText size={16} /> Written text</button></nav>
        {mode === "audio" ? <div className="panel"><div className="record"><div className="mic"><Mic size={27} /></div><h3>{recording ? "Listening to you…" : file && preview ? "Recording ready" : "Speak naturally"}</h3><p>Record a response or upload an existing audio file.</p>{recording && <div className="live">● REC {String(Math.floor(elapsed / 60)).padStart(2, "0")}:{String(elapsed % 60).padStart(2, "0")}</div>}<div className="buttons">{recording ? <button className="dark" onClick={stopRec}><Square size={15} /> Stop recording</button> : <button className="dark" onClick={startRec}><Mic size={15} /> Start recording</button>}<span>or</span><button onClick={() => input.current?.click()}><Upload size={15} /> Upload audio</button><input ref={input} hidden type="file" accept="audio/*" onChange={(event) => { setFile(event.target.files?.[0] || null); setPreview(""); setData(null); }} /></div></div>{file && <div className="file"><b>{file.name}</b><span>{(file.size / 1048576).toFixed(2)} MB</span>{preview && <audio controls src={preview} />}</div>}<div className="drop" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); setFile(event.dataTransfer.files[0] || null); setPreview(""); setData(null); }}><Upload size={16} /> Drop an audio file here. MP3, WAV, M4A, WebM and OGG supported.</div><div className="bottom"><span><ShieldCheck size={14} /> Sent to your configured backend</span><button className="primary" disabled={!file || busy || recording} onClick={sendAudio}>{busy ? "Analyzing…" : <>Analyze audio <Send size={14} /></>}</button></div></div> : <div className="panel"><div className="text-head"><b><FileText size={16} /> Your writing</b><span>{text.trim() ? text.trim().split(/\s+/).length : 0} words</span></div><textarea rows={9} value={text} onChange={(event) => setText(event.target.value)} placeholder="Write or paste your English text here…" /><p className="hint"><Check size={14} /> Grammar and filler words can be analyzed from text.</p><div className="bottom"><span>Text analysis</span><button className="primary" disabled={!text.trim() || busy} onClick={sendText}>{busy ? "Analyzing…" : <>Analyze text <Send size={14} /></>}</button></div></div>}
      </section>
      {error && <div className="error"><AlertCircle size={18} /><div><b>Analysis failed</b><p>{error}</p></div></div>}
      {data && <ResultsView data={data} />}
      <section className="features"><small>WHAT YOU GET</small><h2>Five lenses on your English</h2><div><article><b>01 / Grammar</b><p>Find possible grammar issues.</p></article><article><b>02 / Fluency</b><p>Review the fluency estimate.</p></article><article><b>03 / Pace</b><p>Understand your WPM.</p></article><article><b>04 / Pauses</b><p>See detected silent intervals.</p></article><article><b>05 / Fillers</b><p>Identify filler words.</p></article></div></section>
      <footer><b>verba<span className="green">.</span></b><span>Built for clearer communication.</span><button onClick={reset}><RotateCcw size={14} /> Reset workspace</button></footer>
    </main>
  </div>;
}
