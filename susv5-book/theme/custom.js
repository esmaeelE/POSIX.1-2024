/* SUSv5 — back-to-top + width toggle */
(function () {
    "use strict";

    /* ---- back-to-top button ---- */
    var btn = document.createElement("button");
    btn.className = "back-to-top";
    btn.setAttribute("aria-label", "Back to top");
    btn.innerHTML = "&#8593;";
    document.body.appendChild(btn);

    var ticking = false;
    function onScroll() {
        if (!ticking) {
            window.requestAnimationFrame(function () {
                btn.classList.toggle("visible", window.scrollY > 400);
                ticking = false;
            });
            ticking = true;
        }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    btn.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    /* ---- width toggle ---- */
    var toggle = document.createElement("button");
    toggle.className = "width-toggle";
    toggle.setAttribute("aria-label", "Toggle content width");
    toggle.innerHTML = "&#9776; Wide";
    toggle.title = "Toggle wide content area";

    var wide = localStorage.getItem("susv5-wide-content") === "1";
    if (wide) document.body.classList.add("wide-content");

    toggle.addEventListener("click", function () {
        wide = !wide;
        document.body.classList.toggle("wide-content", wide);
        localStorage.setItem("susv5-wide-content", wide ? "1" : "0");
    });

    /* inject into menu bar */
    var menuBar = document.getElementById("mdbook-menu-bar");
    if (menuBar) {
        var rightBtns = menuBar.querySelector(".right-buttons");
        if (rightBtns) {
            rightBtns.insertBefore(toggle, rightBtns.firstChild);
        }
    }
})();