/* ==========================================================================
   Learning progress, kept in this browser.

   Two halves that share one storage key:
   - every lesson page grows a "mark as learned" control at the end;
   - the front page reads those marks back as a count, a 26-tick ruler and a
     "continue" link.

   No account, no backend, no sync. localStorage can be unavailable (private
   windows, blocked site data), so every read and write is guarded and the
   page has to stay correct when nothing comes back.

   Material's instant navigation swaps the document without a reload, so the
   work runs inside document$ rather than on DOMContentLoaded.
   ========================================================================== */

(function () {
  "use strict";

  var STORE = "aiae.progress.v2";   // v1 的课号在 2026-09-06 重排后失效
  var PATH_STORE = "aiae.path.v1";
  var TOTAL = 26;
  // /lessons/08-context-engineering-for-agents/  -- exercises pages and the
  // lessons overview both fall outside this shape and stay unmarkable.
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

  function mountProgress() {
    var root = document.querySelector("[data-progress]");
    if (!root) return;

    // The architecture map above already links every lesson, so it doubles as
    // the id -> url index and there is no second list to keep in sync.
    var links = {};
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-lesson]"),
      function (a) {
        links[a.getAttribute("data-lesson")] = a;
      }
    );

    var data = progress();
    var ids = Object.keys(data).filter(function (id) {
      return Object.prototype.hasOwnProperty.call(links, id);
    });

    var empty = root.querySelector(".prog__empty");
    var body = root.querySelector(".prog__body");
    if (!ids.length) {
      if (empty) empty.hidden = false;
      if (body) body.hidden = true;
      return;
    }
    if (empty) empty.hidden = true;
    if (body) body.hidden = false;

    ids.forEach(function (id) {
      links[id].classList.add("is-done");
    });

    var next = null;
    for (var i = 0; i < TOTAL; i++) {
      var id = pad(i);
      if (links[id] && ids.indexOf(id) === -1) {
        next = id;
        break;
      }
    }

    var done = root.querySelector("[data-prog-done]");
    if (done) done.textContent = String(ids.length);

    var ruler = root.querySelector("[data-prog-ruler]");
    if (ruler) {
      ruler.textContent = "";
      for (var j = 0; j < TOTAL; j++) {
        var tid = pad(j);
        var tick = document.createElement(links[tid] ? "a" : "span");
        tick.className = "prog__tick";
        if (links[tid]) tick.href = links[tid].getAttribute("href");
        if (ids.indexOf(tid) !== -1) tick.classList.add("is-done");
        else if (tid === next) tick.classList.add("is-next");
        tick.title = tid + (ids.indexOf(tid) !== -1 ? " · 已掌握" : " · 未标记");
        ruler.appendChild(tick);
      }
    }

    var latest = ids.reduce(function (best, id) {
      return !best || (data[id].at || 0) > (data[best].at || 0) ? id : best;
    }, null);
    var last = root.querySelector("[data-prog-last]");
    if (last && latest) {
      last.textContent = data[latest].title || latest;
      last.href = links[latest].getAttribute("href");
    }

    var cont = root.querySelector("[data-prog-next]");
    if (cont) {
      if (next) {
        cont.href = links[next].getAttribute("href");
        cont.textContent = "继续第 " + next + " 课 →";
      } else {
        cont.href = links["25"].getAttribute("href");
        cont.textContent = "26 课全部标记完成 ✓";
      }
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
    if (id) mountMark(id);
    mountProgress();
    mountPicker();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(boot);
  } else {
    document.addEventListener("DOMContentLoaded", boot);
  }
})();
