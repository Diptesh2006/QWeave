# Manuscript status

`manuscript.tex` is the editable A4, two-column, Times-style source. It now
documents the deterministic path, fixed-route scheduler, wider semantic
checks, directed-coupler lowering, the guarded Gymnasium environment, and the
full benchmark-v2 training and ablation study. The reported result is bounded:
PPO training improves on the untrained policy, while the tested message passing
and learned paths do not improve paired median outcomes over the deterministic
references. The generated Word and PDF copies are kept separately under
`docx/` and `pdf/`. The author order is Atharva Sheersh Pandey, Diptesh Das,
Shrivardhini N, Haridasu Sreedhar, and faculty guide Prof. Bhuvaneswari M.
The current artifacts follow the supplied BERT/ACL-style recreation guide:
A4, two columns, one-inch margins, Times New Roman, compact 11-point body
text, author-year citations, black text, and no visible page numbers. A target
venue and its official template remain to be agreed.
The separate `ieee/` folder contains an IEEE conference-style edition with an
IEEEtran source, editable DOCX, rendered PDF, and reproducible builder. It is
a general IEEE conference layout; conference-specific page limits, headers,
copyright notices, and anonymity rules still take precedence.
The 15 bibliography entries and their supporting claims were checked against
primary records and IBM Quantum documentation on 2026-09-22. The manuscript
also includes formal arguments for mapping-search termination, routing
invariants and supported unitary semantics, fixed-route scheduling,
directed-CNOT lowering, and guarded-route termination. These arguments do not
turn the finite learned-policy experiment into a theorem. See the
[academic audit](../docs/ACADEMIC_AUDIT_2026-09-21.md) and the
[submission checklist](SUBMISSION_CHECKLIST.md).

Install the paper-build dependencies with `pip install -e ".[paper]"`. Build
the editable Word artifact with `python build_docx.py` and the matching PDF
with `python build_pdf.py`. Build the TeX source when a TeX distribution is
available from this folder with
`pdflatex manuscript.tex`, `bibtex manuscript`, and two further `pdflatex`
passes. No TeX engine was available in the local environment, so the repository
PDF is produced directly from the same maintained source and was inspected as
a six-page raster render. The DOCX was regenerated and structurally checked for
the same page, column, typography, color, and content settings.

Before external submission, agree author order and contributions, select the
venue template, review citations against full texts, and obtain an independent
rerun of benchmark v2 on a second clean machine. Device-calibration claims
remain out of scope until a calibration-derived study is frozen and run.
