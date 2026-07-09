import pytest

from ai_research_kb.web.services.clickup import ClickUpError, push_tasks


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, *, json, headers):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.responses.pop(0)

    def close(self):
        pass


def make_task(**overrides):
    task = {
        "id": "t1",
        "title": "Test task",
        "description": "desc",
        "source_doc": "cluster/doc.md",
        "source_section": "Yapılacaklar",
        "effort": "M",
        "depends_on": [],
        "status": "approved",
        "task_ref": None,
        "task_url": None,
    }
    task.update(overrides)
    return task


def test_dry_run_previews_approved_unpushed_tasks():
    tasks = [make_task(id="t1"), make_task(id="t2", status="proposed")]
    results = push_tasks(tasks, list_id="123", token="tok", dry_run=True)
    assert len(results) == 1
    assert results[0]["action"] == "would_create"
    assert tasks[0]["task_ref"] is None  # dry-run never mutates


def test_dry_run_skips_already_pushed_tasks():
    tasks = [make_task(task_ref="existing-ref", task_url="https://app.clickup.com/t/existing-ref")]
    results = push_tasks(tasks, list_id="123", token="tok", dry_run=True)
    assert results[0]["action"] == "skip"
    assert results[0]["task_ref"] == "existing-ref"


def test_real_push_creates_and_mutates_tasks_in_place():
    tasks = [make_task(id="t1")]
    fake = FakeClient([FakeResponse(200, {"id": 999, "url": "https://app.clickup.com/t/999"})])
    results = push_tasks(tasks, list_id="123", token="tok", dry_run=False, http_client=fake)

    assert results[0]["action"] == "created"
    assert tasks[0]["task_ref"] == "999"
    assert tasks[0]["task_url"] == "https://app.clickup.com/t/999"
    assert fake.calls[0]["headers"]["Authorization"] == "tok"
    assert "list/123/task" in fake.calls[0]["url"]


def test_real_push_is_idempotent_on_rerun():
    tasks = [make_task(id="t1")]
    fake = FakeClient([FakeResponse(200, {"id": 999, "url": "https://x/999"})])
    push_tasks(tasks, list_id="123", token="tok", dry_run=False, http_client=fake)

    fake2 = FakeClient([])
    results = push_tasks(tasks, list_id="123", token="tok", dry_run=False, http_client=fake2)
    assert results[0]["action"] == "skip"
    assert fake2.calls == []


def test_real_push_raises_on_http_error():
    tasks = [make_task(id="t1")]
    fake = FakeClient([FakeResponse(401, text="unauthorized")])
    with pytest.raises(ClickUpError):
        push_tasks(tasks, list_id="123", token="bad", dry_run=False, http_client=fake)


def test_non_approved_tasks_are_never_pushed():
    tasks = [make_task(id="t1", status="proposed")]
    fake = FakeClient([])
    results = push_tasks(tasks, list_id="123", token="tok", dry_run=False, http_client=fake)
    assert results == []
    assert fake.calls == []
