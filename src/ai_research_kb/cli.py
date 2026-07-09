"""Command-line entry point: ai-research-kb."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .comments import add_comment, check_broken_anchors, list_comments, resolve_comment
from .consistency import run_consistency_check
from .frontmatter import validate_tree
from .models import CommentStatus
from .repo import find_repo_root

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="ai-research-kb: research .md dokümanlarını sorgulanabilir, tutarlı bir bilgi tabanına dönüştürür.",
)
comment_app = typer.Typer(help="Yorum katmanı (<doc>.comments.yaml) işlemleri.")
app.add_typer(comment_app, name="comment")
web_app = typer.Typer(help="Web panel (FastAPI) yönetim işlemleri.")
app.add_typer(web_app, name="web")


def _default_root(root_opt: Path | None) -> Path:
    return root_opt if root_opt is not None else find_repo_root() / "research"


@app.command()
def validate(
    root: Path | None = typer.Option(
        None, "--root", help="Taranacak dizin (varsayılan: <repo>/research)"
    ),
) -> None:
    """Frontmatter şemasını ve yorum anchor'larını doğrula (CI'da fail eden kritik kontrol)."""
    scan_root = _default_root(root)
    results = validate_tree(scan_root)
    has_error = False

    for path, (_fm, issues) in results.items():
        for issue in issues:
            marker = "HATA" if issue.severity == "error" else "UYARI"
            typer.echo(f"[{marker}] {issue.path}: {issue.message}")
            if issue.severity == "error":
                has_error = True

    for path in results:
        for comment_id in check_broken_anchors(path):
            typer.echo(f"[HATA] {path}: kırık yorum anchor'ı (comment id={comment_id})")
            has_error = True

    if not results:
        typer.echo(f"Uyarı: {scan_root} altında .md dosyası bulunamadı.")

    if has_error:
        typer.echo("Doğrulama BAŞARISIZ.")
        raise typer.Exit(code=1)
    typer.echo(f"Doğrulama başarılı ({len(results)} doküman).")


@app.command("check-consistency")
def check_consistency_cmd(
    cluster: str | None = typer.Option(None, "--cluster", help="Tek bir cluster ile sınırla"),
    root: Path | None = typer.Option(None, "--root", help="Taranacak dizin"),
    fmt: str = typer.Option("md", "--format", help="Çıktı formatı: md | json"),
    output: Path | None = typer.Option(None, "--output", help="Raporu dosyaya da yaz"),
) -> None:
    """Tutarlılık & optimizasyon raporu üret (bilgilendirici; build'i düşürmez)."""
    scan_root = _default_root(root)
    report = run_consistency_check(scan_root, cluster=cluster)

    if fmt == "json":
        data = {
            "llm_skipped": report.llm_skipped,
            "findings": [f.__dict__ for f in report.findings],
        }
        text = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        lines = ["# Tutarlılık Raporu", ""]
        if report.llm_skipped:
            lines.append(
                "> Not: LLM yapılandırılmadığı için çelişki adayı (contradiction candidate) "
                "kontrolü atlandı; diğer kontroller normal çalıştı.\n"
            )
        by_cat = report.by_category()
        if not by_cat:
            lines.append("Herhangi bir bulgu yok.")
        for cat, items in by_cat.items():
            lines.append(f"## {cat} ({len(items)})")
            for it in items:
                lines.append(f"- **{it.severity}** [{it.cluster}] `{it.doc}`: {it.message}")
            lines.append("")
        text = "\n".join(lines)

    if output:
        output.write_text(text, encoding="utf-8")
    typer.echo(text)


@comment_app.command("add")
def comment_add(
    doc: Path = typer.Argument(..., help="Doküman yolu (ör. research/x/analiz.md)"),
    anchor: str = typer.Option(..., help="Başlık adı veya dokümandan kısa bir alıntı"),
    body: str = typer.Option(..., help="Yorum metni"),
    author: str = typer.Option(..., help="Yazar"),
) -> None:
    try:
        c = add_comment(doc, anchor, body, author)
    except ValueError as e:
        typer.echo(f"Hata: {e}")
        raise typer.Exit(code=1)
    typer.echo(f"Yorum eklendi: id={c.id}")


@comment_app.command("list")
def comment_list(
    doc: Path = typer.Argument(...),
    status: CommentStatus | None = typer.Option(None, help="open | resolved"),
) -> None:
    for c in list_comments(doc, status):
        typer.echo(f"[{c.status.value}] {c.id} ({c.author}, {c.created}) @ {c.anchor}\n    {c.body}")


@comment_app.command("resolve")
def comment_resolve(doc: Path = typer.Argument(...), comment_id: str = typer.Argument(...)) -> None:
    try:
        resolve_comment(doc, comment_id)
    except ValueError as e:
        typer.echo(f"Hata: {e}")
        raise typer.Exit(code=1)
    typer.echo("Yorum çözümlendi.")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Web panel API'sini başlat (WEB_JWT_SECRET .env'de tanımlı olmalı)."""
    try:
        import uvicorn
    except ImportError:
        typer.echo("Web bağımlılıkları kurulu değil: pip install -e '.[web]'")
        raise typer.Exit(code=1)
    uvicorn.run("ai_research_kb.web.main:app", host=host, port=port, reload=reload)


@web_app.command("create-user")
def web_create_user(
    username: str = typer.Argument(...),
    password: str = typer.Option(
        ..., prompt=True, hide_input=True, confirmation_prompt=True, help="Şifre"
    ),
    role: str = typer.Option("viewer", "--role", help="admin | editor | viewer"),
) -> None:
    """users.yaml içinde bir kullanıcı oluştur/güncelle (idempotent, kullanıcı adına göre)."""
    try:
        from .web.roles import Role
        from .web.users import upsert_user
    except ImportError:
        typer.echo("Web bağımlılıkları kurulu değil: pip install -e '.[web]'")
        raise typer.Exit(code=1)
    try:
        role_enum = Role(role)
    except ValueError:
        typer.echo(f"Geçersiz rol: {role} (admin | editor | viewer)")
        raise typer.Exit(code=1)
    user = upsert_user(username, password, role_enum)
    typer.echo(f"Kullanıcı kaydedildi: {user.username} ({user.role.value})")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
