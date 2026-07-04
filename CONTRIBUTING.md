# Katkıda Bulunma

Katkılarınız için teşekkürler! Bu proje self-hosted, açık kaynak (MIT) bir
araç olarak geliştiriliyor; hiçbir kurumsal/iç bilgi barındırmamalı — örnekler
her zaman `/examples` altında sentetik olmalı.

## Geliştirme ortamı

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Test ve lint

```bash
pytest
ruff check .
```

PR açmadan önce ikisinin de temiz geçtiğinden emin olun.

## Fazlar

Proje fazlar halinde ilerliyor (Faz 1: yapı/tutarlılık, Faz 2: index/RAG/MCP,
Faz 3: research → task → ClickUp). Bir fazın kapsamı dışına çıkan büyük
özellik önerileri için önce bir issue açıp tartışmanız iyi olur.

## Kod stili

- Yeni bir zorunlu bulut bağımlılığı eklemeyin; her şey self-hosted çalışmalı.
- LLM gerektiren her adım opsiyonel olmalı ve LLM yoksa sessizce atlanmalı.
- Kanonik terimler, beklenen bölümler, blocklist gibi kurum/anlam bağımlı veri
  kod içine değil `config.yaml` şemasına eklenmeli.
- Harici sistemlere (ör. ClickUp) giden mutasyonlar idempotent olmalı ve
  `--dry-run` desteklemeli.

## Pull Request süreci

1. Fork/branch oluşturun.
2. Değişikliğinizi küçük ve odaklı tutun.
3. `pytest` ve `ruff check .` çalıştırın.
4. PR açıklamasında neyi neden değiştirdiğinizi kısaca yazın.
