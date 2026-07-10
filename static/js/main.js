/**
 * NextGen News - Main JavaScript
 */
(function () {
    'use strict';

    // Search autocomplete
    const searchInput = document.getElementById('searchInput');
    const autocompleteBox = document.getElementById('searchAutocomplete');
    let debounceTimer;

    if (searchInput && autocompleteBox) {
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const query = this.value.trim();
            if (query.length < 2) {
                autocompleteBox.classList.remove('active');
                return;
            }
            debounceTimer = setTimeout(function () {
                fetch('/search/autocomplete/?q=' + encodeURIComponent(query))
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (!data.results.length) {
                            autocompleteBox.classList.remove('active');
                            return;
                        }
                        autocompleteBox.innerHTML = data.results.map(function (item) {
                            return '<a href="' + item.url + '">' + item.title + '</a>';
                        }).join('');
                        autocompleteBox.classList.add('active');
                    });
            }, 300);
        });

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !autocompleteBox.contains(e.target)) {
                autocompleteBox.classList.remove('active');
            }
        });
    }

    // Share button
    document.querySelectorAll('.share-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const url = window.location.origin + btn.dataset.url;
            if (navigator.share) {
                navigator.share({ title: document.title, url: url });
            } else {
                navigator.clipboard.writeText(url).then(function () {
                    alert('Link copied to clipboard!');
                });
            }
        });
    });

    // Dark mode toggle (if user preference stored)
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function () {
            const html = document.documentElement;
            const theme = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        });
        const saved = localStorage.getItem('theme');
        if (saved) document.documentElement.setAttribute('data-bs-theme', saved);
    }

    // Lazy loading enhancement
    if ('loading' in HTMLImageElement.prototype) {
        document.querySelectorAll('img[loading="lazy"]').forEach(function (img) {
            img.decoding = 'async';
        });
    }
})();
