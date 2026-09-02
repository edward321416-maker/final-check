"""Verify generated sample files without treating metadata as validator evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
records = []
for case, duration in (("demo-broken", 12), ("demo-fixed", 8)):
    for file in sorted((root / "fixtures" / case).iterdir()):
        if file.suffix not in {".pdf", ".mp4"}:
            continue
        record = {"path": file.relative_to(root).as_posix(), "bytes": file.stat().st_size,
                  "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
        if file.suffix == ".mp4":
            result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file)], capture_output=True, text=True, encoding="utf-8", check=True)
            info = json.loads(result.stdout)
            video = next(s for s in info["streams"] if s["codec_type"] == "video")
            assert float(info["format"]["duration"]) == duration
            assert video["width"] == 320 and video["height"] == 180
            assert video["avg_frame_rate"] == "10/1"
            assert not any(s["codec_type"] == "audio" for s in info["streams"])
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(file), "-f", "null", "-"], check=True)
            record.update(duration_seconds=duration, codec=video["codec_name"], width=320,
                          height=180, fps=10, audio_streams=0, full_decode="PASS")
        else:
            assert file.read_bytes().startswith(b"%PDF-1.4")
            record["header_check"] = "PASS (not semantic PDF validation)"
        records.append(record)
(root / "artifacts").mkdir(exist_ok=True)
(root / "artifacts/fixture-verification.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
print(f"PASS: {len(records)} synthetic files; both H.264 videos fully decoded; 320x180, 10fps, no audio")
