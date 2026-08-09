(function () {
  "use strict";

  var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Animated number counters ---------- */
  var raf = window.requestAnimationFrame || function (cb) { setTimeout(cb, 16); };
  var ctrl = window.cancelAnimationFrame || clearTimeout;

  function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }

  function animateNumber(el, target, duration) {
    if (!el || prefersReduced) {
      if (el) { el.textContent = target; delete el.dataset.motionFrom; }
      return;
    }
    var from = 0;
    if (el.dataset.motionFrom !== undefined && el.textContent.replace(/[^0-9]/g, "") !== "") {
      from = parseInt(el.dataset.motionFrom, 10) || 0;
    }
    var targetInt = parseInt(String(target).replace(/[^0-9]/g, ""), 10) || 0;
    if (el.dataset.motionFrame) ctrl(parseInt(el.dataset.motionFrame, 10));
    var start = performance.now();
    var dur = duration || 750;
    function tick(now) {
      var p = Math.min(1, (now - start) / dur);
      var v = Math.round(from + (targetInt - from) * easeOutExpo(p));
      el.textContent = v.toLocaleString("en-US");
      el.dataset.motionFrom = String(v);
      if (p < 1) {
        el.dataset.motionFrame = String(raf(tick));
      } else {
        delete el.dataset.motionFrame;
      }
    }
    el.dataset.motionFrame = String(raf(tick));
  }

  /* ---------- Mouse spotlight ---------- */
  var spotlight = document.querySelector(".spotlight");
  var hasFinePointer = window.matchMedia && window.matchMedia("(pointer: fine)").matches;
  if (spotlight && hasFinePointer) {
    document.documentElement.classList.add("has-mouse");
    var sx = 0, sy = 0, cx = 0, cy = 0, tick = false;
    document.addEventListener("mousemove", function (e) {
      sx = e.clientX; sy = e.clientY;
      if (!tick) { tick = true; runSpotlight(); }
    });
    function runSpotlight() {
      cx += (sx - cx) * 0.14;
      cy += (sy - cy) * 0.14;
      spotlight.style.setProperty("--mx", cx + "px");
      spotlight.style.setProperty("--my", cy + "px");
      if (Math.abs(cx - sx) > 0.5 || Math.abs(cy - sy) > 0.5) {
        raf(runSpotlight);
      } else { tick = false; }
    }
  }

  /* ---------- Sticky header state ---------- */
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (header) header.classList.toggle("scrolled", (window.scrollY || 0) > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Scroll reveal ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  window.TokenMotion = window.TokenMotion || {};
  window.TokenMotion.animateNumber = animateNumber;
})();