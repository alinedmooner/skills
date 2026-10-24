---
type: brief
status: active
summary: "Asistente que responde preguntas sobre un recetario familiar de 300 recetas con RAG."
created: 2026-10-01
updated: 2026-10-05
tags: [rag, llm]
---

# recetas-rag

## Objetivo
Responder "¿qué cocino con lo que tengo?" citando la receta exacta.

## Stack
- Base de datos: Postgres 16 con pgvector. Ver [[adr-0001-usar-pgvector]].
- Modelo: `claude-sonnet-5-5`.
- Chunking: una receta por chunk. Ver [[experimento-chunking]].

## Estado
Prototipo en local.

## Enlaces
- Repo del proyecto: `examples/demo-project` (en este mismo repo de realined)
