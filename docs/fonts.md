# Worksheet Fonts

All arithmetic and spelling scripts default to **Andika Regular** and
accept `--font`. The same face is used for prompts, headings, instructions, and
page numbers. Text wrapping and arithmetic alignment use
that face's actual widths. Changing fonts can change wrapping and pagination.

```sh
# Andika is the default; no font installation or runtime download is needed.
worksheet_venv/bin/python spelling_practice.py --grade 2

# Use the previous face explicitly.
worksheet_venv/bin/python spelling_practice.py --grade 2 --font Helvetica

# Other standard PDF faces work in every script.
worksheet_venv/bin/python mad_minute.py --font Courier

# Load a TrueType font you have permission to embed.
worksheet_venv/bin/python spelling_practice.py --grade 2 \
  --font "/path/to/Verdana.ttf"
```

## Supported Choices

- `Andika`: the bundled Regular face, subset-embedded in generated PDFs.
- Standard PDF font names, including `Helvetica`, `Helvetica-Bold`, `Times-Roman`,
  `Times-Italic`, and `Courier`. These use PDF standard fonts rather than an
  embedded TrueType file.
- A local `.ttf` path, including a quoted path with spaces. Relative paths are
  resolved from the current working directory; `~` is supported.
- For Python callers, a font name already registered with ReportLab.

Names are case-sensitive. System font families are not discovered automatically:
to use Arial, Verdana, or another installed face, supply its actual `.ttf` path.
The project bundles only Andika Regular; other weights can be supplied as font
files. OpenType/CFF, variable-font workflows, font collections, and automatic
bold/italic family selection are not provided by this option. Use a static
TrueType face. Unknown names, unreadable files, and invalid fonts fail instead
of silently substituting another face. Keep input font files distinct from
output destinations.

`--font-size` still controls prompt size: spelling defaults to 22 points and
arithmetic to 20. Writing headings remain 18 points, instructions 12,
and page numbers 10. Changing the typeface does not change these sizes or the
handwriting guide style. Andika was chosen for its literacy-oriented letterforms,
not as a claim of a proven improvement in spelling retention.

## Python API

Both `WritingLayout` and `WorksheetLayout` accept `font_name`, defaulting to
`"Andika"`. The lower-level `wrap_text`, `draw_instructions`, and `draw_problem`
functions also accept `font_name`. Use `resolve_font` to register a supported
face explicitly and obtain its ReportLab name. Font registration is cached in
ReportLab's process-wide registry; keep font files unchanged during a process.

```python
from worksheet import WritingExercise, WritingLayout, generate_writing_pdf

generate_writing_pdf(
    "practice.pdf",
    [WritingExercise("rain"), WritingExercise("train")],
    WritingLayout(font_name="Andika"),
)
```

## Bundled Font

- Font: Andika Regular, version 7.000.
- Copyright: 2004-2025 SIL Global; reserved font names "Andika" and "SIL".
- License: SIL Open Font License 1.1, included verbatim in
  [`worksheet/data/fonts/OFL.txt`](../worksheet/data/fonts/OFL.txt).
- Source: [SIL's Andika downloads](https://software.sil.org/andika/download/).
- Release archive: [Andika-7.000.zip](https://software.sil.org/downloads/r/andika/Andika-7.000.zip).
- Bundled asset: `worksheet/data/fonts/Andika-Regular.ttf`, unmodified from that
  archive. No fonts are fetched at worksheet-generation time.

SHA-256 fingerprints of the downloaded release and bundled file:

```text
Andika-7.000.zip
88ba6ea41ef4a8e5214b090df8fa2983be1babe4843efaa99cdb6078b0e2c070

Andika-Regular.ttf
27484fdc98d0d63f90407f8266e28295f6fb16d2b13c5024df0214f17152919a
```

The OFL permits bundling and PDF embedding; its terms do not impose the font's
license on generated worksheet documents. For other font files, check their
licenses before embedding or redistribution.
