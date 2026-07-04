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
  CI entegrasyonu. (Bu repo şu an burada.)
- ⏳ **Faz 2** — Yerel embedding index, RAG araması, MCP server.
- ⏳ **Faz 3** — Research → flow → task planı → kod etki analizi → ClickUp.

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
docker compose run --rm ai-research-kb validate --root examples
```

`docker-compose.yml`, `research/`, `examples/`, `config.yaml` ve `index/`
dizinlerini konteynere bağlar; kendi dokümanlarınızı `research/` altına
koyduğunuzda ekstra bir adım gerekmez.

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

## Test

```bash
pytest
```

Testler, `/examples/rag-pipeline-degerlendirmesi/` altındaki sentetik cluster
üzerinde çalışır ve yukarıdaki tüm kontrolleri kapsar.

## Lisans

MIT — bkz. [LICENSE](./LICENSE).
