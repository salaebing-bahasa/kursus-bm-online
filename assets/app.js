(function () {
  "use strict";

  // 1. Kad "Kata hari ini" di laman utama
  var wbtn = document.getElementById("w-next");
  if (wbtn && window.VOCAB && window.VOCAB.length) {
    var V = window.VOCAB, card = document.querySelector(".pair"), last = 0;
    function show(i) {
      var v = V[i];
      document.getElementById("w-ms").textContent = v[0];
      document.getElementById("w-th").textContent = v[1];
      document.getElementById("w-ex").textContent = v[2];
      var link = document.getElementById("w-link");
      link.href = "pertemuan/" + String(v[3]).padStart(2, "0") + ".html";
      link.textContent = "Dari Pertemuan " + v[3];
      card.classList.remove("swap"); void card.offsetWidth; card.classList.add("swap");
      last = i;
    }
    // kata berbeza setiap hari, sama untuk semua pelajar pada hari yang sama
    var day = Math.floor((Date.now() + 7 * 3600e3) / 864e5);
    show(day % V.length);
    wbtn.addEventListener("click", function () {
      var i; do { i = Math.floor(Math.random() * V.length); } while (V.length > 1 && i === last);
      show(i);
    });
  }

  // 2. Kelas seterusnya (kelas bermula 2.00 petang, tamat 3.30 petang waktu Thailand)
  if (window.SCHEDULE) {
    var now = Date.now(), next = null;
    document.querySelectorAll(".session, .sched tr[data-date]").forEach(function (li) {
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
        var tr = document.querySelector('.sched tr[data-date="' + next.s[0] + '"]');
        if (tr) tr.classList.add("is-next");
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
          else { o.classList.add("wrong"); fb.textContent = "Kurang tepat. Jawapan yang betul: " + (opts[ans].querySelector(".rm") || opts[ans]).textContent; fb.className = "fb no"; }
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
  var tocLinks = document.querySelectorAll(".sec-nav a");
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

  // 5. Tunjuk / sembunyi baris tulisan Jawi
  var jb = document.querySelector(".jw-toggle"), docEl = document.documentElement;
  if (jb) {
    var setJw = function (on) {
      docEl.classList.toggle("no-jw", !on);
      jb.setAttribute("aria-pressed", on ? "true" : "false");
      try { localStorage.setItem("jawi", on ? "1" : "0"); } catch (e) {}
    };
    jb.setAttribute("aria-pressed", docEl.classList.contains("no-jw") ? "false" : "true");
    jb.addEventListener("click", function () { setJw(docEl.classList.contains("no-jw")); });
  }

})();
