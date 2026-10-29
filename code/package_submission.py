"""Build an explicit source-only archive and verify its contents."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def package(root: Path) -> Path:
    destination=root/"code.zip"
    paths=[root/"README.md", root/"code/README.md"]
    paths.extend(p for p in (root/"code").rglob("*") if p.is_file() and (p.suffix==".py" or p.name=="requirements.txt")
                 and not any(part in {"__pycache__",".venv","cache",".cache","runs"} for part in p.parts))
    required=[root/"code"/"evaluation"/name for name in ("evaluation_report.md","usage_report.md")]
    if not all(p.exists() for p in required):
        raise ValueError("Generate evaluation and usage Markdown reports before packaging")
    paths.extend(required)
    supporting=[root/"code/evaluation"/name for name in ("architecture.md", "correctness_review.md")]
    paths.extend(p for p in supporting if p.exists())
    fallback_report=root/"code/evaluation/competition_fallbacks.md"
    if fallback_report.exists():
        paths.append(fallback_report)
    temporary=destination.with_suffix(".zip.tmp")
    with ZipFile(temporary,"w",compression=ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path,path.relative_to(root).as_posix())
        for path in required:
            archive.write(path,"evaluation/"+path.name)
        for path in supporting:
            if path.exists():
                archive.write(path,"evaluation/"+path.name)
        if fallback_report.exists():
            archive.write(fallback_report,"evaluation/"+fallback_report.name)
    with ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive integrity check failed")
        for name in archive.namelist():
            if any(part.startswith(".") or part in {"dataset","runs","__pycache__"} for part in Path(name).parts):
                raise ValueError("Archive includes excluded data or cache")
            if Path(name).suffix not in {".py",".md",".txt"}:
                raise ValueError("Archive includes unexpected or nested binary artifact")
    temporary.replace(destination)
    return destination


if __name__=="__main__":
    print(package(Path(__file__).resolve().parents[1]))
