(function () {
  "use strict";

  // 1. Kad kontrastif di laman utama
  var btn = document.getElementById("c-next");
  if (btn) {
    var pairs = [["makae", "makan"], ["ikae", "ikan"], ["ayae", "ayam"], ["panah", "panas"], ["abae", "abang"],
      ["tigo", "tiga"], ["muroh", "murah"], ["mahae", "mahal"], ["hijo", "hijau"], ["kunie", "kuning"],
      ["beloq", "belok"], ["sakiq", "sakit"], ["batoq", "batuk"], ["nasik", "nasi"], ["ambo", "saya"], ["kijo", "kerja"]];
    var i = 0, pair = document.querySelector(".pair");
    btn.addEventListener("click", function () {
      i = (i + 1) % pairs.length;
      ["c-dia", "c-dia2"].forEach(function (id) { document.getElementById(id).textContent = pairs[i][0]; });
      ["c-std", "c-std2"].forEach(function (id) { document.getElementById(id).textContent = pairs[i][1]; });
      pair.classList.remove("swap"); void pair.offsetWidth; pair.classList.add("swap");
    });
  }

  // 2. Kelas seterusnya (kelas bermula 2.00 petang, tamat 3.30 petang waktu Thailand)
  if (window.SCHEDULE) {
    var now = Date.now(), next = null;
    document.querySelectorAll(".session").forEach(function (li) {
      var end = new Date(li.dataset.date + "T15:30:00+07:00").getTime();
      if (end < now) li.classList.add("is-past");
    });
    Object.keys(window.SCHEDULE).forEach(function (n) {
      var s = window.SCHEDULE[n], end = new Date(s[0] + "T15:30:00+07:00").getTime();
      if (end >= now && (next === null || end < next.end)) next = { n: +n, s: s, end: end };
    });
    var box = document.getElementById("kelas-seterusnya"), link = document.getElementById("next-link");
    if (box && link) {
      if (next) {
        link.href = "pertemuan/" + String(next.n).padStart(2, "0") + ".html";
        link.textContent = "Pertemuan " + next.n + ": " + next.s[1] + " — Ahad, " + next.s[2] + ", 2.00 petang bersama " + next.s[3];
        var li = document.querySelector('.session [href="' + link.getAttribute("href") + '"]');
        if (li) li.parentNode.classList.add("is-next");
      } else {
        link.removeAttribute("href");
        link.textContent = "Kursus telah tamat. Terima kasih kerana belajar bersama kami!";
      }
      box.hidden = false;
    }
  }

  // 3. Kuiz kendiri
  document.querySelectorAll(".quiz").forEach(function (quiz) {
    var qs = quiz.querySelectorAll(".q"), score = quiz.querySelector(".score");
    function update() {
      var done = quiz.querySelectorAll(".q.done").length, right = quiz.querySelectorAll(".q.correct").length;
      score.textContent = done < qs.length
        ? "Sudah dijawab: " + done + " / " + qs.length
        : "Markah anda: " + right + " / " + qs.length + (right === qs.length ? " — Syabas!" : right >= qs.length * 0.6 ? " — Bagus!" : " — Cuba lagi selepas ulang kaji.");
    }
    qs.forEach(function (q) {
      var ans = +q.dataset.ans, opts = q.querySelectorAll(".opt"), fb = q.querySelector(".fb");
      opts.forEach(function (o) {
        o.addEventListener("click", function () {
          if (q.classList.contains("done")) return;
          q.classList.add("done");
          var pick = +o.dataset.i;
          opts.forEach(function (x) { x.disabled = true; });
          opts[ans].classList.add("right");
          if (pick === ans) { q.classList.add("correct"); fb.textContent = "Betul!"; fb.className = "fb ok"; }
          else { o.classList.add("wrong"); fb.textContent = "Kurang tepat. Jawapan yang betul: " + opts[ans].textContent; fb.className = "fb no"; }
          update();
        });
      });
    });
    quiz.querySelector(".quiz-reset").addEventListener("click", function () {
      qs.forEach(function (q) {
        q.classList.remove("done", "correct");
        q.querySelectorAll(".opt").forEach(function (x) { x.disabled = false; x.classList.remove("right", "wrong"); });
        var fb = q.querySelector(".fb"); fb.textContent = ""; fb.className = "fb";
      });
      score.textContent = "Jawab semua " + qs.length + " soalan untuk melihat markah anda.";
    });
  });

  // 4. Penanda bahagian aktif dalam isi kandungan
  var tocLinks = document.querySelectorAll(".toc a");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) {
          tocLinks.forEach(function (a) { a.classList.remove("on"); });
          if (map[e.target.id]) map[e.target.id].classList.add("on");
        }
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    document.querySelectorAll(".block").forEach(function (s) { io.observe(s); });
  }

  // 5. Carian halaman kontrastif
  var cs = document.getElementById("csearch");
  if (cs) {
    cs.addEventListener("input", function () {
      var q = cs.value.trim().toLowerCase();
      document.querySelectorAll(".cgroup").forEach(function (g) {
        var any = false;
        g.querySelectorAll("li").forEach(function (li) {
          var hit = !q || li.textContent.toLowerCase().indexOf(q) > -1;
          li.hidden = !hit; any = any || hit;
        });
        g.hidden = !any;
      });
    });
  }
})();
