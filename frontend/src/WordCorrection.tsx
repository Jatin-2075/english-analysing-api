import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { AudioLines, Check, Pencil, X } from "lucide-react";
import "./wordCorrection.css";

type Props = { transcript: string; api: string };

type Previous = { id: number; confirmed_word: string | null };

type Token = { text: string; lead: string; core: string; trail: string; isWord: boolean };

function tokenize(transcript: string): Token[] {
  return transcript.split(/(\s+)/).filter((part) => part !== "").map((part) => {
    if (/^\s+$/.test(part)) return { text: part, lead: "", core: "", trail: "", isWord: false };
    const match = part.match(/^([^\p{L}\p{N}]*)(.*?)([^\p{L}\p{N}]*)$/u);
    const [, lead = "", core = "", trail = ""] = match || [];
    return { text: part, lead, core, trail, isWord: core.length > 0 };
  });
}

export default function WordCorrection({ transcript, api }: Props) {
  const tokens = useMemo(() => tokenize(transcript), [transcript]);
  const [selected, setSelected] = useState<number | null>(null);
  const [corrected, setCorrected] = useState<Record<number, string>>({});
  const [value, setValue] = useState("");
  const [isName, setIsName] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [previous, setPrevious] = useState<Previous[]>([]);

  useEffect(() => { setSelected(null); setCorrected({}); setError(""); }, [transcript]);

  const selectedToken = selected !== null ? tokens[selected] : null;
  const heardWord = selectedToken?.core || "";

  useEffect(() => {
    setPrevious([]);
    if (!heardWord) return;
    let cancelled = false;
    fetch(`${api}/feedback/words/${encodeURIComponent(heardWord)}`)
      .then((response) => (response.ok ? response.json() : []))
      .then((rows: Previous[]) => {
        if (cancelled) return;
        setPrevious(rows);
        const savedWord = rows.find((row) => row.confirmed_word?.trim())?.confirmed_word?.trim();
        if (savedWord) setValue((current) => current.trim() ? current : savedWord);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [heardWord, api]);

  function pick(index: number) {
    setSelected(index);
    setValue(corrected[index] || "");
    setError("");
  }

  function contextAround(index: number) {
    const words = tokens.map((token, i) => ({ token, i })).filter((item) => item.token.isWord);
    const position = words.findIndex((item) => item.i === index);
    return words.slice(Math.max(0, position - 8), position + 9).map((item) => item.token.text).join(" ");
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    const confirmed = value.trim();
    if (selected === null || !heardWord) return;
    if (!confirmed) { setError("Please type the correct spelling."); return; }
    setSaving(true); setError("");
    try {
      const response = await fetch(`${api}/feedback/words`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_word: heardWord,
          suggested_word: null,
          confirmed_word: confirmed,
          accepted: true,
          context: contextAround(selected),
          is_name: isName,
        }),
      });
      if (!response.ok) throw new Error();
      setCorrected((current) => {
        const updated = { ...current };
        tokens.forEach((token, index) => {
          if (token.isWord && token.core.toLowerCase() === heardWord.toLowerCase()) {
            updated[index] = confirmed;
          }
        });
        return updated;
      });
      setSelected(null);
    } catch {
      setError("Could not save your correction. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const savedCount = Object.keys(corrected).length;

  return (
    <article className="transcript wc">
      <b><AudioLines size={15} /> Transcript</b>
      <p className="wc-hint"><Pencil size={12} /> Name or surname heard wrong? Tap the word to correct it.</p>

      <p className="wc-text">
        {tokens.map((token, index) => {
          if (!token.isWord) return token.text;
          const fixed = corrected[index];
          return (
            <span key={index}>
              {token.lead}
              <button
                type="button"
                className={`wc-word${fixed ? " fixed" : ""}${selected === index ? " active" : ""}`}
                onClick={() => pick(index)}
                title={fixed ? `You corrected "${token.core}" to "${fixed}"` : "Tap to correct this word"}
              >
                {fixed || token.core}
              </button>
              {token.trail}
            </span>
          );
        })}
      </p>

      {selectedToken && (
        <form className="wc-panel" onSubmit={save}>
          <div className="wc-panel-head">
            <span>Heard: <strong>{heardWord}</strong></span>
            <button type="button" className="wc-close" onClick={() => setSelected(null)} aria-label="Close"><X size={15} /></button>
          </div>

          <label className="wc-label" htmlFor="wc-input">What should it be?</label>
          <input
            id="wc-input"
            className="wc-input"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="Type the correct spelling"
            maxLength={100}
            autoFocus
          />

          {previous.filter((row) => row.confirmed_word).length > 0 && (
            <div className="wc-previous">
              <small>Corrections saved before:</small>
              <div>
                {Array.from(new Set(previous.map((row) => row.confirmed_word).filter(Boolean) as string[])).slice(0, 5).map((word) => (
                  <button type="button" key={word} onClick={() => setValue(word)} aria-label={`Use correction ${word}`}>{word}</button>
                ))}
              </div>
            </div>
          )}

          <label className="wc-check">
            <input type="checkbox" checked={isName} onChange={(event) => setIsName(event.target.checked)} />
            This is a name or surname
          </label>

          {error && <p className="wc-error" role="alert">{error}</p>}

          <div className="wc-actions">
            <button type="submit" className="wc-save" disabled={saving}>{saving ? "Saving..." : "Save correction"}</button>
            <button type="button" className="wc-cancel" onClick={() => setSelected(null)}>Cancel</button>
          </div>
        </form>
      )}

      {savedCount > 0 && !selectedToken && (
        <p className="wc-saved"><Check size={14} /> {savedCount} correction{savedCount === 1 ? "" : "s"} saved. Thank you, this helps us get names right.</p>
      )}
    </article>
  );
}