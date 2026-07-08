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
  cli.py          # `ai-research-kb` CLI (typer) — validate, check-consistency,
                  # comment, serve, web create-user
  web/            # opsiyonel FastAPI panel; CLI'yi SARAR, onu değiştirmez
    auth.py, deps.py, roles.py, users.py   # JWT + users.yaml + RBAC hiyerarşisi
    schemas.py                              # REST request/response modelleri
    routers/       # auth, search, docs, comments, consistency, tasks
    services/      # search.py (anahtar kelime, embedding'in yerini tutuyor),
                   # tasks.py (minimal task-plan.yaml çıkarımı/CRUD), clusters.py
```

Kritik (build'i düşüren) kontroller ile bilgilendirici (sadece rapor eden)
kontroller kasıtlı olarak ayrı modüllerde: `frontmatter.py` + `comments.py`
= kritik; `consistency.py` = rapor. Bu ayrımı bozmayın.

`web/` katmanı hakkında önemli noktalar:
- Tamamen opsiyonel (`pip install -e ".[web]"`); kurulu değilse CLI'nin geri
  kalanı etkilenmez (`cli.py`'deki `serve`/`web create-user` komutları içeride
  `import` yapıp `ImportError` durumunda net bir mesajla çıkar).
- `deps.get_app_root()` (gerçek repo kökü — `users.yaml`/`config.yaml` için) ile
  `deps.get_docs_root()` (`config.yaml`'daki `web.docs_root`, taranan dizin)
  bilinçli olarak ayrı tutulur; bunları birbirine karıştırmayın (Faz 1a'da bir
  kez bu yüzden config sessizce built-in default'a düşen bir bug oldu).
- `services/search.py` gerçek bir embedding indeksi DEĞİL, basit anahtar kelime
  araması; imza (query, filters) sabit tutuldu ki gerçek indeks eklendiğinde
  sadece bu dosya değişsin.
- `services/tasks.py`, orijinal Faz 3'teki tam `flow.yaml`/kod-etki-analizi
  planının küçük bir alt kümesidir: sadece yapılandırılmış bir başlık (vars.
  "Yapılacaklar") altındaki numaralı listeleri çıkarır. `generate_tasks` HER
  ZAMAN idempotent ve non-destructive olmalı — var olan task'ları asla silme/
  ezme, sadece yeni (stable id ile) ekle.
- Faz 1a'da tüm uçlar `get_current_user`'a bağlı (geçerli JWT yeterli); rol
  bazlı kısıtlama (`require_role`, `roles.py`'de hazır) henüz hiçbir route'a
  bağlanmadı — bu bilinçli, Faz 1c'nin kapsamı.

## Test / doğrulama

```bash
pip install -e ".[dev,web]"
pytest                                    # tests/ (CLI) + tests/web/ (FastAPI)
ai-research-kb validate --root examples
ai-research-kb check-consistency --root examples
```

`/examples/rag-pipeline-degerlendirmesi/` kasıtlı olarak hem geçerli hem de
tutarlılık kontrollerinin her birini (a-e) tetikleyecek küçük kusurlar içeren
sentetik bir cluster'dır — yeni bir kontrol eklerken önce burada test edin.
`task-plan.yaml` (task-plan servisinin ürettiği dosya) BU CLUSTER'A ASLA
committed EDİLMEMELİ — `index/` gibi türetilmiş/mutasyona uğrayan bir dosyadır;
committed edilirse örnek cluster'ın "temiz başlangıç" varsayımı bozulur ve
`tests/web/test_tasks_api.py`'deki "generate öncesi boş" / "generate sonrası
hepsi proposed" testleri kırılır (bir kere böyle bir hataya düşüldü, tekrar
etmeyin). `tasarim.comments.yaml` farklı: o append-only bir sidecar, committed
kalması güvenli. `tests/web/` testleri zaten kendi disposable kopyalarını
(`writable_client` fixture, `tmp_path`'e kopya) kullanır, gerçek `/examples`'ı
hiç mutasyona uğratmaz.

## Faz durumu

Orijinal doküman-odaklı plan: Faz 1 (yapı/frontmatter/yorum/tutarlılık) tamam.
Bu plan artık bir **web panel** girişimiyle genişliyor (kullanıcı talebi):
CLI-sadece araçtan web-first bir panele geçiş; orijinal Faz 2 (index/RAG/MCP)
ve Faz 3'ün (flow/task/ClickUp) web-native karşılıklarını üretiyor, CLI'yi
silmeden. Alt adımlar (kullanıcının kendi numaralandırması):
- ✅ 1a — Backend scaffold (FastAPI, JWT, `web/` altında yukarıdaki uçlar)
- ⏳ 1b — Frontend skeleton (React: login, arama, doküman görünümü)
- ⏳ 1c — Permission layer (admin/editor/viewer route zorlaması)
- ⏳ Faz 2 (web) — ClickUp entegrasyonu panelden (dry-run → push, idempotent)

Kullanıcı onayı olmadan bir sonraki alt adıma geçmeyin — her adımdan sonra
test + özet + durup onay bekleme kuralı geçerli.
