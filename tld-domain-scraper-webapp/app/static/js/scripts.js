document.addEventListener("DOMContentLoaded", function () {
    // ── Scrape form: show spinner and disable button on submit ──
    const scrapeForm = document.getElementById("scrape-form");
    const scrapeBtn = document.getElementById("scrape-btn");
    const scrapeProgress = document.getElementById("scrape-progress");

    if (scrapeForm && scrapeBtn) {
        scrapeForm.addEventListener("submit", function () {
            scrapeBtn.disabled = true;
            scrapeBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Scraping...';
            if (scrapeProgress) scrapeProgress.classList.remove("d-none");
        });
    }

    // ── Download button: confirm before downloading ──
    const downloadBtn = document.getElementById("download-btn");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", function (event) {
            if (!confirm("Download scraped domains as a CSV file?")) {
                event.preventDefault();
            }
        });
    }

    // ── Highlight the active nav link ──
    const navLinks = document.querySelectorAll(".navbar-nav .nav-link");
    const currentPath = window.location.pathname;
    navLinks.forEach(function (link) {
        const href = link.getAttribute("href");
        if (href && currentPath.startsWith(href) && href !== "/") {
            link.classList.add("active");
        } else if (href === "/" && currentPath === "/") {
            link.classList.add("active");
        }
    });

    // ── Toast helper (used for flash-free JS notifications if needed) ──
    function showToast(message, type) {
        type = type || "success";
        const container = document.getElementById("toast-container");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = "toast align-items-center text-bg-" + type + " border-0 show";
        toast.role = "alert";
        toast.innerHTML =
            '<div class="d-flex">' +
            '<div class="toast-body">' + message + "</div>" +
            '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
            "</div>";
        container.appendChild(toast);
        setTimeout(function () {
            if (container.contains(toast)) container.removeChild(toast);
        }, 4000);
    }

    // Expose globally in case other scripts need it
    window.showToast = showToast;
});
