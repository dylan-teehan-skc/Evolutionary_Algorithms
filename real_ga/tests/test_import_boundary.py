import ast
import unittest
from pathlib import Path

GA_DIR = Path(__file__).resolve().parents[1]

# module root -> path prefixes (relative to ga/) allowed to import it
ALLOWED = {
    "pymunk": ("src/sim/",),
    "pygame": ("smoke_video.py", "src/video/"),
    "imageio_ffmpeg": ("smoke_video.py", "src/video/"),
}
# the pure core imports none of these (D-05: it never reads YAML either)
CORE_FORBIDDEN = {"pymunk", "pygame", "imageio_ffmpeg", "yaml"}


def imported_roots(source):
    roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def violations(path, roots):
    rel = path.relative_to(GA_DIR).as_posix()
    found = []
    for root, prefixes in ALLOWED.items():
        if root in roots and not rel.startswith(prefixes):
            found.append(f"{rel} imports {root}")
    if rel.startswith("src/climb/"):
        found += [f"{rel} imports {r}" for r in sorted(roots & CORE_FORBIDDEN)]
    return sorted(set(found))


class ImportBoundaryTests(unittest.TestCase):
    def test_imported_roots_returns_top_level_absolute_modules(self):
        source = "import pymunk\nfrom pygame import font\nimport os.path\nfrom . import x"
        self.assertEqual(imported_roots(source), {"pymunk", "pygame", "os"})

    def test_violations_flags_pymunk_in_core(self):
        path = GA_DIR / "src" / "climb" / "x.py"
        self.assertEqual(
            violations(path, {"pymunk", "yaml"}),
            ["src/climb/x.py imports pymunk", "src/climb/x.py imports yaml"],
        )

    def test_real_tree_respects_the_boundary(self):
        files = list((GA_DIR / "src").rglob("*.py")) + list(GA_DIR.glob("*.py"))
        found = []
        for path in files:
            found += violations(path, imported_roots(path.read_text()))
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
