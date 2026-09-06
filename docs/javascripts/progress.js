/* ==========================================================================
   Learning progress, kept in this browser.

   Both records are keyed on the lesson's slug, never on its number: a lesson
   inserted in the middle shifts every number after it, and progress keyed on
   a number would silently point at the wrong lessons. Slugs do not move.

   Two records, two jobs:
   - opening a lesson is written down on its own (aiae.last.v2). This is what
     the hero's "接着读" button resumes from, so resuming costs the reader
     nothing -- no button to remember to press.
   - marking a lesson learned is deliberate (aiae.progress.v3). That is what
     the count and the ruler report, and they only appear once something has
     actually been marked. The ruler has one tick per lesson listed on the
     front page, so adding a lesson lengthens it on its own.

   The two are separate on purpose. An earlier version resumed from the marks
   alone, which meant a reader who never pressed "mark as learned" -- most of
   them -- had no resume link at all.

   No account, no backend, no sync. localStorage can be unavailable (private
   windows, blocked site data), so every read and write is guarded and the
   page has to stay correct when nothing comes back.

   Material's instant navigation swaps the document without a reload, so the
   work runs inside document$ rather than on DOMContentLoaded.
   ========================================================================== */

(function () {
  "use strict";

  var STORE = "aiae.progress.v3";   // v2 的 key 是课号，2026-09-06 起改用 slug
  var LAST_STORE = "aiae.last.v2";
  var PATH_STORE = "aiae.path.v1";
  // /lessons/context-engineering-for-agents/  -- the lessons overview is
  // /lessons/ itself, falls outside this shape, and stays unmarkable.
  var LESSON_URL = /\/lessons\/([a-z0-9-]+)\/(?:index\.html)?$/;

  function read(key) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function write(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      return false;
    }
  }

  function drop(key) {
    try {
      window.localStorage.removeItem(key);
    } catch (e) {
      /* nothing to do -- the UI resets either way */
    }
  }

  function progress() {
    var data = read(STORE);
    return data && typeof data === "object" ? data : {};
  }

  function lastVisit() {
    var data = read(LAST_STORE);
    return data && typeof data === "object" && data.id ? data : null;
  }

  /* --- lesson pages ------------------------------------------------------- */

  function lessonId() {
    var m = LESSON_URL.exec(window.location.pathname);
    return m ? m[1] : null;
  }

  // The h1 already opens with the lesson's number, which is the label a
  // reader recognises; the slug is only ever the key.
  function lessonTitle(id) {
    var h1 = document.querySelector(".md-content__inner h1");
    return h1 ? h1.textContent.replace(/[¶¶]/g, "").trim() : id;
  }

  // Written on every lesson view, including a re-read. Cheap enough to do
  // unconditionally: one small object, overwritten each time.
  function noteVisit(id) {
    write(LAST_STORE, { id: id, title: lessonTitle(id), at: Date.now() });
  }

  function mountMark(id) {
    var inner = document.querySelector(".md-content__inner");
    if (!inner || inner.querySelector(".mark")) return;

    var box = document.createElement("div");
    box.className = "mark";

    var button = document.createElement("button");
    button.type = "button";
    button.className = "mark__btn";

    var note = document.createElement("p");
    note.className = "mark__note";
    note.textContent = "记录只存在这台设备的浏览器里，不上传，也不需要登录。";

    function paint() {
      var done = Object.prototype.hasOwnProperty.call(progress(), id);
      button.textContent = done ? "已掌握 ✓　取消标记" : "标记为已掌握";
      button.setAttribute("aria-pressed", done ? "true" : "false");
      box.classList.toggle("is-done", done);
    }

    button.addEventListener("click", function () {
      var data = progress();
      if (Object.prototype.hasOwnProperty.call(data, id)) {
        delete data[id];
      } else {
        data[id] = { at: Date.now(), title: lessonTitle(id) };
      }
      write(STORE, data);
      paint();
    });

    paint();
    box.appendChild(button);
    box.appendChild(note);
    inner.appendChild(box);
  }

  /* --- front page: progress ------------------------------------------------ */

  // The first lesson at or after position `from` that is not marked done.
  // Null back means everything from there on is marked.
  function nextUndone(from, order, done) {
    for (var i = from; i < order.length; i++) {
      if (done.indexOf(order[i]) === -1) return order[i];
    }
    return null;
  }

  // One-time carry-over from the numbered keys (aiae.*.v2 / v1), which the
  // 2026-09-06 slug change invalidated. The contents still shows each
  // lesson's number, so the page itself is the map. Safe to delete once
  // readers have come back once.
  function carryOver(order, links) {
    var byNumber = {};
    order.forEach(function (slug) {
      var n = links[slug].querySelector("span");
      if (n) byNumber[n.textContent.trim()] = slug;
    });

    if (!read(STORE)) {
      var oldMarks = read("aiae.progress.v2");
      if (oldMarks) {
        var marks = {};
        Object.keys(oldMarks).forEach(function (id) {
          if (byNumber[id]) marks[byNumber[id]] = oldMarks[id];
        });
        if (Object.keys(marks).length) write(STORE, marks);
      }
    }

    if (!read(LAST_STORE)) {
      var oldVisit = read("aiae.last.v1");
      if (oldVisit && oldVisit.id && byNumber[oldVisit.id]) {
        write(LAST_STORE, {
          id: byNumber[oldVisit.id], title: oldVisit.title, at: oldVisit.at
        });
      }
    }
  }

  function mountProgress() {
    // The contents list on the front page links every lesson, so it doubles
    // as the id -> element index and there is no second list to keep in sync.
    var links = {};
    var order = [];
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-lesson]"),
      function (a) {
        var slug = a.getAttribute("data-lesson");
        links[slug] = a;
        order.push(slug);   // DOM order is the course order
      }
    );
    if (!order.length) return;   // not the front page

    carryOver(order, links);

    var data = progress();
    var done = Object.keys(data).filter(function (id) {
      return Object.prototype.hasOwnProperty.call(links, id);
    });

    /* --- resume, from the last lesson opened ------------------------------ */

    // A lesson already marked done means carry on past it; an unmarked one
    // means the reader was still in it. Readers with marks but no visit on
    // record (they marked lessons before this was added) resume at their
    // first unmarked lesson instead.
    var visit = lastVisit();
    var anchor = visit && links[visit.id] ? visit.id : null;
    var resume;
    if (anchor) {
      resume = done.indexOf(anchor) === -1
        ? anchor
        : nextUndone(order.indexOf(anchor) + 1, order, done);
    } else {
      resume = done.length ? nextUndone(0, order, done) : null;
    }

    var cont = document.querySelector("[data-prog-next]");
    if (cont && (resume || anchor)) {
      if (resume) {
        cont.href = links[resume].getAttribute("href");
        // The contents entry already reads "08 Context Engineering", which is
        // a better label than the lesson's full h1.
        cont.textContent = "接着读 " + links[resume].textContent.trim() + " →";
      } else {
        cont.href = links[anchor].getAttribute("href");
        cont.textContent = order.length + " 课全部标记完成 ✓";
      }
      cont.hidden = false;
      // Two primary buttons would compete; starting over steps back once
      // there is somewhere to resume.
      var cta = cont.closest(".hero__cta");
      if (cta) cta.classList.add("has-progress");
    }

    /* --- the count and the ruler, only once something is marked ---------- */

    var root = document.querySelector("[data-progress]");
    if (!root) return;
    var body = root.querySelector(".prog__body");
    if (!done.length) {
      if (body) body.hidden = true;
      return;
    }
    if (body) body.hidden = false;

    done.forEach(function (id) {
      links[id].classList.add("is-done");
    });

    var count = root.querySelector("[data-prog-done]");
    if (count) count.textContent = String(done.length);

    var total = root.querySelector("[data-prog-total]");
    if (total) total.textContent = "/ " + order.length + " 课已掌握";

    var ruler = root.querySelector("[data-prog-ruler]");
    if (ruler) {
      ruler.textContent = "";
      order.forEach(function (slug) {
        var tick = document.createElement("a");
        tick.className = "prog__tick";
        tick.href = links[slug].getAttribute("href");
        if (done.indexOf(slug) !== -1) tick.classList.add("is-done");
        else if (slug === resume) tick.classList.add("is-next");
        tick.title = links[slug].textContent.trim()
          + (done.indexOf(slug) !== -1 ? " · 已掌握" : " · 未标记");
        ruler.appendChild(tick);
      });
    }

    // What the reader last had open, which is not necessarily the newest
    // mark -- re-reading an old lesson should show that lesson.
    var newestMark = done.reduce(function (best, id) {
      return !best || (data[id].at || 0) > (data[best].at || 0) ? id : best;
    }, null);
    var shownId = anchor || newestMark;
    var lastEl = root.querySelector("[data-prog-last]");
    if (lastEl && shownId) {
      lastEl.textContent = (anchor && visit.title) || data[shownId].title || shownId;
      lastEl.href = links[shownId].getAttribute("href");
    }

    var reset = root.querySelector("[data-prog-reset]");
    if (reset) {
      // Two clicks instead of a confirm() dialog, which blocks the page.
      reset.addEventListener("click", function () {
        if (reset.dataset.armed !== "1") {
          reset.dataset.armed = "1";
          reset.textContent = "再点一次，记录就没了";
          return;
        }
        drop(STORE);
        drop(LAST_STORE);
        drop("aiae.progress.v2");
        drop("aiae.last.v1");
        window.location.reload();
      });
    }
  }

  /* --- front page: which path ---------------------------------------------- */

  function mountPicker() {
    var picker = document.querySelector("[data-picker]");
    if (!picker) return;

    var options = picker.querySelectorAll("[data-path]");
    var panels = document.querySelectorAll(".path[data-path]");
    if (!panels.length) return;

    function show(choice) {
      Array.prototype.forEach.call(options, function (o) {
        o.setAttribute("aria-pressed", o.dataset.path === choice ? "true" : "false");
      });
      Array.prototype.forEach.call(panels, function (p) {
        p.hidden = p.dataset.path !== choice;
      });
    }

    // Without JS every path stays visible, so hiding is the first thing done.
    show(read(PATH_STORE));

    Array.prototype.forEach.call(options, function (o) {
      o.addEventListener("click", function () {
        var choice = o.getAttribute("aria-pressed") === "true" ? null : o.dataset.path;
        if (choice) write(PATH_STORE, choice);
        else drop(PATH_STORE);
        show(choice);
      });
    });
  }

  function boot() {
    var id = lessonId();
    if (id) {
      mountMark(id);
      noteVisit(id);
    }
    mountProgress();
    mountPicker();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(boot);
  } else {
    document.addEventListener("DOMContentLoaded", boot);
  }
})();
