"""Print a markdown table of sdist/wheel outputs

for use in github job summary
"""

from pathlib import Path


def make_summary(dist_dir: str | Path) -> str:
    """Render a list of files as a markdown table

    For use summarizing wheel outputs
    """

    dist_dir = Path(dist_dir)
    all_dists = sorted(dist_dir.glob("*"))
    lines = [
        f"### {len(all_dists)} files",
        "",
        "| filename | size |",
        "|----------|------|",
    ]
    for path in all_dists:
        size = path.stat().st_size
        if size < 1e6:
            size_s = f"{size / 1e3:.0f} kB"
        else:
            size_s = f"{size / 1e6:.1f} MB"
        lines.append(f"| {path.name} | {size_s} |")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        dist_dir = Path(sys.argv[1])
    else:
        dist_dir = Path("dist")
    print(make_summary(dist_dir))
