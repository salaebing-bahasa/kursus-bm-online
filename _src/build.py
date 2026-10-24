#!/usr/bin/env python3
"""Bina laman web Kursus BM Online daripada fail _src/units/*.md.

Cara guna:  python3 _src/build.py
Output ditulis ke folder akar repositori (index.html, pertemuan/*.html, kontrastif.html).
"""
import html, json, re
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src" / "units"
GOATCOUNTER = "kursus-bm-online"  # kod laman GoatCounter

PHASES = [
    (1, 5, "Aktiviti Harian & Perhubungan (I)"),
    (6, 10, "Aktiviti Harian & Perhubungan (II)"),
    (11, 15, "Interaksi Sosial & Budaya"),
    (16, 20, "Pengukuhan & Komunikasi Formal"),
]

# (tarikh ISO, tarikh paparan, pengajar, fokus kemahiran & tatabahasa, aktiviti & penilaian)
SCHEDULE = {
    1: ("2026-11-01", "1 November 2026", "Prof. Madya Dr. Numan", "Sejarah dan perkembangan Bahasa Melayu di Nusantara", "Garis masa sejarah Bahasa Melayu"),
    2: ("2026-11-08", "8 November 2026", "Assist. Prof. Nawawi", "Mendengar: Vokal (a, e, i, o, u)", "Perbandingan bunyi 'makae' dan 'makan'"),
    3: ("2026-11-15", "15 November 2026", "Assist. Prof. Huda", "Bertutur: Kata Ganti Nama Diri (Saya, Awak, Anda)", "Lakonan simulasi perkenalan diri secara formal"),
    4: ("2026-11-22", "22 November 2026", "Dr. Abdonlah", "Membaca: Kata Nama Am & Kata Nama Khas", "Membina carta organisasi keluarga sendiri"),
    5: ("2026-11-29", "29 November 2026", "Dr. Samsina", "Mendengar: Kata Bilangan & Penjodoh Bilangan", "Kuiz spontan harga barang di pasar"),
    6: ("2026-12-06", "6 Disember 2026", "Dr. Uniansasmita", "Menulis: Kata Sifat (besar, bersih, jauh)", "Padanan gambar dengan perkataan yang betul"),
    7: ("2026-12-13", "13 Disember 2026", "Encik Lee", "Bertutur: Kata Kerja Transitif", "Vlog pendek \"Satu Jam dalam Hidup Saya\""),
    8: ("2026-12-20", "20 Disember 2026", "Cik Khadijah", "Membaca: Kata Kerja Tak Transitif", "Temu bual rakan sekelas tentang hobi"),
    9: ("2026-12-27", "27 Disember 2026", "Assist. Prof. Dr. Ilyas", "Mendengar: Kata Sendi Nama (di, ke, dari)", "Lukis peta berdasarkan arahan lisan guru"),
    10: ("2027-01-03", "3 Januari 2027", "Cik Rohani", "Bertutur: Ayat Perintah & Permintaan", "Simulasi memesan makanan secara dalam talian"),
    11: ("2027-01-10", "10 Januari 2027", "Cik Firdaos", "Menulis: Kata Hubung (dan, atau, tetapi)", "Menulis mesej ringkas kepada doktor"),
    12: ("2027-01-17", "17 Januari 2027", "Puan Kamilia", "Bertutur: Ayat Tanya (Berapa, Mana)", "Main peranan penjual dan pembeli"),
    13: ("2027-01-24", "24 Januari 2027", "Dr. Suhaila", "Membaca: Kata Adjektif Warna & Ukuran", "Persembahan slaid \"Fesyen Kegemaran Saya\""),
    14: ("2027-01-31", "31 Januari 2027", "Ustaz Abd. Ghani", "Mendengar: Penanda Wacana (Selain itu, Kemudian)", "Laporan cuaca kreatif ala berita TV"),
    15: ("2027-02-07", "7 Februari 2027", "Ustaz Nurdin", "Menulis: Imbuhan Awalan (meN-, ber-)", "Menulis kad ucapan digital untuk kawan"),
    16: ("2027-02-14", "14 Februari 2027", "Assist. Prof. Muhammad", "Membaca: Kata Pinjaman & Istilah ICT", "Mencari maklumat di laman berita Melayu"),
    17: ("2027-02-14", "14 Februari 2027", "Assist. Prof. Samiyah", "Bertutur: Ayat Penyata & Ayat Seruan", "Pembentangan \"Cita-cita Saya\""),
    18: ("2027-02-21", "21 Februari 2027", "Assist. Prof. Hasbullah", "Mendengar: Kata Tanya (Bagaimana, Mengapa)", "Membina itinerari pelancongan ringkas"),
    19: ("2027-02-28", "28 Februari 2027", "Dr. Pareeda & Puan Kartini", "Menulis: Membina Perenggan Mudah", "Menulis ulasan pendek tentang filem Melayu"),
    20: ("2027-03-07", "7 Mac 2027", "Dr. Pareeda, Puan Kartini, Assist. Prof. Muhammad & Dr. Uniansasmita", "Semua kemahiran: Pengukuhan tatabahasa", "Penilaian akhir: Pembentangan projek individu"),
}

SECTION_IDS = {"Objektif Pembelajaran": "objektif", "Kosa Kata": "kosa-kata", "Perbualan": "perbualan",
               "Tatabahasa": "tatabahasa", "Latihan": "latihan", "Kuiz": "kuiz"}
SECTION_TH = {"objektif": "วัตถุประสงค์", "kosa-kata": "คำศัพท์", "perbualan": "บทสนทนา",
              "tatabahasa": "ไวยากรณ์", "latihan": "แบบฝึกหัด", "kuiz": "แบบทดสอบ"}

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
    h = h.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return h


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


def contrast_pairs(md_text):
    """Ambil pasangan dialek → standard daripada jadual 'Fokus Sebutan'."""
    pairs = []
    for m in re.finditer(r"### Fokus Sebutan[^\n]*\n\n((?:\|.*\n?)+)", md_text):
        rows = table_rows(m.group(1).strip().splitlines())
        head = [h.lower() for h in rows[0]]
        di = next(k for k, h in enumerate(head) if "dialek" in h)
        si = next(k for k, h in enumerate(head) if "standard" in h or "bms" in h)
        for r in rows[1:]:
            clean = lambda s: re.sub(r"\*\*|\(elak\)", "", s).strip()
            pairs.append((clean(r[di]), clean(r[si])))
    return pairs


def page(title, body, depth=0, desc="", active=""):
    p = "../" * depth
    nav = [("index.html#jadual", "Jadual", "jadual"), ("kontrastif.html", "Dialek → Standard", "kontrastif"),
           ("index.html#penilaian", "Penilaian", "penilaian")]
    links = "".join(f'<a href="{p}{h}"{" aria-current=\"page\"" if a == active else ""}>{t}</a>' for h, t, a in nav)
    return f"""<!doctype html>
<html lang="ms">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bai+Jamjuree:wght@500;600;700&family=Sarabun:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
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
  <p>Bahan disediakan oleh pasukan pengajar kursus. Laman ini dikendalikan oleh Asst. Prof. Muhammad Salaebing, Universiti Thaksin.</p>
</footer>
<script src="{p}assets/app.js"></script>
<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
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
            toc.append(f'<li><a href="#{sid}">{esc(title)}<span lang="th">{SECTION_TH.get(sid, "")}</span></a></li>')
            inner = quiz_html(parse_quiz(content), n) if sid == "kuiz" else render_content(content)
            parts.append(f'<section class="block" id="{sid}"><h2>{esc(title)}</h2>{inner}</section>')
        prev_l = f'<a class="pn prev" href="{n-1:02d}.html"><small>Sebelumnya</small>{esc(units[n-1][0]["title"])}</a>' if n > 1 else "<span></span>"
        next_l = f'<a class="pn next" href="{n+1:02d}.html"><small>Seterusnya</small>{esc(units[n+1][0]["title"])}</a>' if n < 20 else "<span></span>"
        dl = ""
        if meta.get("docx"):
            dl += f'<a class="btn" href="https://drive.google.com/file/d/{meta["docx"]}/view" target="_blank" rel="noopener">Nota kuliah penuh (Word)</a>'
        if meta.get("pdf"):
            dl += f'<a class="btn-ghost" href="https://drive.google.com/file/d/{meta["pdf"]}/view" target="_blank" rel="noopener">Versi PDF</a>'
        prep = meta.get("penyediaan", "—")
        prep_html = f'<div><dt>Penyediaan bahan</dt><dd>{esc(prep)}</dd></div>' if prep not in ("", "—") else ""
        note17 = '<p class="flag">Tarikh dalam reka bentuk kursus sama dengan Pertemuan 16 — sila semak dengan penyelaras.</p>' if n == 17 else ""
        body = f"""
<article class="unit">
  <header class="unit-hero">
    <p class="unit-num"><span>Pertemuan {n}</span> <time datetime="{iso}">{date}</time></p>
    <h1>{esc(meta['title'])}</h1>
    <p class="unit-th" lang="th">{esc(meta.get('th',''))}</p>
    {note17}
    <dl class="unit-meta">
      <div><dt>Pengajar</dt><dd>{esc(teacher)}</dd></div>
      <div><dt>Fokus kemahiran</dt><dd>{esc(focus)}</dd></div>
      <div><dt>Aktiviti & penilaian</dt><dd>{esc(activity)}</dd></div>
      {prep_html}
    </dl>
    <div class="actions">{dl}</div>
  </header>
  <div class="unit-body">
    <nav class="toc" aria-label="Bahagian pelajaran"><ol>{''.join(toc)}</ol></nav>
    <div class="unit-main">{''.join(parts)}</div>
  </div>
  <nav class="prevnext" aria-label="Pertemuan lain">{prev_l}{next_l}</nav>
</article>"""
        (out_dir / f"{n:02d}.html").write_text(
            page(f"P{n}: {meta['title']} — Kursus BM Online", body, 1, f"Pertemuan {n}: {meta['title']}"), encoding="utf-8")
    return units


def build_index(units):
    rows = []
    for a, b, name in PHASES:
        items = []
        for n in range(a, b + 1):
            iso, date, teacher, focus, activity = SCHEDULE[n]
            t = units[n][0]["title"]
            items.append(f"""<li class="session" data-date="{iso}">
  <a href="pertemuan/{n:02d}.html">
    <span class="s-num">{n}</span>
    <span class="s-date"><time datetime="{iso}">{date}</time></span>
    <span class="s-title">{esc(t)}<span lang="th">{esc(units[n][0].get('th',''))}</span></span>
    <span class="s-focus">{esc(focus)}</span>
    <span class="s-teacher">{esc(teacher)}</span>
  </a></li>""")
        rows.append(f'<section class="phase"><h3><span>Pertemuan {a}–{b}</span>{esc(name)}</h3><ol class="sessions">{"".join(items)}</ol></section>')
    sched_json = json.dumps({n: [SCHEDULE[n][0], units[n][0]["title"], SCHEDULE[n][1], SCHEDULE[n][2]] for n in SCHEDULE})
    body = f"""
<section class="hero">
  <div class="hero-text">
    <h1>Dari dialek ke bahasa standard, satu Ahad demi satu Ahad.</h1>
    <p class="lede">Kursus dalam talian 20 pertemuan untuk penutur Melayu Selatan Thai. Kita mulakan dengan apa yang sudah anda tahu — dialek ibunda — dan belajar memakai Bahasa Melayu Standard sebagai "pakaian rasmi" mengikut tempat.</p>
    <div class="actions"><a class="btn" href="#jadual">Lihat jadual kelas</a><a class="btn-ghost" href="pertemuan/01.html">Mula dari Pertemuan 1</a></div>
  </div>
  <figure class="contrast" aria-live="polite">
    <div class="pair"><span class="dia" id="c-dia">makae</span><span class="arrow" aria-hidden="true"></span><span class="std" id="c-std">makan</span></div>
    <figcaption>Dalam dialek kita sebut <b id="c-dia2">makae</b>. Dalam bahasa standard kita sebut <b id="c-std2">makan</b>.</figcaption>
    <button type="button" class="btn-ghost" id="c-next">Contoh lain</button>
  </figure>
</section>

<section class="next" id="kelas-seterusnya" hidden>
  <p class="next-label">Kelas seterusnya</p>
  <p class="next-body"><a id="next-link" href="#"></a></p>
</section>

<section class="facts" aria-label="Butiran kursus">
  <dl>
    <div><dt>Tempoh</dt><dd>30 jam (20 pertemuan, 1 jam 30 minit setiap satu)</dd></div>
    <div><dt>Tarikh</dt><dd>1 November 2026 – 7 Mac 2027</dd></div>
    <div><dt>Waktu</dt><dd>Setiap Ahad, 2.00–3.30 petang (Masa Patani)</dd></div>
    <div><dt>Platform</dt><dd>Zoom / Google Meet / Microsoft Teams</dd></div>
  </dl>
</section>

<section class="schedule" id="jadual">
  <h2>Jadual 20 pertemuan</h2>
  <p class="sub">Klik pada pertemuan untuk membuka kosa kata, dialog, tatabahasa, latihan dan kuiz kendiri.</p>
  {''.join(rows)}
</section>

<section class="unique">
  <h2>Keunikan modul</h2>
  <div class="two">
    <div><h3>Pendekatan kontrastif</h3><p>Guru sentiasa membandingkan: "Dalam dialek kita sebut begini, dalam bahasa standard sebut begini." Semua pasangan bunyi yang dipelajari dikumpulkan di halaman <a href="kontrastif.html">Dialek → Standard</a>.</p></div>
    <div><h3>Fokus dalam talian</h3><p>Alat digital yang interaktif — Kahoot, Quizizz, Wordwall, Breakout Rooms — supaya peserta di Selatan Thai seronok belajar dan tidak terbeban.</p></div>
  </div>
</section>

<section class="assess" id="penilaian">
  <h2>Cara penilaian</h2>
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
</section>
<script>window.SCHEDULE = {sched_json};</script>
"""
    (ROOT / "index.html").write_text(page("Kursus Bahasa Melayu Online — Tahap Permulaan", body, 0,
        "Kursus Bahasa Melayu secara dalam talian (tahap permulaan) untuk penutur Melayu Selatan Thai."), encoding="utf-8")


def build_contrast(units):
    groups, allpairs = [], []
    for n, (meta, _, raw) in units.items():
        pairs = contrast_pairs(raw)
        if not pairs:
            continue
        allpairs += pairs
        lis = "".join(f'<li><span class="dia">{esc(d)}</span><span class="arrow" aria-hidden="true"></span><span class="std">{esc(s)}</span></li>' for d, s in pairs)
        groups.append(f'<section class="cgroup"><h2><a href="pertemuan/{n:02d}.html">Pertemuan {n}: {esc(meta["title"])}</a></h2><ul class="clist">{lis}</ul></section>')
    body = f"""
<section class="page-head">
  <h1>Dialek → Standard</h1>
  <p class="lede">Semua pasangan sebutan yang dibandingkan dalam kursus ini — {len(allpairs)} pasangan daripada {len(groups)} pertemuan. Kiri: sebutan dialek Patani. Kanan: Bahasa Melayu Standard.</p>
  <label class="search"><span>Cari perkataan</span><input type="search" id="csearch" placeholder="contoh: makan, abang, mahal"></label>
</section>
<div class="cgroups">{''.join(groups)}</div>
"""
    (ROOT / "kontrastif.html").write_text(page("Dialek → Standard — Kursus BM Online", body, 0,
        "Senarai pasangan sebutan dialek Patani dan Bahasa Melayu Standard.", "kontrastif"), encoding="utf-8")
    (ROOT / "assets" / "pairs.json").write_text(json.dumps(allpairs, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    u = build_units()
    build_index(u)
    build_contrast(u)
    print("Siap:", len(u), "pertemuan")
