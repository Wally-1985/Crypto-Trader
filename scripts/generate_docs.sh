#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p docs/pdf

python3 - <<'PY'
from pathlib import Path
import textwrap

root = Path.cwd()
source_to_pdf = {
    "First Installation.md": "First Installation.pdf",
    "Installation Guide.md": "Installation Guide.pdf",
    "User Guide.md": "User Guide.pdf",
    "ASVS Audit Template.md": "ASVS Audit v0.1.0-dev.pdf",
}

def esc_pdf(text: str) -> str:
    return text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')

def markdown_to_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.replace('`', '')
        if line.startswith('#'):
            line = line.lstrip('#').strip().upper()
        wrapped = textwrap.wrap(line, width=88) or ['']
        lines.extend(wrapped)
    return lines

def write_pdf(lines: list[str], path: Path) -> None:
    pages = []
    per_page = 48
    for i in range(0, len(lines), per_page):
        page_lines = lines[i:i + per_page]
        content = ['BT', '/F1 10 Tf', '50 790 Td', '14 TL']
        for line in page_lines:
            content.append(f'({esc_pdf(line)}) Tj T*')
        content.append('ET')
        pages.append('\n'.join(content).encode())

    objects: list[bytes] = []
    objects.append(b'<< /Type /Catalog /Pages 2 0 R >>')
    kids_refs = ' '.join(f'{4 + idx*2} 0 R' for idx in range(len(pages)))
    objects.append(f'<< /Type /Pages /Kids [{kids_refs}] /Count {len(pages)} >>'.encode())
    objects.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
    for idx, stream in enumerate(pages):
        page_obj_num = 4 + idx*2
        stream_obj_num = page_obj_num + 1
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_obj_num} 0 R >>'.encode())
        objects.append(b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream')

    out = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for num, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f'{num} 0 obj\n'.encode())
        out.extend(obj)
        out.extend(b'\nendobj\n')
    xref = len(out)
    out.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f\n'.encode())
    for offset in offsets[1:]:
        out.extend(f'{offset:010d} 00000 n\n'.encode())
    out.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    path.write_bytes(out)

for src, pdf in source_to_pdf.items():
    source_path = root / 'docs/source' / src
    pdf_path = root / 'docs/pdf' / pdf
    lines = markdown_to_lines(source_path.read_text())
    write_pdf(lines, pdf_path)
    print(f'generated {pdf_path}')
PY
