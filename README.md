# realined

**Tu segundo cerebro, realineado cada noche por un agente en la nube de Claude.**

realined es un juego de palabras con *realigned* (realineado) y con alined, su autor.
Es un agente de [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)
que mantiene un segundo cerebro en Markdown + Git mientras duermes:

- Procesa lo que capturaste: textos, recortes web, PDFs, imágenes y transcripciones.
- Repara la estructura: frontmatter, enlaces rotos, etiquetas duplicadas y notas huérfanas.
- Una vez por semana comprueba que tu contexto sigue diciendo la verdad sobre el código del proyecto.

Todo llega como **un pull request por ejecución**: tú decides qué se queda.

## Por qué

Un segundo cerebro pensado para LLMs se degrada solo: el inbox crece, los datos de precios
caducan, las decisiones dejan de coincidir con el código. El patrón **LLM Wiki** de Karpathy
(fuentes crudas inmutables → wiki mantenido por el LLM → esquema en `AGENTS.md`, con las
operaciones *ingest*, *query* y *lint*) resuelve eso. realined lo ejecuta de forma automática en
la nube, sobre una estructura **PARA**, con estas reglas de seguridad:

- Nunca borra nada.
- Nunca toca tus fuentes crudas (`30-resources/raw/`).
- Nunca escribe en `main`.
- Cita la fuente de todo lo que escribe.

## Qué hay en este repo

```
realined/
├── skills/                    # Agent Skills (SKILL.md), portables: nube y Claude Code
│   ├── realined-ingest/       # fuentes crudas → notas fuente citadas → wiki
│   ├── realined-lint/         # chequeo + arreglos seguros (scripts/lint.py, sin dependencias)
│   └── realined-review/       # revisión semanal: índice, briefs, contexto vs. código, inbox
├── templates/vault/           # plantilla de segundo cerebro: PARA, AGENTS.md, index, log, plantillas
├── examples/                  # vault y proyecto FICTICIOS con fallos sembrados para probar
├── agent/BRIEF.md             # diseño del agente para crearlo con managed-agents-wizard
└── scripts/check.py           # comprueba las invariantes de AGENTS.md (también en CI)
```

## Empezar

**1. Crea tu segundo cerebro** (o adapta el tuyo) desde la plantilla:

```sh
cp -r templates/vault ~/mi-cerebro && cd ~/mi-cerebro && git init
```

Ajusta `AGENTS.md`: tus carpetas, tu taxonomía de etiquetas y lo que el agente puede mover.

**2. Prueba las skills en local** con Claude Code, antes de pagar nada en la nube:

```sh
mkdir -p ~/.claude/skills && ln -s "$PWD"/skills/realined-* ~/.claude/skills/
python3 skills/realined-lint/scripts/lint.py examples/demo-vault --today 2026-10-24
python3 scripts/check.py   # invariantes del repo: 7 comprobaciones, sin dependencias
```

Luego, dentro de `examples/demo-vault`, pídele a Claude Code: "haz lint del vault" o "procesa
las fuentes nuevas".

**3. Crea el agente en la nube** con la skill
[managed-agents-wizard](https://github.com/JairoTorregrosa/jaiskills/tree/main/skills/models/managed-agents-wizard)
de Jairo Torregrosa y la CLI `ant`:

> Usa managed-agents-wizard con agent/BRIEF.md: crea el agente realined en Managed Agents.

El wizard confirma cada capa contigo y escribe `agents/realined/`. Después lo aplica con
`ant apply`, hace una prueba con tope de costo sobre el vault de ejemplo y te explica la traza.
Al final lo programa.

## Hoja de ruta

| Versión | Qué añade |
|---|---|
| v0 | Una Session de prueba sobre el vault de ejemplo, "dry run", tope de USD 3 |
| v1 | Pull requests reales en un repo privado de prueba |
| v2 | Ejecución nocturna (Deployment) + memoria de lo ya procesado |
| v3 | Revisión semanal comparando el contexto con el código del proyecto |
| v4 | Disparo por evento (GitHub Action al subir capturas) y tu vault real |

## Seguridad y privacidad

- **Token:** el agente usa un token *fine-grained* de GitHub que solo ve tu vault (y el repo del
  proyecto en modo lectura). Lo guardas en un vault de Managed Agents y nunca pasa por el chat.
- **Red cerrada:** sin acceso a la web (`networking: limited`, sin `web_search`/`web_fetch`).
  Tus notas solo viajan al modelo que las procesa.
- **Las notas son datos:** el texto de tus notas nunca se trata como instrucciones. El vault de
  ejemplo incluye una instrucción inyectada a propósito para comprobarlo.
- **Sin secretos en el vault:** nada de claves en notas ni snippets. El linter las busca y te
  pide rotarlas.
- **Repo público, datos ficticios:** este repo solo debe contener datos ficticios. Tu vault real
  va en un repo privado aparte.

## Créditos

- Estructura de skills y método de construcción del agente:
  [jaiskills](https://github.com/JairoTorregrosa/jaiskills) de Jairo Torregrosa.
- Patrón LLM Wiki: [Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
- PARA y CODE: [Tiago Forte](https://fortelabs.com/blog/why-para-is-the-key-to-the-ai-era/).
- Estándares: [AGENTS.md](https://agents.md/) y Agent Skills (`SKILL.md`).

## Licencia

MIT.
