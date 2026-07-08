# ai-research-kb

Self-hosted, git-native bir bilgi tabanı: yoğun, prose ağırlıklı markdown
research/tasarım dokümanlarınızı AI'ın sorgulayabildiği, kendini tutarlı tutan
canlı bir veritabanına dönüştürür. İleriki fazlarda research'ten flow → task →
kod etkisi üretip ClickUp gibi harici bir task sistemine aktarır.

> **English summary:** ai-research-kb is a self-hosted, MIT-licensed tool that
> turns a folder of Markdown research documents into a queryable, self-checking
> knowledge base — with local-first multilingual embeddings, an optional LLM for
> the fuzzy steps, and (in a later phase) a research → flow → task → ClickUp
> pipeline that always goes through an editable file + explicit approval gate.

## Temel ilkeler

- **Self-hosted çekirdek**: indeksleme, arama ve tutarlılık kontrolü hiçbir
  zorunlu bulut servisi olmadan kendi makinenizde/sunucunuzda çalışır.
- **Kaynak doğruluk = git**: `research/` altındaki `.md` dosyaları tek doğruluk
  kaynağıdır. İndeks, raporlar ve task planları türetilmiştir; sıfırdan yeniden
  üretilebilir.
- **LLM opsiyonel**: çelişki adayı tespiti, acceptance criteria ve diff özeti
  gibi adımlar bir LLM sağlayıcısı yapılandırılırsa çalışır; yapılandırılmazsa
  sessizce atlanır (graceful degradation), geri kalan her şey normal çalışır.
- **Harici sisteme asla doğrudan atlama yok**: research'ten ClickUp'a giden her
  adım, repo içinde düzenlenebilir bir dosya üretir; kullanıcı onu düzenler,
  açıkça onaylar, ancak o zaman harici bir mutasyon (idempotent) yapılır.
- **Telemetri yok.**

## Faz durumu

- ✅ **Faz 1** — Yapı, frontmatter şeması, yorum katmanı, tutarlılık kontrolü,
  CI entegrasyonu.
- 🔄 **Web panel** (bu repo şu an burada) — CLI-sadece araçtan web-first bir
  panele geçiş; orijinal Faz 2 (arama/RAG) ve Faz 3'ün (task planı/ClickUp)
  web-native karşılıklarını üretir. Alt adımlar:
  - ✅ **1a — Backend scaffold**: FastAPI, JWT auth, `/research`'ü saran REST
    API'ler (search, get_doc, comments, consistency, minimal task-plan).
  - ⏳ **1b — Frontend skeleton**: React login + arama + doküman görünümü.
  - ⏳ **1c — Permission layer**: admin/editor/viewer rol zorlaması.
  - ⏳ **Faz 2 (web)** — ClickUp entegrasyonu panelden (dry-run → push).
- ⏳ Yerel embedding index / gerçek RAG araması ve MCP server, 1a'daki
  basit anahtar kelime aramasının yerini alacak (bkz. "Bilinen sınırlamalar").

## Kurulum

### Python ile

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp config.example.yaml config.yaml   # zaten repo kökünde bir config.yaml var; isterseniz özelleştirin
cp .env.example .env                 # LLM/ClickUp anahtarları opsiyonel
```

### Docker ile

```bash
docker compose build
touch users.yaml   # ilk çalıştırmadan önce: boş dosya, bind mount için gerekli
docker compose run --rm cli validate --root examples
docker compose up api   # http://localhost:8000 — web panel API'si
```

`docker-compose.yml`, `research/`, `examples/`, `config.yaml`, `index/` ve
`users.yaml`'ı konteynerlere bağlar; kendi dokümanlarınızı `research/` altına
koyduğunuzda ekstra bir adım gerekmez. İki servis var: `cli` (tek seferlik
komutlar için) ve `api` (web panel, sürekli çalışır).

## Doküman yapısı

Her research konusu bir **cluster**'dır (bir klasör), içinde 1 veya daha fazla
`.md` doküman bulunur:

```
research/<cluster>/<doc>.md
research/<cluster>/<doc>.comments.yaml   # yorum katmanı (opsiyonel sidecar)
```

Her `.md` dosyası şu frontmatter alanlarını taşımalıdır:

| Alan | Açıklama |
| --- | --- |
| `title` | Doküman başlığı |
| `cluster` | İçinde bulunduğu klasörle birebir eşleşmeli |
| `status` | `draft` \| `review` \| `final` \| `archived` |
| `doc_type` | `analysis` \| `design` \| `change-plan` \| `notes` \| `other` |
| `tags` | Serbest metin etiket listesi |
| `related_docs` | Diğer dokümanlara göreli path'ler |
| `version` | Tam sayı, varsayılan `1` |
| `created`, `updated` | ISO tarih |
| `task_id`, `task_url` | Opsiyonel, Faz 3'te ClickUp task'ına bağlanır |

Canonik terimler, beklenen bölüm başlıkları, zamana duyarlı ifade kalıpları ve
blocklist tamamen `config.yaml` üzerinden yapılandırılır — repo kodunda hiçbir
kurumsal/iç bilgi hardcoded değildir. `/examples/rag-pipeline-degerlendirmesi/`
altında bu şemanın çalışan, sentetik bir örneği bulunur.

## CLI kullanımı

```bash
# Frontmatter şemasını + yorum anchor'larını doğrula (kritik / CI'da fail eder)
ai-research-kb validate --root examples

# Tutarlılık & optimizasyon raporu (bilgilendirici; build'i düşürmez)
ai-research-kb check-consistency --root examples --format md

# Yorum ekle / listele / çözümle
ai-research-kb comment add examples/rag-pipeline-degerlendirmesi/tasarim.md \
  --anchor "Riskler" --body "Bunu da ölçelim" --author "adiniz"
ai-research-kb comment list examples/rag-pipeline-degerlendirmesi/tasarim.md
ai-research-kb comment resolve examples/rag-pipeline-degerlendirmesi/tasarim.md <comment-id>
```

`--root` verilmezse varsayılan olarak `<repo kökü>/research` taranır.

## Tutarlılık kontrolleri

`check-consistency` şu kontrolleri çalıştırır (hepsi LLM'siz çalışır, sadece
`c` maddesi LLM gerektirir ve yapılandırılmamışsa atlanır):

- **a)** Kırık çapraz referans: `related_docs` ve metin içi `.md` linkleri.
- **b)** Terminoloji tutarsızlığı: `config.yaml`'daki kanonik terimlere göre.
- **c)** *[LLM opsiyonel]* Çelişki adayı: aynı cluster'daki dokümanlar arasında
  — bir hüküm değil, "insan incelesin" işareti.
- **d)** Zamana duyarlı iddia: tarih/beta/GA gibi ifadeler.
- **e)** Yapı/gap: `doc_type`'a göre beklenen bölümlerin eksik olanları.

## Web panel (opsiyonel, `pip install -e ".[web]"`)

CLI'nin yanında, aynı kütüphaneyi (`ai_research_kb`) saran bir FastAPI backend
çalışır — CLI komutları hiçbir şekilde etkilenmez, ikisi yan yana kullanılabilir.

```bash
pip install -e ".[web]"
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # WEB_JWT_SECRET için
# .env içine WEB_JWT_SECRET=<üretilen değer> yazın

ai-research-kb web create-user admin --role admin      # şifre interaktif sorulur
ai-research-kb web create-user ayse --role editor
ai-research-kb web create-user mehmet --role viewer

ai-research-kb serve   # http://127.0.0.1:8000
```

`users.yaml` (repo kökü) `.env` gibi gitignore'dadır; şema için
`users.example.yaml`'a bakın. Roller: `admin` > `editor` > `viewer` (hiyerarşik).

Panelin taradığı dizin `config.yaml`'daki `web.docs_root` ile belirlenir
(varsayılan `research`; demo için `examples` yapılabilir).

### Uçlar (Faz 1a — kimlik doğrulama var, rol zorlaması henüz yok → 1c)

| Uç | Açıklama |
| --- | --- |
| `POST /api/auth/login` | `{username, password}` → JWT + rol |
| `GET /api/auth/me` | Geçerli kullanıcı |
| `GET /api/search?q=&cluster=&status=&doc_type=` | Anahtar kelime araması; sonuçlar `related_docs` içerir |
| `GET /api/clusters`, `GET /api/clusters/{cluster}` | Cluster listesi + çapraz referans haritası |
| `GET /api/docs/{cluster}/{doc}` | Frontmatter + doküman gövdesi |
| `GET/POST /api/docs/{cluster}/{doc}/comments`, `.../resolve` | Yorum katmanını sarar (`comments.py`) |
| `GET /api/consistency?cluster=` | Tutarlılık raporu (a-e), JSON |
| `GET /api/tasks/{cluster}`, `POST .../generate`, `PATCH .../{id}`, `POST .../{id}/approve` | Bkz. "Task planlama (MVP)" |

Tüm uçlar `Authorization: Bearer <token>` ister.

### Task planlama (MVP)

`POST /api/tasks/{cluster}/generate`, cluster'daki dokümanlarda yapılandırılmış
başlık (varsayılan `## Yapılacaklar`) altındaki numaralı listeleri
`<cluster>/task-plan.yaml`'a çıkarır — idempotent (var olan task'ları asla
silmez/ezmez, sadece yenilerini ekler). `PATCH` ile başlık/açıklama/effort
düzenlenebilir, `approve` ile onaylanır. `task-plan.yaml`, `index/` gibi
türetilmiş/mutasyona uğrayan bir dosyadır — `/examples` altında committed
edilmez (aksi halde örnek cluster "temiz başlangıç" özelliğini kaybeder);
`examples/rag-pipeline-degerlendirmesi` üzerinde kendiniz deneyebilirsiniz:

```bash
curl -X POST http://127.0.0.1:8000/api/tasks/rag-pipeline-degerlendirmesi/generate \
  -H "Authorization: Bearer $TOKEN"
```

**Bilinen sınırlamalar (bilinçli MVP kapsamı):** bu, orijinal Faz 3 planındaki
tam `flow.yaml` + bağımlılık çıkarımı + kod etki analizi boru hattı değildir —
sadece numaralı liste çıkarımı. ClickUp push (dry-run + gerçek, idempotent
`task_ref` yazımı) web panel'in **Faz 2**'sinde eklenecek. Arama da gerçek bir
embedding indexi değil, basit anahtar kelime eşleşmesidir; `search_docs()`
imzası sabit tutuldu ki gerçek indeks eklendiğinde API/frontend değişmesin.

## Test

```bash
pytest
```

Testler, `/examples/rag-pipeline-degerlendirmesi/` altındaki sentetik cluster
üzerinde çalışır ve yukarıdaki tüm kontrolleri kapsar (`tests/`: CLI/kütüphane,
`tests/web/`: FastAPI uçları, `httpx`/`TestClient` ile).

## Lisans

MIT — bkz. [LICENSE](./LICENSE).
