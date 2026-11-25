"""Convertit un .md en .html imprimable (puis Chrome headless -> PDF)."""
import sys, markdown
from pathlib import Path
src = Path(sys.argv[1]); titre = sys.argv[2]
corps = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"])
css = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 17pt; margin: 0 0 6pt; } h2 { font-size: 13pt; margin: 16pt 0 4pt; border-bottom: 1px solid #ccc; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; } p, li { margin: 3pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 3pt 5pt; text-align: left; vertical-align: top; } th { background: #eee; }
hr { border: 0; border-top: 1px solid #ccc; } code { font-size: 9pt; }
"""
src.with_suffix(".html").write_text(f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{titre}</title><style>{css}</style></head><body>{corps}</body></html>', encoding="utf-8")
