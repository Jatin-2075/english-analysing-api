import { useState } from "react";
import { Check, Star } from "lucide-react";
import "./wordCorrection.css";

type Props = { api: string; assessmentId?: string; score?: number };

export default function RatingFeedback({ api, assessmentId, score }: Props) {
  const [rating, setRating] = useState(0);
  const [reason, setReason] = useState("");
  const [state, setState] = useState<"idle" | "saving" | "done" | "error">("idle");

  if (!assessmentId) return null;

  async function submit() {
    if (!rating) return;
    setState("saving");
    try {
      const response = await fetch(`${api}/feedback/assessments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assessment_id: assessmentId,
          rating,
          original_score: score ?? null,
          reason: reason.trim() || null,
        }),
      });
      if (!response.ok) throw new Error();
      setState("done");
    } catch {
      setState("error");
    }
  }

  if (state === "done") {
    return <section className="detail-card rf"><p className="wc-saved"><Check size={14} /> Thanks for your feedback.</p></section>;
  }

  return (
    <section className="detail-card rf">
      <span className="eyebrow">YOUR FEEDBACK</span>
      <h3>How accurate was this assessment?</h3>
      <div className="rf-stars" role="radiogroup" aria-label="Rating">
        {[1, 2, 3, 4, 5].map((value) => (
          <button
            type="button"
            key={value}
            role="radio"
            aria-checked={rating === value}
            aria-label={`${value} star${value === 1 ? "" : "s"}`}
            className={value <= rating ? "on" : ""}
            onClick={() => setRating(value)}
          >
            <Star size={22} fill={value <= rating ? "currentColor" : "none"} />
          </button>
        ))}
      </div>
      {rating > 0 && (
        <>
          <textarea
            className="wc-input"
            rows={2}
            maxLength={500}
            placeholder="Anything we got wrong? (optional)"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
          {state === "error" && <p className="wc-error" role="alert">Could not send feedback. Please try again.</p>}
          <div className="wc-actions">
            <button type="button" className="wc-save" disabled={state === "saving"} onClick={submit}>
              {state === "saving" ? "Sending..." : "Send feedback"}
            </button>
          </div>
        </>
      )}
    </section>
  );
}