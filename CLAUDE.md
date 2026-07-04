# CLAUDE.md

Bu dosya, bu repo üzerinde çalışan Claude Code oturumları için bağlam sağlar.

## Proje nedir

`ai-research-kb`: self-hosted, git-native bir araç. Prose ağırlıklı markdown
research/tasarım dokümanlarını AI'ın sorgulayabildiği, kendini tutarlı tutan bir
bilgi tabanına dönüştürür; ileride research'ten flow → task → kod etkisi
üretip ClickUp'a aktarır. Dil: Python. Dokümanlar Türkçe + İngilizce karışık
olabilir.

## Değişmez ilkeler

- **Self-hosted çekirdek**: indeksleme/arama/tutarlılık kontrolü zorunlu bulut
  servisi gerektirmeden çalışmalı. Embedding varsayılan olarak yerel model.
- **LLM her zaman opsiyonel**: `config.yaml`'da `llm.provider` boşsa, LLM
  gerektiren adım sessizce atlanır — hata fırlatmaz, geri kalanı çalışmaya
  devam eder. Bkz. `src/ai_research_kb/llm.py::get_llm_provider`.
- **Kaynak doğruluk = git**: `research/**/*.md`. `index/`, raporlar, task
  planları türetilmiştir ve sıfırdan yeniden üretilebilir olmalı.
- **Harici mutasyona doğrudan atlama yok**: research → ClickUp arasındaki her
  adım repo içinde düzenlenebilir bir dosya üretir; kullanıcı onaylamadan
  harici bir çağrı yapılmaz (Faz 3).
- **Public repo hijyeni**: kod içine hiçbir kurumsal/iç bilgi hardcode edilmez;
  kanonik terimler / beklenen bölümler / blocklist `config.yaml`'dan okunur.
  Örnekler yalnızca `/examples` altında ve sentetiktir.
- **Telemetri yok.**

## Kod yapısı

```
src/ai_research_kb/
  repo.py         # repo kökü bulma, markdown/frontmatter parse, doküman keşfi
  models.py       # pydantic: Frontmatter, Comment, CommentFile
  config.py       # config.yaml -> config.example.yaml -> built-in default zinciri
  frontmatter.py  # KRİTİK doğrulama: şema + cluster/klasör eşleşmesi (CI'da fail eder)
  comments.py     # <doc>.comments.yaml CRUD + anchor doğrulama (CI'da fail eder)
  consistency.py  # bilgilendirici kontroller a-e (CI'yı düşürmez, sadece rapor)
  llm.py          # opsiyonel LLM sağlayıcı arayüzü (Anthropic; graceful degrade)
  cli.py          # `ai-research-kb` CLI (typer)
```

Kritik (build'i düşüren) kontroller ile bilgilendirici (sadece rapor eden)
kontroller kasıtlı olarak ayrı modüllerde: `frontmatter.py` + `comments.py`
= kritik; `consistency.py` = rapor. Bu ayrımı bozmayın.

## Test / doğrulama

```bash
pip install -e ".[dev]"
pytest
ai-research-kb validate --root examples
ai-research-kb check-consistency --root examples
```

`/examples/rag-pipeline-degerlendirmesi/` kasıtlı olarak hem geçerli hem de
tutarlılık kontrollerinin her birini (a-e) tetikleyecek küçük kusurlar içeren
sentetik bir cluster'dır — yeni bir kontrol eklerken önce burada test edin.

## Faz durumu

Faz 1 (bu commit) tamam: yapı, frontmatter, yorum katmanı, tutarlılık raporu,
CI. Faz 2 (index/RAG/MCP) ve Faz 3 (flow/task/ClickUp) henüz başlamadı; kullanıcı
onayı olmadan bu fazların kapsamına girmeyin.
