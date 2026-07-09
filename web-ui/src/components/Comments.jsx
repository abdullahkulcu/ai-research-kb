import { useEffect, useState } from "react";
import { apiFetch, AuthError } from "../api.js";
import { isEditorOrAbove } from "../roles.js";

function CommentItem({ comment, canWrite, onResolve }) {
  return (
    <li className={`comment-item comment-${comment.status}`}>
      <div className="comment-meta">
        <strong>{comment.author}</strong> · <span className="badge">{comment.anchor}</span>{" "}
        · <span className={`badge badge-${comment.status}`}>{comment.status}</span>
      </div>
      <div className="comment-body">{comment.body}</div>
      {canWrite && comment.status === "open" && (
        <button className="link-button" onClick={() => onResolve(comment.id)}>
          Çözümle
        </button>
      )}
      {comment.thread.length > 0 && (
        <ul className="comment-thread">
          {comment.thread.map((reply) => (
            <CommentItem key={reply.id} comment={reply} canWrite={canWrite} onResolve={onResolve} />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function Comments({ token, role, cluster, doc, headings, onAuthError }) {
  const [comments, setComments] = useState(null);
  const [error, setError] = useState(null);
  const [anchor, setAnchor] = useState(headings[0] || "");
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const canWrite = isEditorOrAbove(role);

  function load() {
    apiFetch(`/docs/${cluster}/${doc}/comments`, { token })
      .then(setComments)
      .catch((err) => (err instanceof AuthError ? onAuthError() : setError(err.message)));
  }

  useEffect(() => {
    setComments(null);
    setError(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cluster, doc]);

  async function handleResolve(commentId) {
    try {
      await apiFetch(`/docs/${cluster}/${doc}/comments/${commentId}/resolve`, {
        token,
        method: "POST",
      });
      load();
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch(`/docs/${cluster}/${doc}/comments`, {
        token,
        method: "POST",
        body: { anchor, body },
      });
      setBody("");
      load();
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="comments-section">
      <h3>Yorumlar</h3>
      {error && <div className="error-banner">{error}</div>}
      {!comments && !error && <p className="hint">Yükleniyor…</p>}

      {comments && (
        <ul className="comment-list">
          {comments.length === 0 && <li className="hint">Henüz yorum yok.</li>}
          {comments.map((c) => (
            <CommentItem key={c.id} comment={c} canWrite={canWrite} onResolve={handleResolve} />
          ))}
        </ul>
      )}

      {canWrite ? (
        <form className="comment-form" onSubmit={handleSubmit}>
          <select value={anchor} onChange={(e) => setAnchor(e.target.value)}>
            {headings.length === 0 && <option value="">(başlık yok)</option>}
            {headings.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
          <textarea
            placeholder="Yorumunuz…"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            required
          />
          <button type="submit" disabled={submitting || !body.trim()}>
            {submitting ? "Gönderiliyor…" : "Yorum ekle"}
          </button>
        </form>
      ) : (
        <p className="hint">Yorum eklemek için editor veya admin rolü gerekir.</p>
      )}
    </div>
  );
}
