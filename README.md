# humanhash2

humanhash2 shows each SHA-256 digest as a short name of the form `word-word-word-NN`, and shows a directory hash tree as one manifest per directory, so a person can see which file differs between two trees without reading hex.

```
$ python3 humanhash2.py diff v1 v2
v1/                          crunch-spoil-kiss-46  ->  erode-sauce-horror-01
  docs/                      real-tongue-obtain-29  ->  unhappy-alarm-stuff-22
    + notes.md               comfort-side-cry-86
  src/                       video-note-world-49  ->  foster-install-video-02
    core/                    lyrics-face-festival-41  ->  boy-again-say-46
      config.py              dilemma-easy-yard-06  ->  intact-offer-minor-03
```

`./demo.sh` builds these two trees and prints the full `tree --full` output for both, followed by the diff above.

## Usage

The script needs Python 3.7 or later and no packages outside the standard library.

* `python3 humanhash2.py name FILE...` prints the name of each file.
* `python3 humanhash2.py tree DIR` prints every node of the tree with its name.
* `python3 humanhash2.py tree --full DIR` also prints each full hex digest.
* `python3 humanhash2.py diff DIR_A DIR_B` prints only the path from the root to each entry that differs.
* `-w N` sets the number of words per name (1 to 10, default 3).

## Name format

The leading 128 bits of the digest are read as one integer and split in mixed radix. The lowest field is taken mod 100 and gives the number. Each further field is taken mod 2048 and gives one word.

| Format | Bits | Objects at which a collision becomes 50% likely | Chance two given objects get the same name |
| --- | --- | --- | --- |
| `word-NN` | 17.6 | 533 | 1 in 204,800 |
| `word-word-NN` | 28.6 | 24,113 | 1 in 419,430,400 |
| `word-word-word-NN` (default) | 39.6 | 1,091,246 | 1 in 858,993,459,200 |
| git 7-hex abbreviation | 28.0 | 19,291 | 1 in 268,435,456 |

A longer name extends a shorter one. For example, `general-word-thank-69` becomes `general-word-thank-ring-69`, so the words keep their order and the number stays at the end. git lengthens an abbreviated hash the same way when it collides.

## Hash tree

* A file's digest is the SHA-256 of its content, which equals the output of `shasum -a 256`.
* A directory's digest is the SHA-256 of its manifest. Each manifest line is `<kind> <full hex digest> <name>`, sorted by name, where `<kind>` is `f` for a file and `d` for a directory.
* The manifest contains full child digests rather than child names, so the tree keeps the collision resistance of SHA-256.
* A directory's own name is recorded in its parent's manifest rather than in its own digest.
* `.git`, `.DS_Store`, `__pycache__`, and symbolic links are skipped.

## Rules for use

* A name is a display form only. Cache keys, lookups, and stored references use the full digest.
* A name suits change detection where nobody forges content on purpose. For the default 39.6-bit name, finding any colliding pair takes about 2^20 hashes and matching a chosen name takes about 2^39.6, so a check against a forger compares the full hex.

## Word list

`bip39_english.txt` is the English word list from [BIP-39](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt). The list has 2048 words of 3 to 8 letters, and no two words share their first 4 letters. The file's SHA-256 is `2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda`.

The list contains 806 pairs of words that differ by one letter, such as `act` and `art`. The words and the number of a name are independent fields, so misreading a whole name requires every field to look alike at once.

## Prior art

[humanhash](https://github.com/zacharyvoase/humanhash) maps one digest to 4 words. It XOR-folds the digest into 4 bytes and looks each byte up in a 256-word list, which gives 32 bits. humanhash2 differs in three ways:
* humanhash2 truncates the digest rather than XOR-folding it, so a longer name extends a shorter one.
* humanhash2 uses a 2048-word list plus a two-digit number, which gives 39.6 bits for the default 3 words.
* humanhash2 adds the directory hash tree and the diff.
