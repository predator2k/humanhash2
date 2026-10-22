#!/bin/sh
# Build two small trees that differ in one edited file and one added file,
# then print both trees and the diff.
set -e
here=$(cd "$(dirname "$0")" && pwd)
d=$(mktemp -d)
mkdir -p "$d/v1/src/core" "$d/v1/docs"
printf '# proj\n' > "$d/v1/README.md"
printf 'def main(): pass\n' > "$d/v1/src/main.py"
printf 'TIMEOUT = 30\n' > "$d/v1/src/core/config.py"
printf 'def parse(x): return x\n' > "$d/v1/src/core/parser.py"
printf 'guide\n' > "$d/v1/docs/guide.md"
cp -R "$d/v1" "$d/v2"
printf 'TIMEOUT = 60\n' > "$d/v2/src/core/config.py"
printf 'notes\n' > "$d/v2/docs/notes.md"
for v in v1 v2; do
  echo "== tree $v"
  python3 "$here/humanhash2.py" tree --full "$d/$v"
done
echo "== diff v1 v2"
python3 "$here/humanhash2.py" diff "$d/v1" "$d/v2"
rm -rf "$d"
