(function () {
  "use strict";
  var script = document.currentScript;
  if (!script) return;

  var model = script.getAttribute("data-model") || "gpt-4o";
  var height = parseInt(script.getAttribute("data-height"), 10) || 640;

  var frame = document.createElement("iframe");
  frame.title = "AI token calculator — TokenCalc";
  frame.src = "https://tokenestimate.com/?embed=1&model=" + encodeURIComponent(model);
  frame.loading = "lazy";
  frame.referrerPolicy = "no-referrer-when-downgrade";
  frame.setAttribute("style", "display:block;width:100%;max-width:1080px;height:" + height + "px;border:1px solid #dfe6f1;border-radius:16px;overflow:hidden");
  frame.setAttribute("scrolling", "no");

  var credit = null;
  if (script.getAttribute("data-credit") !== "off") {
    credit = document.createElement("div");
    credit.setAttribute("style", "font:12px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#8b97ad;margin-top:6px");
    credit.innerHTML = 'Token calculator by <a href="https://tokenestimate.com/" style="color:#2563eb;text-decoration:none">TokenCalc</a>';
  }

  script.parentNode.insertBefore(frame, script);
  if (credit) script.parentNode.insertBefore(credit, script.nextSibling);
})();
