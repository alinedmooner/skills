# media.md — how to read each kind of source

One row per file type found in `30-resources/raw/` or `00-inbox/`. The source note format is
`source-note.md`. When a type cannot be read in this environment, write the source note anyway
with `status: draft`, the field `needs:` and what is missing, so the person sees it in the report.

| Type | Extensions | Read it with | Put in the source note |
|---|---|---|---|
| Markdown, text, web clip | `.md` `.txt` `.html` | The `read` tool | Summary, key claims with the quote location, links found, author and date if present |
| PDF | `.pdf` | The `pdf` skill (Anthropic prebuilt) when attached; else `pdftotext` if installed | Summary, outline of sections with page numbers, figures and tables that matter |
| Image, screenshot, whiteboard | `.png` `.jpg` `.jpeg` `.webp` `.gif` | The `read` tool. Not yet verified in Managed Agents: if it returns no image content, write `needs: vision`. Large images: describe the whole, then the regions that hold text | What it shows, all readable text (OCR) verbatim in a block, diagrams as a list of boxes and arrows, what it is evidence of |
| Audio | `.m4a` `.mp3` `.wav` `.ogg` | Look first for a transcript next to it (`<name>.txt`, `<name>.vtt`, `<name>.srt`). The model cannot listen. | From the transcript: summary, decisions, actions with owner and date, open questions, speakers. With no transcript: `needs: transcript` |
| Video | `.mp4` `.mov` `.webm` | Same as audio: a transcript or subtitles next to it | Same as audio; `needs: transcript` when absent |
| Prompt | `.md` `.txt` in `40-prompts/` or a capture that holds a prompt | The `read` tool | Move to `40-prompts/` as `type: prompt` with `version`, `models_tested`, `inputs`, `output_format`; separate the template (`{{variables}}`) from few-shot examples |
| Spreadsheet, CSV | `.csv` `.xlsx` | `read` for CSV; the `xlsx` skill when attached | Columns, row count, what one row means, 3 example rows with no personal data |
| Anything else | | Do not open binaries with unknown types | `needs: a reader for .<ext>` |

## Audio transcription inside the sandbox (optional, not verified)

A transcription tool inside the Managed Agents sandbox (for example `faster-whisper`) needs
`allow_package_managers: true`, a host to download the model weights in `allowed_hosts`, and
more session time (billed per running hour). Nobody has tested this layer for realined yet. Until
it is tested, transcribe on the person's computer and commit the `.txt` next to the audio. Before
you add it to an agent, read the Environment page in the official docs and measure one run.

## Privacy

- Audio and images often hold third-party faces, voices and personal data. Write what matters
  for the work; do not copy personal identifiers into notes (phone numbers, IDs, addresses).
- A source with `sensitivity: private` stays out of summaries in shared files (`index.md`,
  reviews); link it instead.
