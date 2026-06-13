document.addEventListener('DOMContentLoaded', () => {
  const searchForm = document.getElementById('searchForm');
  const resultsTbody = document.querySelector('#resultsTable tbody');
  const exportBtn = document.getElementById('exportBtn');
  const selectionControls = document.getElementById('selectionControls');
  const selectAllCheckbox = document.getElementById('selectAllCheckbox');
  const selectAllLink = document.getElementById('selectAllLink');
  const deselectAllLink = document.getElementById('deselectAllLink');
  const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
  const selectedCount = document.getElementById('selectedCount');

  let creatorsMap = {};
  let lastSearchItems = []; // Store items from last search

  async function loadCreators() {
    try {
      const res = await fetch('/getAllCreator');
      if (!res.ok) return;
      const creators = await res.json();
      creatorsMap = {};
      for (const c of creators) {
        creatorsMap[c.author_id] = c.name || c.author_id;
      }
    } catch (err) {
      // ignore - creatorsMap will be empty and we fall back to id
    }
  }

  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function getSelectedItems() {
    const checkboxes = document.querySelectorAll('#resultsTable tbody input[type="checkbox"]:checked');
    const selected = [];
    checkboxes.forEach((cb) => {
      const itemId = cb.getAttribute('data-item-id');
      const item = lastSearchItems.find(it => it.item_id === parseInt(itemId, 10));
      if (item) selected.push(item);
    });
    return selected;
  }

  function updateSelectionUI() {
    const allCheckboxes = document.querySelectorAll('#resultsTable tbody input[type="checkbox"]');
    const checkedCheckboxes = document.querySelectorAll('#resultsTable tbody input[type="checkbox"]:checked');
    const count = checkedCheckboxes.length;

    selectedCount.textContent = count;
    downloadSelectedBtn.disabled = count === 0;

    // Update "select all" checkbox state
    if (allCheckboxes.length > 0) {
      selectAllCheckbox.checked = count === allCheckboxes.length && count > 0;
    }
  }

  function downloadJSON(items, filename) {
    const json = JSON.stringify(items, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function doSearch(e) {
    if (e) e.preventDefault();
    const q = document.getElementById('q').value;
    const author_name = document.getElementById('author_name').value;
    const database_id = document.getElementById('database_id').value;

    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (author_name) params.set('author_name', author_name);
    if (database_id) params.set('database_id', database_id);

    const url = `/searchItems?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) {
      alert('Fehler bei der Suche: ' + res.statusText);
      return;
    }
    const items = await res.json();
    lastSearchItems = items; // Store for later download
    resultsTbody.innerHTML = '';

    for (const it of items) {
      const tr = document.createElement('tr');
      const authorLabel = it.author_name ?? (it.author_id ? (creatorsMap[it.author_id] ?? it.author_id) : '');
      tr.innerHTML = `
        <td>
          <input type="checkbox" data-item-id="${it.item_id}">
        </td>
        <td>${it.item_id ?? ''}</td>
        <td>${escapeHtml(it.fragestellung ?? '')}</td>
        <td>${it.question_type ?? ''}</td>
        <td>${it.license ?? ''}</td>
        <td>${it.status ?? ''}</td>
        <td>${escapeHtml(authorLabel)}</td>
        <td>${it.database_id ?? ''}</td>
      `;
      resultsTbody.appendChild(tr);

      // Add checkbox listener
      const checkbox = tr.querySelector('input[type="checkbox"]');
      checkbox.addEventListener('change', () => {
        tr.classList.toggle('table-active', checkbox.checked);
        updateSelectionUI();
      });
    }

    // Show selection controls if items exist
    if (items.length > 0) {
      selectionControls.style.display = 'block';
      selectAllCheckbox.style.display = 'inline-block';
    } else {
      selectionControls.style.display = 'none';
    }

    updateSelectionUI();
  }

  // Event listeners
  searchForm.addEventListener('submit', doSearch);

  exportBtn.addEventListener('click', async () => {
    const q = document.getElementById('q').value;
    const author_name = document.getElementById('author_name').value;
    const database_id = document.getElementById('database_id').value;
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (author_name) params.set('author_name', author_name);
    if (database_id) params.set('database_id', database_id);

    // Trigger file download
    window.location = `/exportItems?${params.toString()}`;
  });

  downloadSelectedBtn.addEventListener('click', () => {
    const selected = getSelectedItems();
    if (selected.length === 0) {
      alert('Keine Items ausgewählt');
      return;
    }
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `selected_items_${timestamp}.json`;
    downloadJSON(selected, filename);
  });

  selectAllLink.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelectorAll('#resultsTable tbody input[type="checkbox"]').forEach(cb => {
      cb.checked = true;
      cb.dispatchEvent(new Event('change'));
    });
    updateSelectionUI();
  });

  deselectAllLink.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelectorAll('#resultsTable tbody input[type="checkbox"]').forEach(cb => {
      cb.checked = false;
      cb.dispatchEvent(new Event('change'));
    });
    updateSelectionUI();
  });

  selectAllCheckbox.addEventListener('change', () => {
    const isChecked = selectAllCheckbox.checked;
    document.querySelectorAll('#resultsTable tbody input[type="checkbox"]').forEach(cb => {
      cb.checked = isChecked;
      cb.dispatchEvent(new Event('change'));
    });
    updateSelectionUI();
  });

  // initial load
  (async () => {
    await loadCreators();
    doSearch();
  })();
});
