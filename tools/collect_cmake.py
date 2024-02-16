"""
collect cmake -LH output

for inclusion in docs
"""

import sys
from pathlib import Path
from subprocess import PIPE, run
from tempfile import TemporaryDirectory

here = Path(__file__).parent.absolute()
repo = here.parent
home = str(Path.home())


def summarize_cmake_output(text: str) -> str:
    """Summarize cmake -LH output

    Formats help strings nicer, excludes common
    """
    text = text.replace(sys.prefix, "$PREFIX")
    text = text.replace(home, "~")
    chunks = text.split("\n\n")
    new_chunks = []
    for chunk in chunks:
        if not chunk:
            continue
        lines = chunk.splitlines()
        doc_lines, assignment = lines[:-1], lines[-1]
        if assignment.startswith(("CMAKE_", "FETCHCONTENT_")):
            continue
        doc_lines = [
            "# " + doc_line.lstrip("/ ")
            for doc_line in doc_lines
            if not doc_line.startswith("--")
        ]
        new_chunks.append("\n".join(doc_lines + [assignment]))
    return "\n\n".join(new_chunks)


def summarize_cmake(path: Path) -> str:
    """Collect summarized cmake -LH output from a repo"""
    path = Path(path).absolute()
    with TemporaryDirectory() as td:
        p = run(
            ["cmake", "-LH", str(path)],
            text=True,
            stderr=sys.stderr,
            stdout=PIPE,
            check=False,
            cwd=td,
        )
    return summarize_cmake_output(p.stdout)


def main():
    if len(sys.argv) < 2:
        paths = [repo]
    else:
        paths = sys.argv[1:]
    for path in paths:
        print(path)
        print(summarize_cmake(path))
        print("\n\n")


if __name__ == "__main__":
    main()
