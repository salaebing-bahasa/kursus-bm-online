# Kursus Bahasa Melayu Online (Tahap Permulaan)

Laman web kursus 20 pertemuan (1 November 2026 – 7 Mac 2027, setiap Ahad 2.00–3.30 petang, Masa Patani).

## Struktur
- `index.html` — laman utama: jadual, kelas seterusnya, penilaian
- `pertemuan/01.html` … `20.html` — kosa kata, perbualan, tatabahasa, latihan dan kuiz kendiri
- `_src/units/*.md` — kandungan setiap pertemuan (sunting di sini)
- `_src/build.py` — bina semula HTML: `pip install markdown && python3 _src/build.py`

## Menyunting kandungan
Ubah fail `_src/units/NN.md`, kemudian jalankan `python3 _src/build.py`.
Jadual (tarikh, pengajar, fokus) ada dalam `SCHEDULE` di `_src/build.py`.

## Reka bentuk & kualiti
- Bentuk buku: kulit, Kandungan, helaian bernombor dan sudut kertas untuk tukar pertemuan.
- Di telefon: maklumat "Kelas seterusnya" dipaparkan dahulu; jadual kosa kata menjadi kad (tiada tatal ke sisi).
- Saiz huruf minimum 13 px (huruf Thai lebih besar), sasaran sentuh sekurang-kurangnya 44 px, kontras warna memenuhi WCAG AA (mod cerah dan gelap).
- `sitemap.xml` dan `robots.txt` dibina semula setiap kali `python3 _src/build.py` dijalankan.

## Nota PDF setiap pertemuan
- Butang "Muat turun PDF" di setiap pertemuan memuat turun `pdf/pertemuan-NN.pdf`.
- PDF dijana daripada halaman laman web, jadi isinya sentiasa sama dengan laman web.
- Selepas mengubah `_src/units/*.md`, bina semula HTML **dan** PDF:
  `python3 _src/build.py && python3 _src/pdf.py` (perlu `pip install playwright` dan `playwright install chromium`).
