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
  const collectionNameInput = document.getElementById('collectionNameInput');
  const createCollectionBtn = document.getElementById('createCollectionBtn');
  const itemDetailsModalElement = document.getElementById('itemDetailsModal');
  const itemDetailsBody = document.getElementById('itemDetailsBody');
  const itemDetailsModal = itemDetailsModalElement ? new bootstrap.Modal(itemDetailsModalElement) : null;

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
    if (createCollectionBtn && collectionNameInput) {
      createCollectionBtn.disabled = count === 0 || !collectionNameInput.value.trim();
    }

    // Update "select all" checkbox state
    if (allCheckboxes.length > 0) {
      selectAllCheckbox.checked = count === allCheckboxes.length && count > 0;
    }
  }

  async function createCollectionFromSelectedItems() {
    const selected = getSelectedItems();
    const name = collectionNameInput.value.trim();

    if (!name) {
      alert('Bitte gib einen Collection-Namen ein');
      return;
    }
    if (selected.length === 0) {
      alert('Bitte waehle mindestens ein Item aus');
      return;
    }

    const payload = {
      name,
      item_ids: selected.map((item) => item.item_id),
    };

    try {
      const res = await fetch('/createItemCollection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Collection konnte nicht gespeichert werden: ${data.detail ?? res.statusText}`);
        return;
      }

      alert(`Collection "${data.name}" gespeichert (ID: ${data.collection_id})`);
      collectionNameInput.value = '';
      updateSelectionUI();
    } catch (err) {
      alert('Fehler beim Speichern der Collection');
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

  function formatValueAsHtml(value) {
    if (value === null || value === undefined) {
      return '<span class="text-muted">-</span>';
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return '<span class="text-muted">(leer)</span>';
      }

      const isPrimitiveArray = value.every((entry) => entry === null || ['string', 'number', 'boolean'].includes(typeof entry));
      if (isPrimitiveArray) {
        return `<ul class="mb-0">${value.map((entry) => `<li>${escapeHtml(String(entry))}</li>`).join('')}</ul>`;
      }

      return value
        .map((entry, idx) => `<div class="detail-array-entry"><div class="detail-array-label">Eintrag ${idx + 1}</div>${formatValueAsHtml(entry)}</div>`)
        .join('');
    }

    if (typeof value === 'object') {
      const entries = Object.entries(value);
      if (entries.length === 0) {
        return '<span class="text-muted">(leer)</span>';
      }

      return `
        <table class="table table-sm table-bordered detail-table mb-2">
          <tbody>
            ${entries.map(([k, v]) => `
              <tr>
                <th class="detail-key">${escapeHtml(k)}</th>
                <td>${formatValueAsHtml(v)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }

    return escapeHtml(String(value));
  }

  function showItemDetails(item) {
    if (!itemDetailsModal || !itemDetailsBody) return;

    const entries = Object.entries(item).filter(([key]) => !key.toLowerCase().includes('solution_attempt'));
    itemDetailsBody.innerHTML = `
      <div class="mb-3">
        <h6 class="mb-0">Item ${escapeHtml(String(item.item_id ?? ''))}</h6>
      </div>
      <table class="table table-bordered detail-table">
        <tbody>
          ${entries.map(([key, value]) => `
            <tr>
              <th class="detail-key">${escapeHtml(key)}</th>
              <td>${formatValueAsHtml(value)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
    itemDetailsModal.show();
  }

  async function exportSingleItem(item) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    downloadJSON(item, `item_${item.item_id}_${ts}.json`);

    const includeAttempts = window.confirm('Sollen die zugehoerigen Solution Attempts als zweite Datei mit exportiert werden?');
    if (!includeAttempts) return;

    try {
      const attemptsRes = await fetch(`/getSolutionAttemptsForItem/${item.item_id}`);
      if (!attemptsRes.ok) {
        alert('Solution Attempts konnten nicht geladen werden: ' + attemptsRes.statusText);
        return;
      }
      const attempts = await attemptsRes.json();
      downloadJSON(attempts, `item_${item.item_id}_solution_attempts_${ts}.json`);
    } catch (err) {
      alert('Fehler beim Laden der Solution Attempts');
    }
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
        <td>
          <div class="d-flex gap-2 justify-content-end">
            <button type="button" class="btn btn-sm btn-outline-success row-export-btn" data-item-id="${it.item_id}">Export</button>
            <button type="button" class="btn btn-sm btn-outline-secondary row-details-btn" data-item-id="${it.item_id}">Details</button>
          </div>
        </td>
      `;
      resultsTbody.appendChild(tr);

      // Add checkbox listener
      const checkbox = tr.querySelector('input[type="checkbox"]');
      checkbox.addEventListener('change', () => {
        tr.classList.toggle('table-active', checkbox.checked);
        updateSelectionUI();
      });

      const rowExportBtn = tr.querySelector('.row-export-btn');
      rowExportBtn.addEventListener('click', async () => {
        await exportSingleItem(it);
      });

      const rowDetailsBtn = tr.querySelector('.row-details-btn');
      rowDetailsBtn.addEventListener('click', () => {
        showItemDetails(it);
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

  if (collectionNameInput) {
    collectionNameInput.addEventListener('input', updateSelectionUI);
  }

  if (createCollectionBtn) {
    createCollectionBtn.addEventListener('click', async () => {
      await createCollectionFromSelectedItems();
    });
  }

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
