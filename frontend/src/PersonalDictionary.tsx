import { FormEvent, useEffect, useState } from "react";
import { BookOpen, Plus, Trash2 } from "lucide-react";

type DictionaryEntry = { id: number; word: string };

type Props = { api: string };

export default function PersonalDictionary({ api }: Props) {
  const [entries, setEntries] = useState<DictionaryEntry[]>([]);
  const [word, setWord] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${api}/dictionary`)
      .then(async (response) => {
        if (!response.ok) throw new Error("Could not load your dictionary.");
        setEntries(await response.json());
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load your dictionary."))
      .finally(() => setLoading(false));
  }, [api]);

  async function addWord(event: FormEvent) {
    event.preventDefault();
    const value = word.trim();
    if (!value) {
      setError("Enter a name or word first.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`${api}/dictionary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word: value }),
      });
      if (response.status === 409) throw new Error("That word is already in your dictionary.");
      if (!response.ok) throw new Error("Could not save that word.");
      const entry = await response.json();
      setEntries((current) => [...current, entry].sort((a, b) => a.word.localeCompare(b.word)));
      setWord("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save that word.");
    } finally {
      setSaving(false);
    }
  }

  async function removeWord(id: number) {
    setDeleting(id);
    setError("");
    try {
      const response = await fetch(`${api}/dictionary/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not delete that word.");
      setEntries((current) => current.filter((entry) => entry.id !== id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not delete that word.");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <section className="dictionary detail-card">
      <div className="dictionary-heading">
        <div className="compact-heading">
          <BookOpen size={18} />
          <div>
            <span className="eyebrow">PERSONAL VOCABULARY</span>
            <h3>Personal Dictionary</h3>
          </div>
        </div>
        <span className="dictionary-count">{entries.length} saved</span>
      </div>
      <p className="dictionary-description">Add names, surnames, or important words to help transcription recognize them.</p>
      <form className="dictionary-form" onSubmit={addWord}>
        <input
          value={word}
          onChange={(event) => setWord(event.target.value)}
          placeholder="Add a name or word"
          maxLength={255}
          aria-label="Name or word"
        />
        <button type="submit" disabled={saving || loading}>
          <Plus size={15} />
          {saving ? "Adding..." : "Add Word"}
        </button>
      </form>
      {error && <p className="dictionary-error" role="alert">{error}</p>}
      {loading ? (
        <p className="dictionary-empty">Loading your words...</p>
      ) : entries.length ? (
        <div className="dictionary-list">
          {entries.map((entry) => (
            <div className="dictionary-entry" key={entry.id}>
              <span>{entry.word}</span>
              <button type="button" onClick={() => removeWord(entry.id)} disabled={deleting === entry.id} aria-label={`Delete ${entry.word}`}>
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="dictionary-empty">No saved words yet.</p>
      )}
    </section>
  );
}
