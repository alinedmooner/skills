---
type: adr
status: active
summary: "Guardamos los embeddings en Postgres con pgvector."
created: 2026-10-05
updated: 2026-10-05
related: ["[[10-projects/recetas-rag/brief]]"]
---

# ADR-0001: Usar pgvector

## Contexto
Necesitamos búsqueda vectorial para 300 recetas.

## Decisión
Postgres 16 + pgvector.

## Consecuencias
Hay que levantar Postgres en local y en producción.
