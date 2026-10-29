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
