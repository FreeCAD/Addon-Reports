// {#
// SPDX-License-Identifier: LGPL-2.1-or-later
// SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
// SPDX-FileNotice: Part of FreeCAD.
// #}

document.addEventListener('DOMContentLoaded', function () {
    var table = document.getElementById('addons-table');
    var searchInput = document.getElementById('addon-search');
    var countEl = document.getElementById('visible-count');
    var totalEl = document.getElementById('total-count');
    if (!table || !searchInput) return;

    var tbody = table.querySelector('tbody');
    var total = tbody.rows.length;
    if (totalEl) totalEl.textContent = total;
    if (countEl) countEl.textContent = total;

    /* search with debounce */
    var timer;
    searchInput.addEventListener('input', function () {
        clearTimeout(timer);
        var q = this.value.toLowerCase().trim();
        timer = setTimeout(function () {
            var vis = 0;
            for (var i = 0; i < tbody.rows.length; i++) {
                var row = tbody.rows[i];
                var ok = !q || row.textContent.toLowerCase().indexOf(q) !== -1;
                row.style.display = ok ? '' : 'none';
                if (ok) vis++;
                var addonId = row.getAttribute('data-addon-id');
                if (addonId) {
                    var card = document.getElementById(addonId);
                    if (card) card.style.display = ok ? '' : 'none';
                }
            }
            if (countEl) countEl.textContent = vis;
        }, 150);
    });

    /* column sort */
    var ths = table.querySelectorAll('th[data-sort]');
    for (var t = 0; t < ths.length; t++) {
        ths[t].addEventListener('click', (function (th) {
            return function () {
                var col = parseInt(th.getAttribute('data-sort'));
                var type = th.getAttribute('data-type') || 'string';
                var rows = [];
                for (var i = 0; i < tbody.rows.length; i++)rows.push(tbody.rows[i]);
                var asc = !th.classList.contains('sort-asc');
                for (var j = 0; j < ths.length; j++)ths[j].classList.remove('sort-asc', 'sort-desc');
                th.classList.add(asc ? 'sort-asc' : 'sort-desc');
                rows.sort(function (a, b) {
                    var va = a.cells[col].getAttribute('data-value') || a.cells[col].textContent.trim();
                    var vb = b.cells[col].getAttribute('data-value') || b.cells[col].textContent.trim();
                    if (type === 'number') { va = parseFloat(va) || 0; vb = parseFloat(vb) || 0; }
                    else { va = va.toLowerCase(); vb = vb.toLowerCase(); }
                    if (va < vb) return asc ? -1 : 1;
                    if (va > vb) return asc ? 1 : -1;
                    return 0;
                });
                for (var k = 0; k < rows.length; k++)tbody.appendChild(rows[k]);
            };
        })(ths[t]));
    }

    /* keyboard shortcuts */
    document.addEventListener('keydown', function (e) {
        if (e.key === '/' && document.activeElement !== searchInput && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault(); searchInput.focus(); searchInput.select();
        }
        if (e.key === 'Escape' && document.activeElement === searchInput) {
            searchInput.value = ''; searchInput.dispatchEvent(new Event('input')); searchInput.blur();
        }
    });

    /* dark / light theme toggle */
    var btn = document.getElementById('theme-toggle');
    if (btn) {
        var html = document.documentElement;
        var icon = btn.querySelector('.ti');
        var label = btn.querySelector('.theme-label');
        function applyTheme(theme) {
            html.setAttribute('data-bs-theme', theme);
            if (icon) { icon.className = theme === 'dark' ? 'ti ti-sun' : 'ti ti-moon'; }
            if (label) { label.textContent = theme === 'dark' ? 'Light' : 'Dark'; }
        }
        var saved = localStorage.getItem('fpa-theme');
        if (saved) applyTheme(saved);
        btn.addEventListener('click', function () {
            var next = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('fpa-theme', next);
        });
    }
});