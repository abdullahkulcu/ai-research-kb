"""ClickUp push (Faz 2): dry-run preview + idempotent real push.

Every external mutation goes through an explicit dry-run first — this module
never calls the ClickUp API unless dry_run=False. Tasks that already carry a
task_ref are skipped on push (idempotent: re-running never creates duplicates).
Only tasks with status "approved" are ever considered.
"""

from __future__ import annotations

from typing import Any, Protocol

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


class ClickUpError(RuntimeError):
    pass


class _Response(Protocol):
    status_code: int

    def json(self) -> dict: ...
    @property
    def text(self) -> str: ...


class _HttpClient(Protocol):
    def post(self, url: str, *, json: dict, headers: dict) -> _Response: ...


def _real_client() -> _HttpClient:
    try:
        import httpx
    except ImportError as e:
        raise ClickUpError(
            "httpx kurulu değil; gerçek ClickUp push için pip install -e '.[web]' yeterli "
            "olmalı (dry-run bu bağımlılığı gerektirmez)."
        ) from e
    return httpx.Client(timeout=15.0)


def push_tasks(
    tasks: list[dict[str, Any]],
    *,
    list_id: str,
    token: str,
    dry_run: bool,
    http_client: _HttpClient | None = None,
) -> list[dict[str, Any]]:
    """Mutates approved+unpushed tasks in place (sets task_ref/task_url) and
    returns one result row per approved task: {id, title, action, task_ref, task_url}.

    action is one of: "would_create" (dry-run), "created" (real push),
    "skip" (already has a task_ref from a previous push).
    """
    results: list[dict[str, Any]] = []
    owns_client = not dry_run and http_client is None
    client = http_client if http_client is not None else (_real_client() if not dry_run else None)

    try:
        for task in tasks:
            if task.get("status") != "approved":
                continue

            if task.get("task_ref"):
                results.append(
                    {
                        "id": task["id"],
                        "title": task["title"],
                        "action": "skip",
                        "task_ref": task["task_ref"],
                        "task_url": task.get("task_url"),
                    }
                )
                continue

            if dry_run:
                results.append(
                    {
                        "id": task["id"],
                        "title": task["title"],
                        "action": "would_create",
                        "task_ref": None,
                        "task_url": None,
                    }
                )
                continue

            description = (
                f"{task['description']}\n\n"
                f"Kaynak: {task['source_doc']} (bölüm: {task['source_section']})"
            )
            resp = client.post(
                f"{CLICKUP_API_BASE}/list/{list_id}/task",
                json={"name": task["title"], "description": description},
                headers={"Authorization": token, "Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                raise ClickUpError(f"ClickUp hata ({resp.status_code}): {resp.text}")
            data = resp.json()
            task["task_ref"] = str(data["id"])
            task["task_url"] = data.get("url")
            results.append(
                {
                    "id": task["id"],
                    "title": task["title"],
                    "action": "created",
                    "task_ref": task["task_ref"],
                    "task_url": task["task_url"],
                }
            )
    finally:
        if owns_client and client is not None:
            client.close()

    return results
