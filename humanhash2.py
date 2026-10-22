"""Human-readable names for SHA-256 digests, plus a directory hash tree
whose per-directory manifests are printed with those names.

A name is a display form of the full digest. Lookups, cache keys and the
parent-node hash input always use the full digest.
"""
import argparse
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

WORDS = Path(__file__).with_name("bip39_english.txt").read_text().split()
assert len(WORDS) == 2048 and len(set(WORDS)) == 2048

IGNORED_NAMES = {".git", ".DS_Store", "__pycache__"}


def short_name(digest: bytes, n_words: int = 2) -> str:
    """Map the leading 128 bits of a digest to 'word-word-NN'.

    Mixed-radix split: the last field is 0..99, each word field is 0..2047.
    A longer name extends a shorter one: the words keep their order and the
    number stays at the end.
    """
    assert 1 <= n_words <= 10  # 100 * 2048**10 < 2**128
    x = int.from_bytes(digest[:16], "big")
    num = x % 100
    x //= 100
    words = []
    for _ in range(n_words):
        words.append(WORDS[x % 2048])
        x //= 2048
    return "-".join(words + [f"{num:02d}"])


@dataclass
class Node:
    name: str
    kind: str  # "f" for a file, "d" for a directory
    digest: bytes
    children: list = field(default_factory=list)


def hash_file(path: Path) -> bytes:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.digest()  # equals `shasum -a 256 <file>`


def hash_tree(path: Path) -> Node:
    if path.is_file():
        return Node(path.name, "f", hash_file(path))
    children = [
        hash_tree(p)
        for p in sorted(path.iterdir(), key=lambda p: p.name)
        if p.name not in IGNORED_NAMES and not p.is_symlink()
    ]
    # Parent input is the manifest of FULL child digests, never the short names.
    manifest = "".join(f"{c.kind} {c.digest.hex()} {c.name}\n" for c in children)
    return Node(path.name, "d", hashlib.sha256(manifest.encode()).digest(), children)


def label(node: Node) -> str:
    return node.name + ("/" if node.kind == "d" else "")


def print_tree(node: Node, n_words: int, full: bool, depth: int = 0) -> None:
    line = f"{'  ' * depth}{label(node):<{28 - 2 * depth}} {short_name(node.digest, n_words)}"
    if full:
        line = f"{line:<56} {node.digest.hex()}"
    print(line)
    for c in node.children:
        print_tree(c, n_words, full, depth + 1)


def print_diff(a: Node, b: Node, n_words: int, depth: int = 0) -> None:
    """Print only the path from the root down to each differing entry."""
    if a.digest == b.digest:
        return
    pad = "  " * depth
    w = 28 - 2 * depth
    print(f"{pad}{label(a):<{w}} {short_name(a.digest, n_words)}  ->  {short_name(b.digest, n_words)}")
    if a.kind != "d" or b.kind != "d":
        return
    left = {c.name: c for c in a.children}
    right = {c.name: c for c in b.children}
    for name in sorted(left.keys() | right.keys()):
        if name not in right:
            print(f"{pad}  - {label(left[name]):<{w - 4}} {short_name(left[name].digest, n_words)}")
        elif name not in left:
            print(f"{pad}  + {label(right[name]):<{w - 4}} {short_name(right[name].digest, n_words)}")
        else:
            print_diff(left[name], right[name], n_words, depth + 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Human-readable SHA-256 names and directory hash trees.")
    ap.add_argument("-w", "--words", type=int, default=2, help="words per name, 1..10 (default 2)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("name", help="print the name of each file")
    p.add_argument("files", nargs="+", type=Path)
    p = sub.add_parser("tree", help="print a directory tree with names")
    p.add_argument("dir", type=Path)
    p.add_argument("--full", action="store_true", help="also print full hex digests")
    p = sub.add_parser("diff", help="print only the paths that differ between two trees")
    p.add_argument("dir_a", type=Path)
    p.add_argument("dir_b", type=Path)
    args = ap.parse_args()

    if args.cmd == "name":
        for f in args.files:
            print(f"{short_name(hash_file(f), args.words)}  {f}")
    elif args.cmd == "tree":
        print_tree(hash_tree(args.dir), args.words, args.full)
    else:
        a, b = hash_tree(args.dir_a), hash_tree(args.dir_b)
        if a.digest == b.digest:
            print(f"identical  {short_name(a.digest, args.words)}")
        else:
            print_diff(a, b, args.words)


if __name__ == "__main__":
    main()
