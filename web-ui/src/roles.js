// Mirrors src/ai_research_kb/web/roles.py — UI-only gating, the real
// enforcement happens server-side (viewer gets a 403 either way).
export const isEditorOrAbove = (role) => role === "editor" || role === "admin";
