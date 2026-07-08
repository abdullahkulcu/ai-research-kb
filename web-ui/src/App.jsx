import { useState } from "react";
import Login from "./pages/Login.jsx";
import Search from "./pages/Search.jsx";
import DocView from "./pages/DocView.jsx";

const STORAGE_KEY = "ai-research-kb.session";

function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [session, setSession] = useState(loadSession);
  const [openDoc, setOpenDoc] = useState(null); // { cluster, doc } | null

  function handleLogin(session) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    setSession(session);
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY);
    setSession(null);
    setOpenDoc(null);
  }

  if (!session) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="brand">ai-research-kb</span>
        <span className="user-badge">
          {session.username} · <em>{session.role}</em>
        </span>
        <button className="logout-button" onClick={handleLogout}>
          Çıkış yap
        </button>
      </header>

      <main>
        {openDoc ? (
          <DocView
            token={session.token}
            cluster={openDoc.cluster}
            doc={openDoc.doc}
            onBack={() => setOpenDoc(null)}
            onOpenDoc={(cluster, doc) => setOpenDoc({ cluster, doc })}
            onAuthError={handleLogout}
          />
        ) : (
          <Search
            token={session.token}
            onOpenDoc={(cluster, doc) => setOpenDoc({ cluster, doc })}
            onAuthError={handleLogout}
          />
        )}
      </main>
    </div>
  );
}
