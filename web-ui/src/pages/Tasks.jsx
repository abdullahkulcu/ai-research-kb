import { useEffect, useState } from "react";
import { apiFetch, AuthError } from "../api.js";
import { isEditorOrAbove } from "../roles.js";

export default function Tasks({ token, role, onAuthError }) {
  const [clusters, setClusters] = useState([]);
  const [cluster, setCluster] = useState("");
  const [tasks, setTasks] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const canWrite = isEditorOrAbove(role);

  useEffect(() => {
    apiFetch("/clusters", { token })
      .then((data) => {
        setClusters(data);
        if (data.length > 0) setCluster(data[0].cluster);
      })
      .catch((err) => (err instanceof AuthError ? onAuthError() : setError(err.message)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadTasks(c) {
    if (!c) return;
    setTasks(null);
    apiFetch(`/tasks/${c}`, { token })
      .then(setTasks)
      .catch((err) => (err instanceof AuthError ? onAuthError() : setError(err.message)));
  }

  useEffect(() => {
    loadTasks(cluster);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cluster]);

  async function handleGenerate() {
    setBusy(true);
    setError(null);
    try {
      await apiFetch(`/tasks/${cluster}/generate`, { token, method: "POST" });
      loadTasks(cluster);
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleApprove(taskId) {
    try {
      await apiFetch(`/tasks/${cluster}/${taskId}/approve`, { token, method: "POST" });
      loadTasks(cluster);
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    }
  }

  async function handleEdit(task) {
    const title = window.prompt("Başlık:", task.title);
    if (title === null) return;
    try {
      await apiFetch(`/tasks/${cluster}/${task.id}`, {
        token,
        method: "PATCH",
        body: { title },
      });
      loadTasks(cluster);
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    }
  }

  async function handleClickUpPush() {
    setError(null);
    try {
      const preview = await apiFetch(`/tasks/${cluster}/clickup/push`, {
        token,
        method: "POST",
        body: { dry_run: true },
      });
      const toCreate = preview.filter((r) => r.action === "would_create");
      const alreadyPushed = preview.filter((r) => r.action === "skip");

      if (toCreate.length === 0) {
        window.alert(
          alreadyPushed.length > 0
            ? "Onaylanmış tüm task'lar zaten ClickUp'a gönderilmiş."
            : "Onaylanmış (approved) ve gönderilmemiş task yok."
        );
        return;
      }

      const lines = [
        `${toCreate.length} task ClickUp'a oluşturulacak:`,
        ...toCreate.map((r) => `- ${r.title}`),
      ];
      if (alreadyPushed.length > 0) {
        lines.push(`(${alreadyPushed.length} task zaten gönderilmiş, atlanacak)`);
      }
      lines.push("", "Devam edilsin mi?");
      if (!window.confirm(lines.join("\n"))) return;

      const result = await apiFetch(`/tasks/${cluster}/clickup/push`, {
        token,
        method: "POST",
        body: { dry_run: false },
      });
      const createdCount = result.filter((r) => r.action === "created").length;
      window.alert(`${createdCount} task ClickUp'a oluşturuldu.`);
      loadTasks(cluster);
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
      else setError(err.message);
    }
  }

  return (
    <div className="tasks-page">
      <div className="tasks-toolbar">
        <select value={cluster} onChange={(e) => setCluster(e.target.value)}>
          {clusters.map((c) => (
            <option key={c.cluster} value={c.cluster}>
              {c.cluster}
            </option>
          ))}
        </select>
        {canWrite ? (
          <>
            <button onClick={handleGenerate} disabled={busy || !cluster}>
              {busy ? "Oluşturuluyor…" : "Yeniden oluştur"}
            </button>
            <button onClick={handleClickUpPush} disabled={!cluster}>
              ClickUp'a Gönder
            </button>
          </>
        ) : (
          <span className="hint">Task oluşturmak/onaylamak için editor+ rolü gerekir.</span>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}
      {tasks === null && !error && <p className="hint">Yükleniyor…</p>}

      {tasks && tasks.length === 0 && (
        <p className="hint">
          Henüz task yok. {canWrite && '"Yeniden oluştur" ile dokümanlardaki "## Yapılacaklar" listelerinden çıkarın.'}
        </p>
      )}

      {tasks && tasks.length > 0 && (
        <table className="tasks-table">
          <thead>
            <tr>
              <th>Başlık</th>
              <th>Durum</th>
              <th>Effort</th>
              <th>Bağımlılıklar</th>
              <th>Kaynak</th>
              <th>ClickUp</th>
              {canWrite && <th></th>}
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>{t.title}</td>
                <td>
                  <span className={`badge badge-${t.status}`}>{t.status}</span>
                </td>
                <td>{t.effort || "—"}</td>
                <td>{t.depends_on.length ? t.depends_on.join(", ") : "—"}</td>
                <td className="tasks-source">{t.source_doc}</td>
                <td>
                  {t.task_url ? (
                    <a href={t.task_url} target="_blank" rel="noreferrer">
                      #{t.task_ref}
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
                {canWrite && (
                  <td className="tasks-actions">
                    <button className="link-button" onClick={() => handleEdit(t)}>
                      Düzenle
                    </button>
                    {t.status === "proposed" && (
                      <button className="link-button" onClick={() => handleApprove(t.id)}>
                        Onayla
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
