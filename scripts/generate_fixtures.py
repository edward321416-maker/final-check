"""Generate reproducible synthetic local demo files; never overwrite original user artifacts."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def pdf(path: Path, label: str) -> None:
    stream = f"BT /F1 20 Tf 40 760 Td (FINAL CHECK - SYNTHETIC DEMO) Tj 0 -40 Td ({label}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010} 00000 n \n".encode())
    data.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(data)


for case, duration in (("demo-broken", 12), ("demo-fixed", 8)):
    directory = ROOT / "fixtures" / case
    pdf(directory / "proposal.pdf", "Demo proposal - one page")
    if case == "demo-fixed":
        pdf(directory / "consent.pdf", "Demo consent - fictional sample")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
        "-i", f"testsrc2=size=320x180:rate=10:duration={duration}",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(directory / "clip.mp4"),
    ], check=True)
    print(f"Generated {case}: synthetic PDF + {duration}s silent MP4")
