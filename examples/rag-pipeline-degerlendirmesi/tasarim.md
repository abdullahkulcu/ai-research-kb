---
title: "RAG Pipeline Değerlendirmesi - Tasarım"
cluster: rag-pipeline-degerlendirmesi
status: review
doc_type: design
tags: [rag, embedding, re-ranking]
related_docs: ["analiz.md"]
version: 1
created: 2026-05-11
updated: 2026-05-15
---

# RAG Pipeline Değerlendirmesi - Tasarım

## Özet
Bu doküman, analiz dokümanında (bkz. [analiz](./analiz.md)) tanımlanan sorunlara
yönelik tasarım önerisini içerir.

## Gereksinimler
- Çok dilli (Türkçe + İngilizce) embedding desteği.
- Retrieval sonrası re-ranking adımı.
- Yerel (self-hosted) çalışabilme; bulut zorunluluğu olmamalı.

## Tasarım
Embedding modeli olarak çok dilli bir sentence-transformers modeli kullanılacak.
Retrieval sonrası, opsiyonel bir LLM re-ranking adımı eklenecek; LLM
yapılandırılmamışsa bu adım atlanacak (graceful degradation).

Alternatif olarak tek dilli embedding + query translation değerlendirildi ancak
ek gecikme (latency) getirdiği için reddedildi.

### Adımlar
1. Dokümanları ## başlıklarına göre chunk'la.
2. Her chunk için embedding üret.
3. Sorgu geldiğinde top-k retrieval yap.
4. (Opsiyonel) LLM ile re-ranking uygula.

## Riskler
Çok dilli embedding modelleri bazı dillerde daha düşük kalite verebilir; bu risk
kabul edilebilir olarak değerlendirildi.
