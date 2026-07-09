import { useEffect, useState } from "react";
import { apiFetch, AuthError } from "../api.js";
import Comments from "../components/Comments.jsx";
import { parseBlocks } from "../markdown.js";

const headingTag = (level) => `h${Math.min(level + 1, 6)}`;

function Block({ block, index }) {
  if (block.type === "heading") {
    const Tag = headingTag(block.level);
    return <Tag key={index}>{block.text}</Tag>;
  }
  if (block.type === "ul") {
    return (
      <ul key={index}>
        {block.items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    );
  }
  if (block.type === "ol") {
    return (
      <ol key={index}>
        {block.items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ol>
    );
  }
  return <p key={index}>{block.text}</p>;
}

export default function DocView({ token, role, cluster, doc, onBack, onOpenDoc, onAuthError }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    apiFetch(`/docs/${cluster}/${doc}`, { token })
      .then(setData)
      .catch((err) => (err instanceof AuthError ? onAuthError() : setError(err.message)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cluster, doc]);

  return (
    <div className="doc-view">
      <button className="back-button" onClick={onBack}>
        ← Aramaya dön
      </button>

      {error && <div className="error-banner">{error}</div>}
      {!data && !error && <p className="hint">Yükleniyor…</p>}

      {data && (
        <>
          <h1>{data.title}</h1>
          <table className="frontmatter-table">
            <tbody>
              <tr>
                <th>cluster</th>
                <td>{data.cluster}</td>
              </tr>
              <tr>
                <th>status</th>
                <td>
                  <span className={`badge badge-${data.status}`}>{data.status}</span>
                </td>
              </tr>
              <tr>
                <th>doc_type</th>
                <td>{data.doc_type}</td>
              </tr>
              <tr>
                <th>tags</th>
                <td>{data.tags.join(", ") || "—"}</td>
              </tr>
              <tr>
                <th>related_docs</th>
                <td>
                  {data.related_docs.length === 0
                    ? "—"
                    : data.related_docs.map((rel) => (
                        <button
                          key={rel}
                          className="link-button"
                          onClick={() => onOpenDoc(cluster, rel)}
                        >
                          {rel}
                        </button>
                      ))}
                </td>
              </tr>
              <tr>
                <th>version</th>
                <td>{data.version}</td>
              </tr>
              <tr>
                <th>created / updated</th>
                <td>
                  {data.created} / {data.updated}
                </td>
              </tr>
            </tbody>
          </table>

          <div className="doc-body">
            {parseBlocks(data.body)
              // the body's own leading "# Title" duplicates the h1 above when it
              // repeats the frontmatter title, as our example docs do
              .filter((block, i) => !(i === 0 && block.type === "heading" && block.level === 1 && block.text === data.title))
              .map((block, i) => (
                <Block key={i} block={block} index={i} />
              ))}
          </div>

          <Comments
            token={token}
            role={role}
            cluster={cluster}
            doc={doc}
            headings={parseBlocks(data.body)
              .filter((b) => b.type === "heading")
              .map((b) => b.text)}
            onAuthError={onAuthError}
          />
        </>
      )}
    </div>
  );
}
