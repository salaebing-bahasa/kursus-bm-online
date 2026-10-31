"""Tukar teks Rumi kepada tulisan Jawi untuk laman Kursus BM Online.

Ejaan diambil daripada _src/jawi.tsv (lajur: rumi, jawi, sumber). Guru boleh membetulkan
mana-mana ejaan terus dalam fail itu, kemudian jalankan semula `python3 _src/build.py`.
Kata yang tiada dalam fail dieja secara automatik mengikut peraturan asas dan dicetak
sebagai senarai semakan semasa membina laman.
"""
import re
from pathlib import Path

TSV = Path(__file__).resolve().parent / "jawi.tsv"
DICT = {}
for _ln in TSV.read_text(encoding="utf-8").splitlines()[1:]:
    _p = _ln.split("\t")
    if len(_p) >= 2 and _p[0] and _p[1]:
        DICT[_p[0].lower()] = _p[1]

MISSES = {}  # kata yang dieja secara automatik (perlu disemak)
PUNCT = str.maketrans({",": "،", "?": "؟", ";": "؛"})
TOKEN = re.compile(r"/[^/\s]{1,6}/|[A-Za-z]+(?:['’-][A-Za-z]+)*|\s+|.", re.S)
# imbuhan yang ditulis sebagai bentuk awalan dalam latihan (meN-, ber- ...)
AFFIX = {"me": "م", "mem": "مم", "men": "من", "meng": "مڠ", "meny": "مڽ", "ber": "بر", "be": "ب", "bel": "بل",
         "pe": "ڤ", "pem": "ڤم", "pen": "ڤن", "peng": "ڤڠ", "peny": "ڤڽ", "per": "ڤر", "se": "س", "di": "د", "ter": "تر"}

# --- ejaan automatik (sandaran) -------------------------------------------------
DIGRAPH = {"ng": "ڠ", "ny": "ڽ", "sy": "ش", "kh": "خ", "gh": "غ", "dh": "ض", "th": "ث"}
CONS = {"b": "ب", "c": "چ", "d": "د", "f": "ف", "g": "ݢ", "h": "ه", "j": "ج", "k": "ک", "l": "ل", "m": "م",
        "n": "ن", "p": "ڤ", "q": "ق", "r": "ر", "s": "س", "t": "ت", "v": "ۏ", "w": "و", "x": "کس", "y": "ي", "z": "ز"}
VOW = {"a": "ا", "i": "ي", "u": "و", "o": "و", "e": ""}


def rule(w):
    """Ejaan kasar huruf demi huruf (untuk kata yang belum ada dalam jawi.tsv)."""
    w = w.lower(); out = []; i = 0
    while i < len(w):
        two = w[i:i + 2]
        if two in DIGRAPH:
            out.append(DIGRAPH[two]); i += 2; continue
        ch = w[i]
        if ch in VOW:
            if i == 0:
                out.append("ا" + ("" if ch in "ae" else VOW[ch]))
            elif ch == "a" and i == len(w) - 1:
                out.append("ا")
            elif ch == "a":
                # a pada suku kata terbuka ditulis alif, pada suku kata tertutup tidak
                nxt = w[i + 1:i + 3]
                out.append("ا" if (len(nxt) == 2 and nxt[0] not in VOW and nxt[1] in VOW) else "")
            else:
                out.append(VOW[ch])
        elif ch == "k" and i == len(w) - 1:
            out.append("ق")
        else:
            out.append(CONS.get(ch, ch))
        i += 1
    return "".join(out)


def word(w):
    k = w.lower().replace("’", "'")
    if k in DICT:
        return DICT[k]
    if "-" in k:
        parts = k.split("-")
        if len(parts) == 2 and parts[0] == parts[1]:          # kata ganda: buku-buku -> بوکو٢
            return word(parts[0]) + "٢"
        joined = "".join(parts)
        if joined in DICT:                                     # suku kata: bu-ku -> بوکو
            return DICT[joined]
        return "-".join(word(p) for p in parts)
    for suf, j in (("lah", "له"), ("kah", "که"), ("nya", "ڽ"), ("kan", "کن")):
        root = k[: -len(suf)]
        if k.endswith(suf) and root in DICT:
            base = DICT[root]
            # partikel -kah/-lah/-nya: vokal a di hujung kata dasar ditulis semula dengan alif (apa -> اڤاکه)
            if suf != "kan" and root.endswith("a") and not base.endswith("ا"):
                base += "ا"
            return base + j
    MISSES[k] = MISSES.get(k) or rule(k)
    return MISSES[k]


def jawi(text):
    """Teks Rumi -> Jawi. Singkatan huruf besar (DBP, ICT, RM) dan nombor dikekalkan."""
    out = []
    toks = TOKEN.findall(text)
    for n, t in enumerate(toks):
        if t[0] == "/" and len(t) > 2:                       # lambang IPA /a/ dikekalkan
            out.append(t)
        elif t[0].isalpha():
            nxt = toks[n + 1] if n + 1 < len(toks) else ""
            if len(t) == 1 or (t.isupper() and len(t) > 1):  # huruf Rumi (a, B) dan singkatan (DBP) dikekalkan
                out.append(t)
            elif nxt == "-" and t.lower() in AFFIX:          # awalan: meny- -> مڽ-
                out.append(AFFIX[t.lower()])
            else:
                out.append(word(t))
        else:
            out.append(t.translate(PUNCT))
    s = "".join(out)
    s = re.sub(r"[“”\"]", "\"", s)
    return re.sub(r"\s+", " ", s).strip()
