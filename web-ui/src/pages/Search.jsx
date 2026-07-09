import { useEffect, useState } from "react";
import { apiFetch, AuthError } from "../api.js";

export default function Search({ token, onOpenDoc, onAuthError }) {
  const [clusters, setClusters] = useState([]);
  const [query, setQuery] = useState("");
  const [cluster, setCluster] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch("/clusters", { token })
      .then(setClusters)
      .catch((err) => (err instanceof AuthError ? onAuthError() : setError(err.message)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runSearch(e) {
    e?.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const params = new URLSearchParams({ q: query });
      if (cluster) params.set("cluster", cluster);
      const data = await apiFetch(`/search?${params.toString()}`, { token });
      setResults(data.results);
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="search-page">
      <form className="search-bar" onSubmit={runSearch}>
        <input
          placeholder="Ara… (ör. embedding, re-ranking)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <select value={cluster} onChange={(e) => setCluster(e.target.value)}>
          <option value="">Tüm cluster'lar</option>
          {clusters.map((c) => (
            <option key={c.cluster} value={c.cluster}>
              {c.cluster} ({c.doc_count})
            </option>
          ))}
        </select>
        <button type="submit" disabled={loading}>
          {loading ? "Aranıyor…" : "Ara"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {results === null && !error && (
        <p className="hint">
          Bir sorgu girin veya boş bırakıp "Ara"ya basarak bir cluster'daki tüm
          dokümanları listeleyin.
        </p>
      )}

      {results !== null && (
        <ul className="result-list">
          {results.length === 0 && <li className="hint">Sonuç bulunamadı.</li>}
          {results.map((r) => (
            <li key={r.doc} className="result-item" onClick={() => onOpenDoc(r.cluster, r.doc.split("/").pop())}>
              <div className="result-title">{r.title}</div>
              <div className="result-meta">
                {r.cluster} · <code>{r.doc}</code>
              </div>
              <div className="result-snippet">{r.snippet}</div>
              {r.related_docs.length > 0 && (
                <div className="result-related">İlgili: {r.related_docs.join(", ")}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
