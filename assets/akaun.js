/* Log masuk peserta · ระบบล็อกอินผู้เรียน (Firebase Authentication + Firestore)
   - Halaman pertemuan (pertemuan/NN.html) dan senarai.html memerlukan log masuk Google
   - Hanya nama dan e-mel peserta disimpan: bmonline/{uid} { nama, emel, setuju, dicipta, kemaskini }
   - Projek Firebase dikongsi dengan laman 0113131 (tatabahasa-melayu); peraturan keselamatan
     ada dalam fail firestore.rules repo tatabahasa-melayu
   Teks Rumi + Jawi datang daripada window.AKAUN_TEKS (dibina oleh _src/build.py) */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signInWithRedirect, getRedirectResult, signOut }
  from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc, getDocs, collection, serverTimestamp }
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
const VERSI_SETUJU = 1;
const GURU = ["salaebing@gmail.com", "smuhammad@tsu.ac.th"]; // mesti sama dengan isGuru() dalam firestore.rules

const T = window.AKAUN_TEKS || {};
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const r = k => (T[k] ? T[k][0] : k);
/* Rumi dengan baris Jawi di bawahnya (ikut butang "Tulisan Jawi") · ข้อความรูมีพร้อมยาวีด้านล่าง */
const tx = (k, tag = "span") => `<${tag} class="rm">${esc(r(k))}</${tag}>${T[k] && T[k][1] ? `<${tag} class="jw" lang="ms-Arab" dir="rtl">${esc(T[k][1])}</${tag}>` : ""}`;
const $ = s => document.querySelector(s);
const pintu = $("#pintu");
let pengguna = null;

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
/* Cip akaun di pengepala · ปุ่มชื่อผู้ใช้และออกจากระบบที่แถบบน */
function cip() {
  let c = $("#akaun-cip");
  if (!pengguna) { if (c) c.remove(); return; }
  if (!c) { c = document.createElement("div"); c.id = "akaun-cip"; c.className = "akaun-cip"; const h = $(".site-head"); if (h) h.appendChild(c); }
  c.innerHTML = `<span class="akaun-nama">${esc(pengguna.displayName || pengguna.email || "")}</span><button type="button" class="akaun-keluar" id="akaun-keluar">${tx("keluar")}</button>`;
  $("#akaun-keluar").onclick = () => signOut(auth);
}

async function selepasMasuk(u) {
  const ref = doc(db, KOLEKSI, u.uid);
  let ada = {};
  try { const s = await getDoc(ref); ada = s.exists() ? s.data() : {}; }
  catch (e) { console.error(e); kunci(`<p>${tx("gagal")}</p><button type="button" class="btn" onclick="location.reload()">${tx("muat_semula")}</button>`); return; }
  const perluSetuju = (ada.setuju && ada.setuju.versi) !== VERSI_SETUJU;
  if (perluSetuju && !(await mintaSetuju())) { await signOut(auth); pintuLogMasuk("ditolak"); return; }
  const data = { nama: u.displayName || "", emel: u.email || "", kemaskini: serverTimestamp() };
  if (!ada.dicipta) data.dicipta = serverTimestamp();
  if (perluSetuju) data.setuju = { versi: VERSI_SETUJU, masa: serverTimestamp() };
  try { await setDoc(ref, data, { merge: true }); } catch (e) { console.error(e); }
  pengguna = u; cip(); buka();
  if ($("#senarai-peserta")) senarai();
}

/* senarai.html: senarai peserta untuk pengajar · หน้ารายชื่อผู้เรียนสำหรับอาจารย์ */
async function senarai() {
  const el = $("#senarai-peserta");
  const guru = pengguna && pengguna.emailVerified && GURU.includes(String(pengguna.email || "").toLowerCase());
  if (!guru) { el.innerHTML = `<p>${tx("senarai_guru")}</p>`; return; }
  try {
    const s = await getDocs(collection(db, KOLEKSI));
    const ms = t => t && t.toMillis ? t.toMillis() : 0;
    const ls = s.docs.map(d => ({ ...d.data(), dicipta: ms(d.data().dicipta), kemaskini: ms(d.data().kemaskini) })).sort((a, b) => b.kemaskini - a.kemaskini);
    const tarikh = t => t ? new Date(t).toLocaleString("ms-MY", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";
    el.innerHTML = `<p><b>${ls.length}</b> ${esc(r("peserta"))} <button type="button" class="btn-ghost" id="sn-csv">${tx("muat_turun")} (CSV)</button></p>
      <div class="tbl-wrap"><table><thead><tr><th>#</th><th>${tx("nama")}</th><th>${tx("emel")}</th><th>${tx("pertama")}</th><th>${tx("terakhir")}</th></tr></thead>
      <tbody>${ls.map((p, i) => `<tr><td>${i + 1}</td><td>${esc(p.nama)}</td><td>${esc(p.emel)}</td><td>${tarikh(p.dicipta)}</td><td>${tarikh(p.kemaskini)}</td></tr>`).join("")}</tbody></table></div>`;
    $("#sn-csv").onclick = () => {
      const z = n => String(n).padStart(2, "0"), f = t => { if (!t) return ""; const d = new Date(t); return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())} ${z(d.getHours())}:${z(d.getMinutes())}`; };
      const sel = v => { let t = String(v == null ? "" : v); if (/^[=+\-@]/.test(t)) t = "'" + t; return /[",\r\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
      const csv = "﻿" + [["nama", "emel", "kali_pertama", "kali_terakhir"], ...ls.map(p => [p.nama, p.emel, f(p.dicipta), f(p.kemaskini)])].map(x => x.map(sel).join(",")).join("\r\n");
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" })); a.download = "peserta-kursus-bm-online.csv"; document.body.appendChild(a); a.click(); setTimeout(() => a.remove(), 1000);
    };
  } catch (e) { console.error(e); el.innerHTML = `<p>${tx("gagal")}</p><small>${esc(e.code || "")}</small>`; }
}

if (window.__BINA_PDF) { /* tools PDF: tiada log masuk · สร้าง PDF ไม่ต้องล็อกอิน */ }
else {
if (pintu) kunci(`<p class="pintu-muat">${tx("memuat")}…</p>`);
getRedirectResult(auth).catch(e => console.error(e));
onAuthStateChanged(auth, u => {
  window.AKAUN_SEDIA = true; pengguna = null; cip();
  if (u) { kunci(`<p class="pintu-muat">${tx("memuat")}…</p>`); selepasMasuk(u); }
  else pintuLogMasuk();
});
}
