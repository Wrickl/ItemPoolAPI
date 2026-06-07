document.addEventListener('DOMContentLoaded', () => {
  const searchForm = document.getElementById('searchForm');
  const resultsTbody = document.querySelector('#resultsTable tbody');
  const exportBtn = document.getElementById('exportBtn');

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
    resultsTbody.innerHTML = '';
    for (const it of items) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${it.item_id ?? ''}</td>
        <td>${escapeHtml(it.fragestellung ?? '')}</td>
        <td>${it.question_type ?? ''}</td>
        <td>${it.license ?? ''}</td>
        <td>${it.status ?? ''}</td>
        <td>${it.author_id ?? ''}</td>
        <td>${it.database_id ?? ''}</td>
      `;
      resultsTbody.appendChild(tr);
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
    const url = `/exportItems?${params.toString()}`;
    window.location = url;
  });

  // initial load
  doSearch();
});

