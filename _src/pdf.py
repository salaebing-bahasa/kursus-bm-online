#!/usr/bin/env python3
"""Jana PDF setiap pertemuan daripada halaman laman web (isi sama dengan laman web).

Cara guna (di folder akar repositori):
    python3 _src/build.py
    pip install playwright && playwright install chromium
    python3 _src/pdf.py
Output: pdf/pertemuan-01.pdf ... pertemuan-20.pdf
"""
import functools, http.server, re, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pdf"
FONT_DIR = sys.argv[sys.argv.index("--fontsource") + 1] if "--fontsource" in sys.argv else None  # pilihan: fon setempat


def local_fonts(page):
    """Jika Google Fonts tidak dapat dicapai, guna fail fon @fontsource setempat."""
    base = Path(FONT_DIR)
    css = []
    for pkg, weights in (("sarabun", ["400", "600", "400-italic"]), ("bai-jamjuree", ["500", "600", "700"]), ("noto-naskh-arabic", ["400", "600"])):
        for w in weights:
            t = (base / pkg / f"{w}.css").read_text()
            css.append(re.sub(r"url\(\./files/([^)]+)\)", rf"url(https://fonts.gstatic.com/local/{pkg}/\1)", t))
    page.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(body="\n".join(css), content_type="text/css"))
    page.route("https://fonts.gstatic.com/local/**", lambda r: r.fulfill(
        body=(base / r.request.url.split("/local/")[1].split("/")[0] / "files" / r.request.url.rsplit("/", 1)[1]).read_bytes(),
        content_type="font/woff2"))


def main():
    OUT.mkdir(exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    units = sorted((ROOT / "pertemuan").glob("*.html"))
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.route("**/gc.zgo.at/**", lambda r: r.abort())
        if FONT_DIR:
            local_fonts(page)
        for f in units:
            n = int(f.stem)
            page.goto(f"http://127.0.0.1:{port}/pertemuan/{f.name}", wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            title = page.evaluate("document.querySelector('.opener h1').firstChild.textContent.trim()")
            head = (f'<div style="font:8.5px Sarabun,sans-serif;color:#6b5a66;width:100%;padding:0 14mm;display:flex;justify-content:space-between">'
                    f'<span>Kursus Bahasa Melayu Online · Tahap Permulaan</span><span>Pertemuan {n} · {title}</span></div>')
            foot = ('<div style="font:9px Sarabun,sans-serif;color:#6b5a66;width:100%;text-align:center">'
                    '— <span class="pageNumber"></span> / <span class="totalPages"></span> —</div>')
            page.emulate_media(media="print")
            page.pdf(path=str(OUT / f"pertemuan-{n:02d}.pdf"), format="A4", print_background=True,
                     display_header_footer=True, header_template=head, footer_template=foot,
                     margin={"top": "18mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
            page.emulate_media(media="screen")
            print("PDF:", f"pertemuan-{n:02d}.pdf")
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
