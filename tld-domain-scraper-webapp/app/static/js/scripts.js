document.addEventListener("DOMContentLoaded", function () {
    // Scraping Form: Show loading indicator
    const scrapeForm = document.querySelector("form[action='/scrape']");
    const scrapeButton = scrapeForm ? scrapeForm.querySelector("button[type='submit']") : null;
    if (scrapeButton) {
        scrapeForm.addEventListener("submit", function () {
            scrapeButton.innerHTML = "Scraping...";
            scrapeButton.disabled = true;
        });
    }

    // Results Page: Dynamic table search
    const searchInput = document.getElementById("search");
    const tableRows = document.querySelectorAll("table tbody tr");
    if (searchInput && tableRows) {
        searchInput.addEventListener("input", function () {
            const query = searchInput.value.toLowerCase();
            tableRows.forEach((row) => {
                const cells = Array.from(row.cells);
                const matches = cells.some((cell) => cell.textContent.toLowerCase().includes(query));
                row.style.display = matches ? "" : "none";
            });
        });
    }

    // Download Button: Confirm action
    const downloadButton = document.querySelector("a[href='/download']");
    if (downloadButton) {
        downloadButton.addEventListener("click", function (event) {
            const confirmDownload = confirm("Are you sure you want to download the domains as a CSV file?");
            if (!confirmDownload) {
                event.preventDefault();
            }
        });
    }

    // Toast Notifications
    function showToast(message, type = "success") {
        const toastContainer = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast align-items-center text-bg-${type} border-0 show`;
        toast.role = "alert";
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 3000);
    }

    // Example Toast on Page Load
    showToast("Welcome to TLD Domain Scraper!", "success");

    // Highlight Active Navigation Link
    const navLinks = document.querySelectorAll(".navbar-nav .nav-link");
    const currentPath = window.location.pathname;
    navLinks.forEach((link) => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
});
