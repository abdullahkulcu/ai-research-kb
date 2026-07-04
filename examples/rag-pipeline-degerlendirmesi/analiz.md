---
title: "RAG Pipeline Değerlendirmesi - Analiz"
cluster: rag-pipeline-degerlendirmesi
status: final
doc_type: analysis
tags: [rag, retrieval, embedding]
related_docs: []
version: 1
created: 2026-05-01
updated: 2026-05-10
---

# RAG Pipeline Değerlendirmesi - Analiz

## Özet
Bu doküman, mevcut retrieval-augmented generation (RAG) pipeline'ının performansını
değerlendirir ve iyileştirme alanlarını tanımlar.

## Bağlam
Sistem şu anda tek dilli bir embedding modeli kullanıyor. Kullanıcılarımızın önemli
bir kısmı Türkçe ve İngilizce karışık sorgular soruyor, bu da retrieval kalitesini
düşürüyor.

Büyük dil modeli çağrıları, retrieval sonrası yeniden sıralama için kullanılmıyor;
bu nedenle bazı alakasız chunk'lar üst sıralarda kalabiliyor.

## Bulgular
- Çok dilli sorgularda recall@10 belirgin şekilde düşüyor.
- Chunk boyutu çok büyük tutulduğunda (>1000 token) alaka düzeyi düşüyor.
- LLM tabanlı re-ranking, GA olmadığı için beta olarak değerlendirilmeli.

## Sonuç
Çok dilli embedding modeline geçiş ve retrieval sonrası re-ranking adımı eklenmesi
öneriliyor. Detaylar için bkz. [tasarım dokümanı](./tasarim.md).
