/* ==========================================================================
   Learning progress, kept in this browser.

   Two records, two jobs:
   - opening a lesson is written down on its own (aiae.last.v1). This is what
     the hero's "接着读" button resumes from, so resuming costs the reader
     nothing -- no button to remember to press.
   - marking a lesson learned is deliberate (aiae.progress.v2). That is what
     the count and the 26-tick ruler report, and they only appear once
     something has actually been marked.

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

  var STORE = "aiae.progress.v2";   // v1 的课号在 2026-09-06 重排后失效
  var LAST_STORE = "aiae.last.v1";
  var PATH_STORE = "aiae.path.v1";
  var TOTAL = 26;
  // /lessons/08-context-engineering-for-agents/  -- the lessons overview
  // falls outside this shape and stays unmarkable.
  var LESSON_URL = /\/lessons\/(\d{2})-[^/]+\/(?:index\.html)?$/;

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

  function lessonTitle(id) {
    var h1 = document.querySelector(".md-content__inner h1");
    var text = h1 ? h1.textContent.replace(/[¶¶]/g, "").trim() : id;
    // The heading already opens with the lesson number; do not repeat it.
    return text.indexOf(id) === 0 ? text : id + " " + text;
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

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  // The first lesson at or after `from` that is not marked done. `from` of
  // null starts at 00. Null back means everything from there on is marked.
  function nextUndone(from, links, done) {
    for (var i = from === null ? 0 : parseInt(from, 10); i < TOTAL; i++) {
      var id = pad(i);
      if (links[id] && done.indexOf(id) === -1) return id;
    }
    return null;
  }

  function mountProgress() {
    // The contents list on the front page links every lesson, so it doubles
    // as the id -> element index and there is no second list to keep in sync.
    var links = {};
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-lesson]"),
      function (a) {
        links[a.getAttribute("data-lesson")] = a;
      }
    );
    if (!Object.keys(links).length) return;   // not the front page

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
        : nextUndone(pad(parseInt(anchor, 10) + 1), links, done);
    } else {
      resume = done.length ? nextUndone(null, links, done) : null;
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
        cont.textContent = "26 课全部标记完成 ✓";
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

    var ruler = root.querySelector("[data-prog-ruler]");
    if (ruler) {
      ruler.textContent = "";
      for (var j = 0; j < TOTAL; j++) {
        var tid = pad(j);
        var tick = document.createElement(links[tid] ? "a" : "span");
        tick.className = "prog__tick";
        if (links[tid]) tick.href = links[tid].getAttribute("href");
        if (done.indexOf(tid) !== -1) tick.classList.add("is-done");
        else if (tid === resume) tick.classList.add("is-next");
        tick.title = tid + (done.indexOf(tid) !== -1 ? " · 已掌握" : " · 未标记");
        ruler.appendChild(tick);
      }
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
