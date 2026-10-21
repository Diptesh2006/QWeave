# QWeave IEEE Conference Version

This folder contains an IEEE conference-style version of the maintained QWeave manuscript. The scientific content and bounded claims come from `paper/manuscript.tex`; the existing manuscript artifacts are unchanged.

Outputs:

- `docx/QWeave_IEEE_Conference.docx` - editable Word manuscript.
- `pdf/QWeave_IEEE_Conference.pdf` - rendered review copy.
- `pdf/QWeave_IEEE_Conference_Revised.pdf` - externally revised nine-page PDF
  with the supplementary 30-run comparison, retained alongside the
  reproducible repository render for direct comparison.
- `latex/QWeave_IEEE_Conference.tex` - IEEEtran conference source.

The current LaTeX/PDF edition contains 75 cited references, including 25
newly cross-checked primary-paper entries with direct PDF links. It includes
three result figures: aggregate held-out routing costs, the five-seed learning
curves, and the case-level SWAP-distribution/synthetic-fidelity analysis. The
formal-correctness section covers mapping termination, routing legality,
masked-policy legality, supported unitary semantics, fixed-route scheduling,
directed lowering, guarded-route termination, and the independent-error proxy.

`build_ieee.py` and the equation-rendering utilities preserve the earlier
editable Word workflow. The maintained submission source is
`latex/QWeave_IEEE_Conference.tex`; compile that source after prose or
bibliography edits so the review PDF reflects the current 75-reference paper.

Render the equation assets after installing the small Node dependency set:

```powershell
pnpm --dir .\paper\ieee install
pnpm --dir .\paper\ieee run render:math
```

Build all outputs with the bundled or project Python environment:

```powershell
python .\paper\ieee\build_ieee.py
```

On Windows with Microsoft Word installed, export the final PDF from the DOCX
so the two delivered formats have identical pagination:

```powershell
powershell -ExecutionPolicy Bypass -File .\paper\ieee\export_word_pdf.ps1
```

The layout follows the standard IEEE conference conventions: US Letter, two columns, Times-style 10-point body text, Roman-numbered sections, an inline abstract and index terms, compact captions, and references numbered in first-citation order. A selected IEEE conference can impose additional title, copyright, page-limit, author-anonymity, or footer requirements; apply those requirements after selecting the venue.
