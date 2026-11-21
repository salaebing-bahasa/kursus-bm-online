/* Akaun peserta · ระบบบัญชีผู้เรียน (Firebase Authentication + Firestore)
   - Halaman pertemuan, kemajuan.html, kata.html, sijil.html dan senarai.html memerlukan log masuk Google
   - bmonline/{uid}            { nama, emel, setuju, dicipta, kemaskini, buka[], kuiz{n:{ok,all,best,cuba,t}}, namaSijil, sijil }
   - bmonline/{uid}/jawapan/*  { n, item, soalan, jawapan, betul, masa }       (setiap jawapan kuiz)
   - bmonline/{uid}/kata/*     { kata, jawi, contoh, contohJawi, n, hafal, ulang, masa }
   - Projek Firebase dikongsi dengan laman 0113131 (tatabahasa-melayu); peraturan keselamatan
     ada dalam fail firestore.rules repo tatabahasa-melayu
   Teks Rumi + Jawi datang daripada window.AKAUN_TEKS (dibina oleh _src/build.py) */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signInWithRedirect, getRedirectResult, signOut }
  from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc, addDoc, deleteDoc, getDocs, collection, query, orderBy, limit, serverTimestamp, arrayUnion }
  from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const fb = initializeApp({
  apiKey: "AIzaSyBHtc0YDkMZmFjkrFC1zduyQjETAj2WGzk",
  authDomain: "tatabahasa-melayu.firebaseapp.com",
  projectId: "tatabahasa-melayu",
  storageBucket: "tatabahasa-melayu.firebasestorage.app",
  messagingSenderId: "657023566026",
  appId: "1:657023566026:web:8ef67ded91089adbf73433"
});
const auth = getAuth(fb), db = getFirestore(fb);
const provider = new GoogleAuthProvider(); provider.setCustomParameters({ prompt: "select_account" });
const KOLEKSI = "bmonline";
const VERSI_SETUJU = 2;          // v2: kemajuan, markah, jawapan dan buku kata turut disimpan
const JUMLAH = 20, LULUS = 0.6;  // 20 pertemuan; lulus kuiz ≥ 60%
const GURU = ["salaebing@gmail.com", "smuhammad@tsu.ac.th"]; // mesti sama dengan isGuru() dalam firestore.rules

const T = window.AKAUN_TEKS || {}, TAJUK = window.BM_TAJUK || {};
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const r = k => (T[k] ? T[k][0] : k);
/* Rumi dengan baris Jawi di bawahnya · ข้อความรูมีพร้อมยาวีด้านล่าง */
const tx = (k, tag = "span") => `<${tag} class="rm">${esc(r(k))}</${tag}>${T[k] && T[k][1] ? `<${tag} class="jw" lang="ms-Arab" dir="rtl">${esc(T[k][1])}</${tag}>` : ""}`;
const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
const keMs = t => t && t.toMillis ? t.toMillis() : (typeof t === "number" ? t : 0);
const pct = (a, b) => b ? Math.round(a / b * 100) : 0;
const tarikh = t => t ? new Date(t).toLocaleString("ms-MY", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";
const tarikhPanjang = t => new Date(t).toLocaleDateString("ms-MY", { day: "numeric", month: "long", year: "numeric" });
const pintu = $("#pintu");
const nPertemuan = (() => { const m = location.pathname.match(/pertemuan\/(\d+)\.html/); return m ? +m[1] : null; })();
const halaman = $("#bm-halaman") ? $("#bm-halaman").dataset.halaman : null;
let pengguna = null, rek = null;
const guruKah = () => !!(pengguna && pengguna.emailVerified && GURU.includes(String(pengguna.email || "").toLowerCase()));
const ref = () => doc(db, KOLEKSI, pengguna.uid);

function buka() { document.documentElement.classList.remove("kunci"); if (pintu) pintu.innerHTML = ""; }
function kunci(html) { document.documentElement.classList.add("kunci"); if (pintu) pintu.innerHTML = `<div class="pintu-kad">${html}</div>`; }
function pintuLogMasuk(nota) {
  kunci(`<h1>${tx("tajuk")}</h1><p>${tx("isi")}</p>
    ${nota ? `<p class="pintu-nota-merah">${tx(nota)}</p>` : ""}
    <button type="button" class="btn pintu-btn" id="pintu-masuk"><svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg><span>${tx("butang")}</span></button>
    <p class="pintu-nota">${tx("data")}</p>`);
  $("#pintu-masuk").onclick = masuk;
}
async function masuk() {
  try { await signInWithPopup(auth, provider); }
  catch (e) {
    if (e && (e.code === "auth/popup-blocked" || e.code === "auth/operation-not-supported-in-this-environment")) { await signInWithRedirect(auth, provider); return; }
    if (e && (e.code === "auth/popup-closed-by-user" || e.code === "auth/cancelled-popup-request")) return;
    console.error(e);
  }
}
function mintaSetuju() {
  return new Promise(resolve => {
    kunci(`<h1>${tx("setuju_tajuk")}</h1><p>${tx("data")}</p><p>${tx("padam")}</p>
      <div class="pintu-butang"><button type="button" class="btn-ghost" id="st-tidak">${tx("tidak")}</button><button type="button" class="btn" id="st-ya">${tx("ya")}</button></div>`);
    $("#st-ya").onclick = () => resolve(true);
    $("#st-tidak").onclick = () => resolve(false);
  });
}

/* ---------- Menu akaun di pengepala · เมนูบัญชีที่แถบบน ---------- */
function cip() {
  let c = $("#akaun-cip");
  if (!pengguna) { if (c) c.remove(); return; }
  if (!c) { c = document.createElement("div"); c.id = "akaun-cip"; c.className = "akaun-cip"; const h = $(".site-head"); if (h) h.appendChild(c); }
  const akar = location.pathname.includes("/pertemuan/") ? "../" : "";
  c.innerHTML = `<button type="button" class="akaun-btn" id="akaun-btn" aria-expanded="false" aria-controls="akaun-menu"><span class="akaun-huruf" aria-hidden="true">${esc((pengguna.displayName || pengguna.email || "?").trim().charAt(0).toUpperCase())}</span><span class="akaun-nama">${esc(pengguna.displayName || pengguna.email || "")}</span></button>
    <div class="akaun-menu" id="akaun-menu" hidden>
      <a href="${akar}kemajuan.html">${tx("kemajuan")}</a>
      <a href="${akar}kata.html">${tx("buku_kata")}</a>
      <a href="${akar}sijil.html">${tx("sijil")}</a>
      ${guruKah() ? `<a href="${akar}senarai.html">${tx("senarai")}</a>` : ""}
      <button type="button" class="akaun-keluar" id="akaun-keluar">${tx("keluar")}</button>
    </div>`;
  const b = $("#akaun-btn"), m = $("#akaun-menu");
  b.onclick = e => { e.stopPropagation(); m.hidden = !m.hidden; b.setAttribute("aria-expanded", String(!m.hidden)); };
  $("#akaun-keluar").onclick = () => signOut(auth);
}
document.addEventListener("click", e => { const m = $("#akaun-menu"); if (m && !m.hidden && !m.contains(e.target)) { m.hidden = true; const b = $("#akaun-btn"); if (b) b.setAttribute("aria-expanded", "false"); } });
document.addEventListener("keydown", e => { const m = $("#akaun-menu"); if (e.key === "Escape" && m && !m.hidden) { m.hidden = true; $("#akaun-btn").focus(); } });

/* ---------- Selepas log masuk · หลังล็อกอิน ---------- */
async function selepasMasuk(u) {
  let ada = {};
  try { const s = await getDoc(doc(db, KOLEKSI, u.uid)); ada = s.exists() ? s.data() : {}; }
  catch (e) { console.error(e); kunci(`<p>${tx("gagal")}</p><button type="button" class="btn" onclick="location.reload()">${tx("muat_semula")}</button>`); return; }
  const perluSetuju = (ada.setuju && ada.setuju.versi) !== VERSI_SETUJU;
  if (perluSetuju && !(await mintaSetuju())) { await signOut(auth); pintuLogMasuk("ditolak"); return; }
  const data = { nama: u.displayName || "", emel: u.email || "", kemaskini: serverTimestamp() };
  if (!ada.dicipta) data.dicipta = serverTimestamp();
  if (perluSetuju) data.setuju = { versi: VERSI_SETUJU, masa: serverTimestamp() };
  if (nPertemuan) data.buka = arrayUnion(nPertemuan);
  try { await setDoc(doc(db, KOLEKSI, u.uid), data, { merge: true }); } catch (e) { console.error(e); }
  pengguna = u;
  rek = { ...ada, buka: [...new Set([...(ada.buka || []), ...(nPertemuan ? [nPertemuan] : [])])], kuiz: ada.kuiz || {} };
  cip(); buka();
  if (nPertemuan) butangKata();
  if ($("#senarai-peserta")) halamanGuru();
  if (halaman === "kemajuan") halamanKemajuan();
  if (halaman === "kata") halamanKata();
  if (halaman === "sijil") halamanSijil();
}

/* ---------- Rekod jawapan dan markah kuiz · บันทึกคำตอบและคะแนน ---------- */
window.addEventListener("bm:jawab", e => {
  if (!pengguna || !nPertemuan) return;
  const d = e.detail || {};
  addDoc(collection(db, KOLEKSI, pengguna.uid, "jawapan"), { n: nPertemuan, item: Number(d.item) || 0, soalan: String(d.soalan || "").slice(0, 300),
    jawapan: String(d.jawapan || "").slice(0, 300), betul: !!d.betul, masa: serverTimestamp() }).catch(err => console.error(err));
});
window.addEventListener("bm:kuiz", e => {
  if (!pengguna || !nPertemuan || !rek) return;
  const { ok, all } = e.detail || {}, lama = rek.kuiz[nPertemuan] || {};
  const k = { ok, all, best: Math.max(lama.best || 0, ok), cuba: (lama.cuba || 0) + 1, t: Date.now() };
  rek.kuiz[nPertemuan] = k;
  setDoc(ref(), { kuiz: { [nPertemuan]: k }, kemaskini: serverTimestamp() }, { merge: true }).catch(err => console.error(err));
});

const statusN = (n, d = rek) => {
  const k = (d.kuiz || {})[n], dibuka = (d.buka || []).includes(n), lulus = !!k && k.best / k.all >= LULUS;
  return { k, dibuka, lulus };
};
const layakSijil = d => Array.from({ length: JUMLAH }, (_, i) => statusN(i + 1, d)).every(s => s.lulus);

/* ---------- Butang simpan kata pada jadual kosa kata · ปุ่มเก็บคำในตารางคำศัพท์ ---------- */
let cacheKata = null;
const slug = k => String(k).toLowerCase().normalize("NFKC").trim().replace(/[\s/]+/g, "-").replace(/[^\p{L}\p{N}\-']/gu, "").slice(0, 60) || "kata";
async function senaraiKata() {
  if (!cacheKata) { const s = await getDocs(collection(db, KOLEKSI, pengguna.uid, "kata")); cacheKata = new Map(s.docs.map(d => [d.id, { id: d.id, ...d.data(), masa: keMs(d.data().masa) }])); }
  return cacheKata;
}
async function butangKata() {
  const rows = $$("#kosa-kata tbody tr"); if (!rows.length) return;
  let ada; try { ada = await senaraiKata(); } catch (e) { console.error(e); return; }
  rows.forEach(tr => {
    const td = tr.cells[0], td2 = tr.cells[1]; if (!td || $(".kata-btn", td)) return;
    const bersih = el => { const c = el.cloneNode(true); $$(".jw, .kata-btn", c).forEach(x => x.remove()); return c.textContent.replace(/\s+/g, " ").trim(); };
    const kata = bersih(td), jw = ($(".jw", td) || {}).textContent || "";
    const contoh = td2 ? bersih(td2) : "", contohJw = td2 && $(".jw", td2) ? $(".jw", td2).textContent : "";
    const id = slug(kata), b = document.createElement("button");
    b.type = "button"; b.className = "kata-btn";
    const lukis = () => { const s = ada.has(id); b.textContent = s ? "★" : "☆"; b.setAttribute("aria-pressed", String(s)); b.setAttribute("aria-label", `${r(s ? "disimpan" : "simpan_kata")}: ${kata}`); b.title = r(s ? "disimpan" : "simpan_kata"); };
    lukis();
    b.onclick = async () => {
      if (ada.has(id)) return;
      const rec = { kata: kata.slice(0, 60), jawi: jw.slice(0, 120), contoh: contoh.slice(0, 300), contohJawi: contohJw.slice(0, 400), n: nPertemuan, hafal: false, ulang: 0 };
      try { await setDoc(doc(db, KOLEKSI, pengguna.uid, "kata", id), { ...rec, masa: serverTimestamp() }); ada.set(id, { id, ...rec, masa: Date.now() }); lukis(); } catch (e) { console.error(e); }
    };
    td.insertBefore(b, td.firstChild);
  });
}

/* ---------- Kemajuan Saya · ความก้าวหน้าของฉัน ---------- */
function halamanKemajuan() {
  const el = $("#bm-isi"), st = Array.from({ length: JUMLAH }, (_, i) => ({ n: i + 1, ...statusN(i + 1) }));
  const dibuka = st.filter(s => s.dibuka).length, lulus = st.filter(s => s.lulus).length, sk = st.filter(s => s.k);
  const purata = sk.length ? Math.round(sk.reduce((a, s) => a + s.k.best / s.k.all, 0) / sk.length * 100) : null;
  el.innerHTML = `<div class="bm-kad-baris">
      <div class="bm-kad"><p class="bm-label">${tx("pertemuan_dibuka")}</p><p class="bm-nilai">${dibuka}<small> / ${JUMLAH}</small></p><div class="bm-bar"><span style="width:${pct(dibuka, JUMLAH)}%"></span></div></div>
      <div class="bm-kad"><p class="bm-label">${tx("kuiz_lulus")}</p><p class="bm-nilai">${lulus}<small> / ${JUMLAH}</small></p><div class="bm-bar"><span style="width:${pct(lulus, JUMLAH)}%"></span></div></div>
      <div class="bm-kad"><p class="bm-label">${tx("purata")}</p><p class="bm-nilai">${purata == null ? "—" : purata + "<small>%</small>"}</p></div>
    </div>
    <p class="bm-pautan"><a class="btn" href="kata.html">${tx("buku_kata")}</a> <a class="btn-ghost" href="sijil.html">${tx("sijil")}</a></p>
    <ol class="bm-senarai">${st.map(s => `<li class="${s.lulus ? "bm-lulus" : s.k ? "bm-ulang" : s.dibuka ? "bm-dibuka" : ""}">
      <span class="bm-no">${s.lulus ? "✓" : s.n}</span>
      <a href="pertemuan/${String(s.n).padStart(2, "0")}.html"><span class="rm">Pertemuan ${s.n}: ${esc(TAJUK[s.n] || "")}</span></a>
      <span class="bm-status">${s.k ? `${tx("kuiz")} ${s.k.best}/${s.k.all} · ${tx(s.lulus ? "lulus" : "ulang")}` : tx(s.dibuka ? "dibuka" : "belum")}</span></li>`).join("")}</ol>`;
}

/* ---------- Buku Kata Saya · สมุดคำศัพท์ ---------- */
async function halamanKata() {
  const el = $("#bm-isi");
  let ls; try { ls = [...(await senaraiKata()).values()].sort((a, b) => (b.masa || 0) - (a.masa || 0)); } catch (e) { console.error(e); el.innerHTML = `<p>${tx("gagal")}</p>`; return; }
  if (!ls.length) { el.innerHTML = `<p class="bm-kosong">${tx("kata_kosong")}</p>`; return; }
  el.innerHTML = `<p class="bm-pautan">${ls.some(x => !x.hafal) ? `<button type="button" class="btn" id="kt-kad">${tx("ulang_kaji")}</button>` : ""}</p>
    <ul class="kt-senarai">${ls.map(x => `<li class="kt-kad${x.hafal ? " kt-hafal" : ""}" data-id="${esc(x.id)}">
      <p class="kt-kata">${esc(x.kata)}</p>${x.jawi ? `<p class="jw" lang="ms-Arab" dir="rtl">${esc(x.jawi)}</p>` : ""}
      ${x.contoh ? `<p class="kt-contoh">${esc(x.contoh)}</p>${x.contohJawi ? `<p class="jw" lang="ms-Arab" dir="rtl">${esc(x.contohJawi)}</p>` : ""}` : ""}
      <div class="kt-kaki">${x.n ? `<a href="pertemuan/${String(x.n).padStart(2, "0")}.html">Pertemuan ${x.n}</a>` : "<span></span>"}
        <label class="kt-cek"><input type="checkbox" data-hafal${x.hafal ? " checked" : ""}> ${tx("ingat")}</label>
        <button type="button" class="kt-padam" data-padam>${tx("padam_kata")}</button></div></li>`).join("")}</ul>`;
  el.onchange = e => {
    if (!e.target.matches("[data-hafal]")) return;
    const li = e.target.closest("[data-id]"), id = li.dataset.id, v = e.target.checked;
    li.classList.toggle("kt-hafal", v); cacheKata.get(id).hafal = v;
    setDoc(doc(db, KOLEKSI, pengguna.uid, "kata", id), { hafal: v }, { merge: true }).catch(err => console.error(err));
  };
  el.onclick = async e => {
    if (!e.target.closest("[data-padam]")) return;
    const li = e.target.closest("[data-id]"), id = li.dataset.id;
    try { await deleteDoc(doc(db, KOLEKSI, pengguna.uid, "kata", id)); cacheKata.delete(id); li.remove(); } catch (err) { console.error(err); }
  };
  const kb = $("#kt-kad"); if (kb) kb.onclick = () => kadImbas(ls.filter(x => !x.hafal));
}
function kadImbas(set) {
  const el = $("#bm-isi"), kad = set.slice().sort(() => Math.random() - .5); let i = 0;
  el.onclick = null; el.onchange = null;
  const lukis = () => {
    if (i >= kad.length) { el.innerHTML = `<p class="bm-siap">✓</p><p class="bm-pautan"><button type="button" class="btn" id="kt-balik">${tx("kembali")}</button></p>`; $("#kt-balik").onclick = () => halamanKata(); return; }
    const x = kad[i];
    el.innerHTML = `<p class="kt-prog">${i + 1} / ${kad.length}</p>
      <button type="button" class="kt-imbas" id="kt-pusing"><span class="kt-depan"><span class="kt-besar">${esc(x.kata)}</span>${x.jawi ? `<span class="jw kt-besar-jw" lang="ms-Arab" dir="rtl">${esc(x.jawi)}</span>` : ""}<small>${tx("tekan_kad")}</small></span>
        <span class="kt-belakang" hidden><span class="kt-contoh">${esc(x.contoh || "")}</span>${x.contohJawi ? `<span class="jw" lang="ms-Arab" dir="rtl">${esc(x.contohJawi)}</span>` : ""}</span></button>
      <div class="pintu-butang"><button type="button" class="btn-ghost" data-j="0">${tx("belum_ingat")}</button><button type="button" class="btn" data-j="1">${tx("ingat")}</button></div>
      <p class="bm-pautan"><button type="button" class="kt-padam" id="kt-henti">${tx("selesai")}</button></p>`;
    $("#kt-pusing").onclick = () => { $(".kt-depan").hidden = !$(".kt-depan").hidden; $(".kt-belakang").hidden = !$(".kt-belakang").hidden; };
    $("#kt-henti").onclick = () => halamanKata();
    $$("[data-j]", el).forEach(b => b.onclick = () => {
      const ok = b.dataset.j === "1"; x.ulang = (x.ulang || 0) + 1; if (ok) x.hafal = true;
      setDoc(doc(db, KOLEKSI, pengguna.uid, "kata", x.id), { ulang: x.ulang, ...(ok ? { hafal: true } : {}) }, { merge: true }).catch(err => console.error(err));
      i++; lukis();
    });
  };
  lukis();
}

/* ---------- Sijil penyertaan · ใบประกาศนียบัตร ---------- */
async function halamanSijil() {
  const el = $("#bm-isi");
  if (!layakSijil(rek)) {
    const lulus = Array.from({ length: JUMLAH }, (_, i) => statusN(i + 1)).filter(s => s.lulus).length;
    el.innerHTML = `<p>${tx("sijil_syarat")}</p><p class="bm-nilai">${lulus}<small> / ${JUMLAH}</small></p><div class="bm-bar"><span style="width:${pct(lulus, JUMLAH)}%"></span></div>
      <p class="bm-pautan"><a class="btn" href="kemajuan.html">${tx("kemajuan")}</a></p>`;
    return;
  }
  if (!rek.namaSijil) {
    el.innerHTML = `<form class="sj-borang" id="sj-borang"><label>${tx("nama_sijil")}<input name="nama" required maxlength="100" value="${esc(pengguna.displayName || "")}"></label><button type="submit" class="btn">${tx("simpan")}</button></form>`;
    $("#sj-borang").onsubmit = async e => {
      e.preventDefault(); const n = e.target.nama.value.trim().replace(/\s+/g, " "); if (!n) return;
      rek.namaSijil = n;
      try { await setDoc(ref(), { namaSijil: n }, { merge: true }); } catch (err) { console.error(err); }
      halamanSijil();
    };
    return;
  }
  if (!rek.sijil) { const s = { kod: `BMO-2569-${pengguna.uid.slice(0, 6).toUpperCase()}`, masa: Date.now() }; rek.sijil = s; setDoc(ref(), { sijil: { kod: s.kod, masa: serverTimestamp() } }, { merge: true }).catch(err => console.error(err)); }
  const t = keMs(rek.sijil.masa) || Date.now();
  document.body.classList.add("ada-sijil");
  el.innerHTML = `<p class="bm-pautan sj-alat"><button type="button" class="btn" id="sj-cetak">${tx("cetak")}</button></p>
    <div class="sj-kertas"><div class="sj-bingkai">
      <p class="sj-kursus">Kursus Bahasa Melayu Secara Dalam Talian · Tahap Permulaan</p>
      <p class="sj-tajuk">Sijil Penyertaan</p><p class="jw sj-tajuk-jw" lang="ms-Arab" dir="rtl">${esc(T.sijil ? T.sijil[1] : "")}</p>
      <p class="sj-kecil">Dengan ini diperakui bahawa</p>
      <p class="sj-nama">${esc(rek.namaSijil)}</p>
      <p class="sj-isi">telah mengikuti Kursus Bahasa Melayu Secara Dalam Talian (Tahap Permulaan) sebanyak 20 pertemuan dan lulus kuiz kendiri setiap pertemuan, 1 November 2026 hingga 14 Mac 2027.</p>
      <div class="sj-kaki"><div><p>${tarikhPanjang(t)}</p></div>
        <div class="sj-ttd"><span class="sj-garis"></span><p>Asst. Prof. Muhammad Salaebing</p><p class="sj-kecil">Bagi pihak pasukan pengajar kursus</p></div></div>
      <p class="sj-nombor">No. sijil ${esc(rek.sijil.kod)}</p>
    </div></div>`;
  $("#sj-cetak").onclick = () => window.print();
}

/* ---------- Halaman pengajar (senarai.html) · หน้าอาจารย์ ---------- */
async function halamanGuru() {
  const el = $("#senarai-peserta");
  if (!guruKah()) { el.innerHTML = `<p>${tx("senarai_guru")}</p>`; return; }
  el.innerHTML = `<p class="pintu-muat">${tx("memuat")}…</p>`;
  try {
    const s = await getDocs(collection(db, KOLEKSI));
    const ls = s.docs.map(d => ({ uid: d.id, ...d.data(), dicipta: keMs(d.data().dicipta), kemaskini: keMs(d.data().kemaskini) })).filter(p => !GURU.includes(String(p.emel || "").toLowerCase()));
    await Promise.all(ls.map(async p => { const j = await getDocs(query(collection(db, KOLEKSI, p.uid, "jawapan"), orderBy("masa", "desc"), limit(3000))).catch(() => null); p.jawapan = j ? j.docs.map(d => ({ ...d.data(), masa: keMs(d.data().masa) })) : []; }));
    ls.forEach(p => {
      const st = Array.from({ length: JUMLAH }, (_, i) => statusN(i + 1, p)), sk = st.filter(x => x.k);
      Object.assign(p, { nBuka: st.filter(x => x.dibuka).length, nKuiz: sk.length, nLulus: st.filter(x => x.lulus).length, layak: st.every(x => x.lulus),
        purata: sk.length ? Math.round(sk.reduce((a, x) => a + x.k.best / x.k.all, 0) / sk.length * 100) : null, st });
    });
    ls.sort((a, b) => b.kemaskini - a.kemaskini);
    const aktif = ls.filter(p => p.kemaskini > Date.now() - 7 * 864e5).length;
    const pk = ls.filter(p => p.purata != null), purata = pk.length ? Math.round(pk.reduce((a, p) => a + p.purata, 0) / pk.length) : null;
    const m = new Map();
    ls.forEach(p => p.jawapan.forEach(j => { const k = `${j.n}|${j.soalan}`; const o = m.get(k) || { n: j.n, soalan: j.soalan, cuba: 0, salah: 0, orang: new Set(), salahOrang: new Set(), jw: {} }; o.cuba++; o.orang.add(p.uid); if (!j.betul) { o.salah++; o.salahOrang.add(p.uid); o.jw[j.jawapan] = (o.jw[j.jawapan] || 0) + 1; } m.set(k, o); }));
    const sukar = [...m.values()].filter(o => o.salah).sort((a, b) => b.salahOrang.size - a.salahOrang.size || b.salah / b.cuba - a.salah / a.cuba).slice(0, 15);
    el.innerHTML = `<div class="bm-kad-baris">
        <div class="bm-kad"><p class="bm-label">${tx("peserta")}</p><p class="bm-nilai">${ls.length}</p></div>
        <div class="bm-kad"><p class="bm-label">${tx("aktif")}</p><p class="bm-nilai">${aktif}</p></div>
        <div class="bm-kad"><p class="bm-label">${tx("purata")}</p><p class="bm-nilai">${purata == null ? "—" : purata + "<small>%</small>"}</p></div>
        <div class="bm-kad"><p class="bm-label">${tx("sijil")}</p><p class="bm-nilai">${ls.filter(p => p.layak).length}</p></div>
      </div>
      <p class="bm-pautan"><button type="button" class="btn" id="sn-csv">${tx("muat_turun")} (CSV)</button> <button type="button" class="btn-ghost" id="sn-csv2">${tx("muat_turun_jawapan")} (CSV)</button></p>
      <div class="tbl-wrap"><table><thead><tr><th>#</th><th>${tx("nama")}</th><th>${tx("pertemuan_dibuka")}</th><th>${tx("kuiz_lulus")}</th><th>${tx("purata")}</th><th>${tx("terakhir")}</th></tr></thead>
      <tbody>${ls.map((p, i) => `<tr><td>${i + 1}</td><td><b>${esc(p.nama)}</b><br><small>${esc(p.emel)}</small>${p.layak ? " 🎓" : ""}</td><td>${p.nBuka}/${JUMLAH}</td><td>${p.nLulus}/${JUMLAH}</td><td>${p.purata == null ? "—" : p.purata + "%"}</td><td>${tarikh(p.kemaskini)}</td></tr>`).join("")}</tbody></table></div>
      <h2 class="bm-h2">${tx("soalan_sukar")}</h2>
      ${sukar.length ? `<ol class="bm-sukar">${sukar.map(o => `<li><p><b>${esc(o.soalan)}</b></p><p class="bm-kecil">Pertemuan ${o.n} · ${o.salahOrang.size}/${o.orang.size} ${esc(r("orang"))} · ${o.salah}/${o.cuba} (${pct(o.salah, o.cuba)}%)</p>
        <p class="bm-kecil">${esc(r("jawapan_salah"))}: ${Object.entries(o.jw).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([w, n]) => `<b>${esc(w)}</b> (${n})`).join(", ")}</p></li>`).join("")}</ol>` : "<p>—</p>"}`;
    const z = n => String(n).padStart(2, "0"), f = t => { if (!t) return ""; const d = new Date(t); return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())} ${z(d.getHours())}:${z(d.getMinutes())}`; };
    const csv = (nama, rows) => {
      const sel = v => { let t = String(v == null ? "" : v); if (/^[=+\-@]/.test(t)) t = "'" + t; return /[",\r\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["﻿" + rows.map(x => x.map(sel).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" })); a.download = nama; document.body.appendChild(a); a.click(); setTimeout(() => a.remove(), 1000);
    };
    $("#sn-csv").onclick = () => csv("peserta-kursus-bm-online.csv", [["nama", "emel", "pertemuan_dibuka", "kuiz_dijawab", "kuiz_lulus", "purata_%", "layak_sijil", "nama_sijil", "kali_pertama", "kali_terakhir", ...Array.from({ length: JUMLAH }, (_, i) => `P${i + 1}_markah_%`)],
      ...ls.map(p => [p.nama, p.emel, p.nBuka, p.nKuiz, p.nLulus, p.purata, p.layak ? 1 : 0, p.namaSijil || "", f(p.dicipta), f(p.kemaskini), ...p.st.map(x => x.k ? pct(x.k.best, x.k.all) : "")])]);
    $("#sn-csv2").onclick = () => csv("jawapan-kursus-bm-online.csv", [["nama", "emel", "masa", "pertemuan", "soalan_no", "soalan", "jawapan", "betul"],
      ...ls.flatMap(p => p.jawapan.slice().reverse().map(j => [p.nama, p.emel, f(j.masa), j.n, j.item, j.soalan, j.jawapan, j.betul ? 1 : 0]))]);
  } catch (e) { console.error(e); el.innerHTML = `<p>${tx("gagal")}</p><small>${esc(e.code || "")}</small>`; }
}

if (window.__BINA_PDF) { /* tools PDF: tiada log masuk · สร้าง PDF ไม่ต้องล็อกอิน */ }
else {
  if (pintu) kunci(`<p class="pintu-muat">${tx("memuat")}…</p>`);
  getRedirectResult(auth).catch(e => console.error(e));
  onAuthStateChanged(auth, u => {
    window.AKAUN_SEDIA = true; pengguna = null; rek = null; cacheKata = null; cip();
    if (u) { kunci(`<p class="pintu-muat">${tx("memuat")}…</p>`); selepasMasuk(u); }
    else pintuLogMasuk();
  });
}
