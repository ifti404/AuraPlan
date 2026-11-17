"""Create the portable distribution archive with stable relative paths."""
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> int:
    source = Path(sys.argv[1]).resolve()
    destination = Path(sys.argv[2]).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in source.rglob("*"):
            if path.is_file():
                relative = path.relative_to(source)
                # Keep local tasks and profiles out of distributable builds.
                if relative.parts[0].casefold() == "data":
                    continue
                archive.write(path, relative.as_posix())
    print(f"Created portable archive: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
