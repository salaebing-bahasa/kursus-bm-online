#!/usr/bin/env python3
"""Bina laman web Kursus BM Online daripada fail _src/units/*.md.

Cara guna:  python3 _src/build.py
Output ditulis ke folder akar repositori (index.html, pertemuan/*.html).
"""
import html, json, re
from pathlib import Path
import markdown
import lxml.html
from jawi import jawi, MISSES

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src" / "units"
GOATCOUNTER = "kursus-bm-online"  # kod laman GoatCounter
SITE = "https://salaebing-bahasa.github.io/kursus-bm-online/"
SITEMAP = []
FONTS = "https://fonts.googleapis.com/css2?family=Bai+Jamjuree:wght@500;600;700&family=Noto+Naskh+Arabic:wght@400;600&family=Sarabun:ital,wght@0,400;0,600;1,400&display=swap"

PHASES = [
    (1, 5, "Aktiviti Harian & Perhubungan (I)"),
    (6, 10, "Aktiviti Harian & Perhubungan (II)"),
    (11, 15, "Interaksi Sosial & Budaya"),
    (16, 20, "Pengukuhan & Komunikasi Formal"),
]

# (tarikh ISO, tarikh paparan, pengajar, fokus kemahiran & tatabahasa, aktiviti & penilaian)
SCHEDULE = {
    1: ("2026-11-01", "1 November 2026", "Prof. Madya Dr. Numan Hayimasae", "Sejarah dan perkembangan Bahasa Melayu di Nusantara", "Garis masa sejarah Bahasa Melayu"),
    2: ("2026-11-08", "8 November 2026", "Asst. Prof. Manavavee Mamah", "Mendengar: Vokal (a, e, i, o, u)", "Latihan mendengar dan menyebut bunyi vokal"),
    3: ("2026-11-15", "15 November 2026", "Asst. Prof. Nurhuda Sadama", "Bertutur: Kata Ganti Nama Diri (Saya, Awak, Anda)", "Lakonan simulasi perkenalan diri secara formal"),
    4: ("2026-11-22", "22 November 2026", "Dr. Abdullah Kreedaoh", "Membaca: Kata Nama Am & Kata Nama Khas", "Membina carta organisasi keluarga sendiri"),
    5: ("2026-11-29", "29 November 2026", "Dr. Samsina Yapha", "Mendengar: Kata Bilangan & Penjodoh Bilangan", "Kuiz spontan harga barang di pasar"),
    6: ("2026-12-06", "6 Disember 2026", "Dr. Uniansasmita Samoh", "Menulis: Kata Sifat (besar, bersih, jauh)", "Padanan gambar dengan perkataan yang betul"),
    7: ("2026-12-13", "13 Disember 2026", "Encik Lee", "Bertutur: Kata Kerja Transitif", "Vlog pendek \"Satu Jam dalam Hidup Saya\""),
    8: ("2026-12-20", "20 Disember 2026", "Ustazah Khadijah Muna", "Membaca: Kata Kerja Tak Transitif", "Temu bual rakan sekelas tentang hobi"),
    9: ("2026-12-27", "27 Disember 2026", "Asst. Prof. Dr. Aleeyah Masae", "Mendengar: Kata Sendi Nama (di, ke, dari)", "Lukis peta berdasarkan arahan lisan guru"),
    10: ("2027-01-03", "3 Januari 2027", "Cik Rahanee Tehsa", "Bertutur: Ayat Perintah & Permintaan", "Simulasi memesan makanan secara dalam talian"),
    11: ("2027-01-10", "10 Januari 2027", "Cik Firdaos Muhamat", "Menulis: Kata Hubung (dan, atau, tetapi)", "Menulis mesej ringkas kepada doktor"),
    12: ("2027-01-17", "17 Januari 2027", "Puan Wankamilia Hayeehasa", "Bertutur: Ayat Tanya (Berapa, Mana)", "Main peranan penjual dan pembeli"),
    13: ("2027-01-24", "24 Januari 2027", "Dr. Suhaila Binsama-ae", "Membaca: Kata Adjektif Warna & Ukuran", "Persembahan slaid \"Fesyen Kegemaran Saya\""),
    14: ("2027-01-31", "31 Januari 2027", "Ustaz Abd. Ghani", "Mendengar: Penanda Wacana (Selain itu, Kemudian)", "Laporan cuaca kreatif ala berita TV"),
    15: ("2027-02-07", "7 Februari 2027", "Ustaz Nurdin", "Menulis: Imbuhan Awalan (meN-, ber-)", "Menulis kad ucapan digital untuk kawan"),
    16: ("2027-02-14", "14 Februari 2027", "Asst. Prof. Muhammad Salaebing", "Membaca: Kata Pinjaman & Istilah ICT", "Mencari maklumat di laman berita Melayu"),
    17: ("2027-02-14", "14 Februari 2027", "Asst. Prof. Samiyah Baleh", "Bertutur: Ayat Penyata & Ayat Seruan", "Pembentangan \"Cita-cita Saya\""),
    18: ("2027-02-21", "21 Februari 2027", "Asst. Prof. Hasbulloh Nadaraning", "Mendengar: Kata Tanya (Bagaimana, Mengapa)", "Membina itinerari pelancongan ringkas"),
    19: ("2027-02-28", "28 Februari 2027", "Asst. Prof. Dr. Pareeda Hayeeteh", "Menulis: Membina Perenggan Mudah", "Menulis ulasan pendek tentang filem Melayu"),
    20: ("2027-03-07", "7 Mac 2027", "Asst. Prof. Dr. Pareeda Hayeeteh, Puan Kartini Wado, Asst. Prof. Muhammad Salaebing & Dr. Uniansasmita Samoh", "Semua kemahiran: Pengukuhan tatabahasa", "Penilaian akhir: Pembentangan projek individu"),
}

SECTION_IDS = {"Objektif Pembelajaran": "objektif", "Kosa Kata": "kosa-kata", "Perbualan": "perbualan",
               "Tatabahasa": "tatabahasa", "Latihan": "latihan", "Kuiz": "kuiz"}

esc = html.escape


def parse_unit(path):
    text = path.read_text(encoding="utf-8")
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    sections = []
    for chunk in re.split(r"^## ", body, flags=re.M)[1:]:
        title, _, content = chunk.partition("\n")
        sections.append((title.strip(), content.strip()))
    return meta, sections


def inline(md_text):
    return markdown.markdown(md_text, extensions=["tables"])[3:-4] if md_text else ""


def table_rows(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c or "-") for c in cells):
            continue
        rows.append(cells)
    return rows


def dialogue_html(rows):
    head, body = rows[0], rows[1:]
    speakers = []
    out = ['<div class="dialog">']
    for r in body:
        who, line = r[0], r[1] if len(r) > 1 else ""
        if who not in speakers:
            speakers.append(who)
        side = "b" if speakers.index(who) % 2 else "a"
        out.append(f'<div class="turn turn-{side}"><span class="who">{esc(who)}</span>'
                   f'<p class="said">{inline(line)}</p></div>')
    out.append("</div>")
    return "\n".join(out)


def render_content(md_text):
    """Tukar markdown ke HTML; jadual 'Penutur | Dialog' menjadi paparan dialog."""
    lines = md_text.splitlines()
    out, buf, i = [], [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i]); i += 1
            rows = table_rows(block)
            if rows and rows[0][0] == "Penutur":
                out.append(markdown.markdown("\n".join(buf), extensions=["tables"])); buf = []
                out.append(dialogue_html(rows))
            else:
                buf.extend(block)
            continue
        buf.append(lines[i]); i += 1
    out.append(markdown.markdown("\n".join(buf), extensions=["tables"]))
    h = "\n".join(out)
    return label_tables(h)


def lbl(heads, i):
    return heads[i] if i < len(heads) else ""


def label_tables(h):
    """Letak data-label (tajuk lajur) pada setiap <td> dan balut jadual dalam kotak yang boleh ditatal dan difokus."""
    def one(m):
        t = m.group(0)
        heads = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<th[^>]*>(.*?)</th>", t, flags=re.S)]
        def row(rm):
            k = iter(range(100))
            return re.sub(r"<td([^>]*)>", lambda cm: f'<td{cm.group(1)} data-label="{esc(lbl(heads, next(k)))}">', rm.group(0))
        t = re.sub(r"<tr>.*?</tr>", row, t, flags=re.S)
        cls = " cards" if len(heads) >= 3 else ""
        return f'<div class="table-wrap{cls}" tabindex="0">{t}</div>'
    return re.sub(r"<table>.*?</table>", one, h, flags=re.S)


# ---------------------------------------------------------------- tulisan Jawi
# Setiap baris/sel berbahasa Melayu diberi baris Jawi di bawahnya (<span class="jw">).
# Ejaan: _src/jawi.tsv (guru boleh membetulkan ejaan dalam fail itu).
TH_CHARS = re.compile("[\u0E00-\u0E7F]")
AR_CHARS = re.compile("[\u0600-\u06FF]")
JW_TAGS = {"td", "li", "p", "legend", "button", "h3", "h4", "blockquote"}
JW_BLOCKS = {"p", "ul", "ol", "li", "table", "div", "fieldset", "blockquote", "h3", "h4"}
# lajur yang berisi huruf/bunyi, IPA atau perkataan Inggeris — tidak dieja dalam Jawi
JW_SKIP_COLS = {"Vokal", "Konsonan", "Diftong", "IPA", "Bahasa Inggeris", "Angka", "Markah (1–10)", "✓"}


def jw_span(text, tag="span"):
    j = jawi(text)
    if not AR_CHARS.search(j):
        return ""
    return f'<{tag} class="jw" lang="ms-Arab" dir="rtl">{esc(j)}</{tag}>'


def jw_text(el):
    """Teks Rumi elemen (tanpa nombor soalan dan tanpa baris Jawi yang sudah ada)."""
    parts = []
    def walk(e):
        cls = e.get("class") or ""
        if "qn" in cls.split() or "jw" in cls.split():
            if e.tail: parts.append(e.tail)
            return
        if e.text: parts.append(e.text)
        for c in e: walk(c)
        if e.tail and e is not el: parts.append(e.tail)
    walk(el)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def add_jawi(fragment):
    """Tambah baris Jawi pada setiap elemen teks Melayu dalam serpihan HTML."""
    root = lxml.html.fragment_fromstring(fragment, create_parent="div")
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.tag not in JW_TAGS:
            continue
        if any(isinstance(c.tag, str) and c.tag in JW_BLOCKS for c in el.iterdescendants()):
            continue                                     # proses elemen paling dalam sahaja
        if el.tag == "td" and el.get("data-label", "") in JW_SKIP_COLS:
            continue
        cls = (el.get("class") or "").split()
        if el.tag == "p" and ("fb" in cls or "flag" in cls):
            continue
        text = jw_text(el)
        if not text or TH_CHARS.search(text) or not re.search("[A-Za-z]{2}", text):
            continue
        if re.fullmatch(r"[A-Za-z]{1,2}", text):          # satu huruf / bunyi sahaja
            continue
        span = jw_span(text)
        if not span:
            continue
        if el.tag == "button":                            # pilihan kuiz: teks Rumi dalam .rm (dibaca oleh app.js)
            rm = lxml.html.fragment_fromstring(f'<span class="rm">{esc(el.text or "")}</span>')
            el.text = None; el.insert(0, rm)
        node = lxml.html.fragment_fromstring(span)
        if el.tag == "legend":                            # soalan kuiz: baris Jawi di bawah legend, dalam kotak soalan
            node.tail = el.tail; el.tail = None
            el.addnext(node)
        else:
            el.append(node)
    out = (root.text or "") + "".join(lxml.html.tostring(c, encoding="unicode") for c in root)
    return out


# Butang tunjuk/sembunyi baris Jawi (pilihan disimpan dalam pelayar)
JW_BTN = ('<button type="button" class="btn-ghost jw-toggle" aria-pressed="true">'
          '<span class="jw-mark" aria-hidden="true">ج</span>'
          '<span>Tulisan Jawi</span></button>')


# Nota sumber ejaan Jawi (dipaparkan di halaman pertemuan dan dalam PDF)
JW_NOTE = ('<p class="jw-note">Ejaan Jawi dalam laman ini mengikut sistem ejaan Jawi Dewan Bahasa dan Pustaka (DBP), Malaysia.</p>')


def jw_report():
    """Cetak kata yang dieja secara automatik (belum ada dalam _src/jawi.tsv)."""
    if MISSES:
        print(f"Jawi: {len(MISSES)} kata dieja secara automatik (sila semak & tambah ke _src/jawi.tsv):")
        print("  " + ", ".join(f"{k}={v}" for k, v in sorted(MISSES.items())))


def parse_quiz(md_text):
    qs, cur = [], None
    for ln in md_text.splitlines():
        ln = ln.strip()
        if ln.startswith("? "):
            cur = {"q": ln[2:], "opts": [], "ans": None}; qs.append(cur)
        elif ln.startswith(("* ", "- ")) and cur is not None:
            if ln.startswith("* "):
                cur["ans"] = len(cur["opts"])
            cur["opts"].append(ln[2:])
    return qs


def quiz_html(qs, uid):
    out = [f'<div class="quiz" data-quiz="{uid}">']
    for n, q in enumerate(qs, 1):
        out.append(f'<fieldset class="q" data-ans="{q["ans"]}"><legend><span class="qn">{n}</span>{esc(q["q"])}</legend><div class="opts">')
        for k, o in enumerate(q["opts"]):
            out.append(f'<button type="button" class="opt" data-i="{k}">{esc(o)}</button>')
        out.append('</div><p class="fb" aria-live="polite"></p></fieldset>')
    out.append(f'<div class="score" aria-live="polite">Jawab semua {len(qs)} soalan untuk melihat markah anda.</div>'
               '<button type="button" class="btn-ghost quiz-reset">Cuba semula</button></div>')
    return "\n".join(out)


def vocab_rows(units):
    """Kumpul baris kosa kata (Bahasa Melayu | Contoh Ayat) untuk kad 'Kata hari ini' (dengan ejaan Jawi)."""
    out = []
    for n, (meta, sections, _) in units.items():
        for title, content in sections:
            if title != "Kosa Kata":
                continue
            for m in re.finditer(r"((?:^\|.*\n?)+)", content, flags=re.M):
                rows = table_rows(m.group(1).strip().splitlines())
                if len(rows) < 2 or rows[0][:2] != ["Bahasa Melayu", "Contoh Ayat"]:
                    continue
                for r in rows[1:]:
                    if len(r) >= 2 and r[0] and r[1]:
                        out.append([r[0], jawi(r[0]), r[1], n])
    return out


def running(right):
    return f'<p class="running" aria-hidden="true"><span>Kursus Bahasa Melayu Online</span><span>{right}</span></p>'


ORN = '<p class="orn" aria-hidden="true"><span></span></p>'


def folio(f):
    return f'<p class="folio" aria-hidden="true"><span>{f}</span></p>'


def page(title, body, depth=0, desc="", active="", path=""):
    p = "../" * depth
    SITEMAP.append(SITE + path)
    nav = [("index.html#kandungan", "Kandungan", "kandungan"), ("index.html#jadual", "Jadual", "jadual"),
           ("index.html#penilaian", "Penilaian", "penilaian")]
    links = "".join(f'<a href="{p}{h}"{" aria-current=\"page\"" if a == active else ""}><span>{t}</span>{jw_span(t, "small")}</a>' for h, t, a in nav)
    return f"""<!doctype html>
<html lang="ms">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta name="theme-color" content="#4A1631">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Kursus BM Online">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:locale" content="ms_MY">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="{FONTS}"></noscript>
<link rel="stylesheet" href="{p}assets/style.css">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<script>try{{if(localStorage.getItem("jawi")==="0")document.documentElement.classList.add("no-jw")}}catch(e){{}}</script>
</head>
<body>
<a class="skip" href="#isi">Langkau ke kandungan</a>
<header class="site-head">
  <a class="brand" href="{p}index.html"><span class="mark" aria-hidden="true"></span><span>Kursus BM Online<small>Tahap Permulaan</small></span></a>
  <nav aria-label="Navigasi utama">{links}</nav>
</header>
<main id="isi">
{body}
</main>
<footer class="site-foot">
  <p>Kursus Bahasa Melayu Secara Online (Tahap Permulaan), 1 November 2026 hingga 7 Mac 2027, setiap Ahad 2.00–3.30 petang (Masa Patani).</p>
  <p>Ejaan Jawi mengikut sistem ejaan Jawi Dewan Bahasa dan Pustaka (DBP), Malaysia</p>
  <p>Bahan disediakan oleh pasukan pengajar kursus. Laman ini dikendalikan oleh Asst. Prof. Muhammad Salaebing, Universiti Thaksin.</p>
</footer>
<script src="{p}assets/app.js" defer></script>
<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def build_units():
    units = {}
    for f in sorted(SRC.glob("*.md")):
        n = int(f.stem)
        meta, sections = parse_unit(f)
        units[n] = (meta, sections, f.read_text(encoding="utf-8"))
    out_dir = ROOT / "pertemuan"; out_dir.mkdir(exist_ok=True)
    for n, (meta, sections, raw) in units.items():
        iso, date, teacher, focus, activity = SCHEDULE[n]
        toc, parts = [], []
        for title, content in sections:
            sid = SECTION_IDS.get(title, re.sub(r"\W+", "-", title.lower()))
            toc.append(f'<li><a href="#{sid}">{esc(title)}</a></li>')
            inner = quiz_html(parse_quiz(content), n) if sid == "kuiz" else render_content(content)
            inner = add_jawi(inner)
            parts.append(f'<section class="block" id="{sid}"><h2>{esc(title)}{jw_span(title)}</h2>{inner}</section>')
        prev_l = (f'<a class="prev" href="{n-1:02d}.html" rel="prev"><small>← Pertemuan {n-1}</small>{esc(units[n-1][0]["title"])}</a>' if n > 1
                  else '<a class="prev" href="../index.html#kandungan"><small>← Kandungan</small>Kandungan</a>')
        next_l = (f'<a class="next" href="{n+1:02d}.html" rel="next"><small>Pertemuan {n+1} →</small>{esc(units[n+1][0]["title"])}</a>' if n < 20
                  else '<a class="next" href="../index.html#penilaian"><small>Akhir buku →</small>Penilaian</a>')
        # Ringkasan pelajaran dalam PDF (dijana daripada halaman ini oleh _src/pdf.py, jadi isinya sama dengan laman web)
        ICON = ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
                'stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 20h14"/></svg>')
        dl = (f'<a class="btn" href="../pdf/pertemuan-{n:02d}.pdf" download="Kursus-BM-Online-Pertemuan-{n:02d}-Ringkasan.pdf">{ICON}'
              f'<span>Ringkasan pelajaran (PDF)</span></a>')
        prep = meta.get("penyediaan", "—")
        prep_html = f'<div><dt>Penyediaan bahan</dt><dd>{esc(prep)}</dd></div>' if prep not in ("", "—") else ""
        note17 = '<p class="flag">Tarikh dalam reka bentuk kursus sama dengan Pertemuan 16 — sila semak dengan penyelaras.</p>' if n == 17 else ""
        phase = next(name for a_, b_, name in PHASES if a_ <= n <= b_)
        body = f"""
<article class="sheet unit">
  {running(f"Pertemuan {n} · {esc(meta['title'])}")}
  <nav class="crumbs" aria-label="Laluan"><a href="../index.html#kandungan">Kandungan</a><span class="cr-ph" aria-hidden="true">›</span><span class="cr-ph">{esc(phase)}</span><span aria-hidden="true">›</span><span aria-current="page">Pertemuan {n}</span></nav>
  <header class="opener">
    <p class="op-k">Pertemuan {n} · <time datetime="{iso}">{date}</time></p>
    <h1>{esc(meta['title'])}{jw_span(meta['title'])}</h1>
    {note17}
    <dl class="unit-meta">
      <div><dt>Pengajar</dt><dd>{esc(teacher)}</dd></div>
      <div><dt>Fokus kemahiran</dt><dd>{esc(focus)}{jw_span(focus)}</dd></div>
      <div><dt>Aktiviti & penilaian</dt><dd>{esc(activity)}{jw_span(activity)}</dd></div>
      {prep_html}
    </dl>
    <div class="actions">{dl}{JW_BTN}</div>
    {JW_NOTE}
  </header>
  <nav class="sec-nav" aria-label="Bahagian pelajaran"><ol>{''.join(toc)}</ol></nav>
  {''.join(parts)}
  <p class="part-note">{esc(phase)}</p>
  {folio(n)}
</article>
<nav class="pager" aria-label="Pertemuan sebelum dan seterusnya">{prev_l}{next_l}</nav>"""
        (out_dir / f"{n:02d}.html").write_text(
            page(f"Pertemuan {n}: {meta['title']} — Kursus BM Online", body, 1, f"Pertemuan {n} ({date}): {meta['title']}. Kosa kata, dialog, tatabahasa, latihan dan kuiz kendiri dalam tulisan Rumi dan Jawi.", "", f"pertemuan/{n:02d}.html"), encoding="utf-8")
    return units


def build_index(units):
    contents, sched = [], []
    for a, b, name in PHASES:
        items, srows = [], []
        for n in range(a, b + 1):
            iso, date, teacher, focus, activity = SCHEDULE[n]
            t = units[n][0]["title"]
            items.append(f"""<li class="session" data-date="{iso}"><a href="pertemuan/{n:02d}.html">
  <span class="toc-k">Pertemuan {n}<small><time datetime="{iso}">{date}</time></small></span>
  <span class="toc-t">{esc(t)}{jw_span(t, "small")}</span><span class="toc-dots"></span><span class="toc-pg">{n}</span></a></li>""")
            srows.append(f'<tr data-date="{iso}"><td class="n" data-label="#"><a href="pertemuan/{n:02d}.html" aria-label="Pertemuan {n}">{n}</a></td><td data-label="Tarikh"><time datetime="{iso}">{date}</time></td>'
                         f'<td data-label="Tajuk"><a href="pertemuan/{n:02d}.html">{esc(t)}</a>{jw_span(t)}</td><td data-label="Fokus kemahiran">{esc(focus)}</td><td data-label="Pengajar">{esc(teacher)}</td></tr>')
        contents.append(f'<li class="toc-part"><span>Bahagian {len(contents)+1} · Pertemuan {a}–{b}</span>{esc(name)}</li>' + "".join(items))
        sched.append(f'<tbody><tr class="ph"><th colspan="5">Bahagian {len(sched)+1} · {esc(name)}</th></tr>{"".join(srows)}</tbody>')
    front = "".join(f'<li class="toc-front"><a href="{h}"><span class="toc-t">{m}{jw_span(m, "small")}</span><span class="toc-dots"></span><span class="toc-pg">{f}</span></a></li>'
                    for h, m, f in [("#pengenalan", "Pengenalan Kursus", "ii"), ("#jadual", "Jadual Kelas", "iii"), ("#penilaian", "Cara Penilaian", "iv")])
    vocab = vocab_rows(units)
    import datetime as _dt
    today = _dt.date.today().isoformat()
    nx = next((n for n in sorted(SCHEDULE) if SCHEDULE[n][0] >= today), 20)  # paparan awal; app.js mengemas kini mengikut masa sebenar
    sched_json = json.dumps({n: [SCHEDULE[n][0], units[n][0]["title"], SCHEDULE[n][1], SCHEDULE[n][2]] for n in SCHEDULE})
    body = f"""
<section class="cover-wrap">
  <div class="cover" role="img" aria-label="Kulit buku: Kursus Bahasa Melayu Online, Tahap Permulaan">
    <div class="cv-frame">
      <p class="cv-top"><span>Kursus Bahasa Melayu Secara Dalam Talian</span><span class="cv-th cv-jw" lang="ms-Arab" dir="rtl">{esc(jawi("Kursus Bahasa Melayu Secara Dalam Talian"))}</span></p>
      <div class="cv-mid">
        <p class="cv-year">Tahap Permulaan · <span class="cv-jw" lang="ms-Arab" dir="rtl">{esc(jawi("Tahap Permulaan"))}</span></p>
        <p class="cv-title">Bahasa Melayu<br>Standard</p>
        <p class="cv-sub">20 Pertemuan · 30 Jam</p>
      </div>
      <p class="cv-author"><span>1 November 2026 – 7 Mac 2027</span><span class="cv-th">Setiap Ahad, 2.00–3.30 petang (Masa Patani)</span></p>
    </div>
  </div>
  <div class="cover-side">
    <h1 class="side-h">Bahasa Melayu Standard, satu Ahad demi satu Ahad.</h1>
    <p class="lede">Kursus dalam talian 20 pertemuan untuk peserta di Selatan Thai. Setiap pertemuan membawa satu tema kehidupan seharian, lengkap dengan kosa kata, dialog, tatabahasa dan kuiz kendiri dalam tulisan Rumi dan Jawi.</p>
    <div class="actions"><a class="btn" href="#kandungan">Buka buku</a><a class="btn-ghost" href="pertemuan/01.html">Mula Pertemuan 1</a></div>
    <section class="next" id="kelas-seterusnya">
      <p class="next-label">Kelas seterusnya</p>
      <p class="next-body"><a id="next-link" href="pertemuan/{nx:02d}.html">Pertemuan {nx}: {esc(units[nx][0]["title"])} — Ahad, {SCHEDULE[nx][1]}, 2.00 petang bersama {esc(SCHEDULE[nx][2])}</a></p>
    </section>
    <figure class="contrast word" aria-live="polite">
      <p class="word-label">Kata hari ini</p>
      <div class="pair"><span class="std" id="w-ms">{esc(vocab[0][0])}</span><span class="th jw-word" id="w-jw" lang="ms-Arab" dir="rtl">{esc(vocab[0][1])}</span></div>
      <figcaption id="w-ex">{esc(vocab[0][2])}</figcaption>
      <div class="word-foot"><button type="button" class="btn-ghost" id="w-next">Kata lain</button><a id="w-link" href="pertemuan/{vocab[0][3]:02d}.html">Dari Pertemuan {vocab[0][3]}</a></div>
    </figure>
  </div>
</section>

<article class="sheet" id="kandungan">
  {running("Kandungan")}
  <h2 class="sheet-title">Kandungan{jw_span("Kandungan", "small")}</h2>
  {ORN}
  <ol class="toc">{front}{''.join(contents)}</ol>
  {folio("i")}
</article>

<article class="sheet" id="pengenalan">
  {running("Pengenalan Kursus")}
  <h2 class="sheet-title">Pengenalan Kursus{jw_span("Pengenalan Kursus", "small")}</h2>
  {ORN}
  <section class="facts" aria-label="Butiran kursus">
    <dl>
      <div><dt>Tempoh</dt><dd>30 jam (20 pertemuan, 1 jam 30 minit setiap satu)</dd></div>
      <div><dt>Tarikh</dt><dd>1 November 2026 – 7 Mac 2027</dd></div>
      <div><dt>Waktu</dt><dd>Setiap Ahad, 2.00–3.30 petang (Masa Patani)</dd></div>
      <div><dt>Platform</dt><dd>Zoom / Google Meet / Microsoft Teams</dd></div>
    </dl>
  </section>
  <h3>Keunikan modul</h3>
  <div class="two">
    <div><h4>Rumi dan Jawi</h4><p>Setiap kosa kata, frasa dan contoh ayat dipaparkan dalam tulisan Rumi bersama tulisan Jawi, supaya peserta dapat membaca kedua-dua tulisan dan mengulang kaji sendiri di rumah.</p></div>
    <div><h4>Fokus dalam talian</h4><p>Alat digital yang interaktif — Kahoot, Quizizz, Wordwall, Breakout Rooms — supaya peserta di Selatan Thai seronok belajar dan tidak terbeban.</p></div>
  </div>
  {folio("ii")}
</article>

<article class="sheet" id="jadual">
  {running("Jadual Kelas")}
  <h2 class="sheet-title">Jadual Kelas{jw_span("Jadual Kelas", "small")}</h2>
  {ORN}
  <p class="sub">Klik pada tajuk pertemuan untuk membuka kosa kata, dialog, tatabahasa, latihan dan kuiz kendiri.</p>
  <div class="table-wrap cards" role="region" aria-label="Jadual kelas" tabindex="0"><table class="sched"><thead><tr><th>#</th><th>Tarikh</th><th>Tajuk</th><th>Fokus kemahiran</th><th>Pengajar</th></tr></thead>{''.join(sched)}</table></div>
  {folio("iii")}
</article>

<article class="sheet assess" id="penilaian">
  {running("Cara Penilaian")}
  <h2 class="sheet-title">Cara Penilaian{jw_span("Cara Penilaian", "small")}</h2>
  {ORN}
  <div class="two">
    <div>
      <h3>Formatif (berterusan) — 60%</h3>
      <ul class="bars">
        <li><span>Kehadiran & penyertaan</span><b style="--w:20">20%</b><small>Keaktifan dalam sesi soal jawab di Zoom / Google Meet</small></li>
        <li><span>Kuiz mingguan</span><b style="--w:20">20%</b><small>Kahoot atau Quizizz untuk menguji tatabahasa</small></li>
        <li><span>Tugasan audio / video</span><b style="--w:20">20%</b><small>Rakaman pendek melalui WhatsApp untuk menilai sebutan</small></li>
      </ul>
    </div>
    <div>
      <h3>Sumatif (akhir) — 40%</h3>
      <ul class="bars">
        <li><span>Ujian lisan akhir</span><b style="--w:20">20%</b><small>Temu bual 5 minit satu-lawan-satu dengan guru dalam BMS</small></li>
        <li><span>Projek penulisan</span><b style="--w:20">20%</b><small>Esei 80–100 patah perkataan: "Diri Saya dan Masa Depan"</small></li>
      </ul>
    </div>
  </div>
  {folio("iv")}
</article>
<script>window.SCHEDULE = {sched_json}; window.VOCAB = {json.dumps(vocab, ensure_ascii=False)};</script>
"""
    (ROOT / "index.html").write_text(page("Kursus Bahasa Melayu Online — Tahap Permulaan", body, 0,
        "Kursus Bahasa Melayu secara dalam talian (tahap permulaan), 20 pertemuan, dalam tulisan Rumi dan Jawi, untuk penutur Melayu Selatan Thai.", "utama", ""), encoding="utf-8")


if __name__ == "__main__":
    u = build_units()
    build_index(u)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u_}</loc></url>\n" for u_ in sorted(SITEMAP)) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")
    print("Siap:", len(u), "pertemuan")
    jw_report()
