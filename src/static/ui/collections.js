document.addEventListener('DOMContentLoaded', () => {
  const collectionsTbody = document.getElementById('collectionsTbody');
  const collectionModal = new bootstrap.Modal(document.getElementById('collectionModal'));
  const itemsModal = new bootstrap.Modal(document.getElementById('itemsModal'));
  const collectionForm = document.getElementById('collectionForm');
  const collectionNameInput = document.getElementById('collectionName');
  const collectionItemIdsInput = document.getElementById('collectionItemIds');
  const saveCollectionBtn = document.getElementById('saveCollectionBtn');
  const newCollectionLink = document.getElementById('newCollectionLink');

  let editingCollectionId = null;

  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  async function loadCollections() {
    try {
      const res = await fetch('/getAllItemCollections');
      if (!res.ok) {
        alert('Collections konnten nicht geladen werden');
        return;
      }
      const collections = await res.json();
      collectionsTbody.innerHTML = '';

      for (const collection of collections) {
        const tr = document.createElement('tr');
        const createdAtFormatted = new Date(collection.created_at).toLocaleString('de-DE');
        tr.innerHTML = `
          <td>${collection.collection_id}</td>
          <td>${escapeHtml(collection.name)}</td>
          <td>${collection.item_ids.length}</td>
          <td>${createdAtFormatted}</td>
          <td>
            <div class="btn-group btn-group-sm gap-1">
              <button type="button" class="btn btn-outline-primary edit-btn" data-collection-id="${collection.collection_id}">Edit</button>
              <button type="button" class="btn btn-outline-info items-btn" data-collection-id="${collection.collection_id}">Items</button>
              <button type="button" class="btn btn-outline-danger delete-btn" data-collection-id="${collection.collection_id}">Delete</button>
            </div>
          </td>
        `;
        collectionsTbody.appendChild(tr);

        const editBtn = tr.querySelector('.edit-btn');
        editBtn.addEventListener('click', () => {
          editingCollectionId = collection.collection_id;
          collectionNameInput.value = collection.name;
          collectionItemIdsInput.value = collection.item_ids.join(',');
          document.getElementById('collectionModalLabel').textContent = `Collection bearbeiten (ID: ${collection.collection_id})`;
          collectionModal.show();
        });

        const deleteBtn = tr.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', async () => {
          if (confirm(`Soll die Collection "${collection.name}" wirklich gelöscht werden?`)) {
            await deleteCollection(collection.collection_id);
          }
        });

        const itemsBtn = tr.querySelector('.items-btn');
        itemsBtn.addEventListener('click', async () => {
          await showCollectionItems(collection);
        });
      }
    } catch (err) {
      alert('Fehler beim Laden der Collections');
    }
  }

  async function showCollectionItems(collection) {
    const itemsLoading = document.getElementById('itemsLoading');
    const itemsTable = document.getElementById('itemsTable');
    const itemsTableBody = document.getElementById('itemsTableBody');
    const itemsError = document.getElementById('itemsError');

    itemsLoading.style.display = 'block';
    itemsTable.style.display = 'none';
    itemsError.style.display = 'none';
    itemsTableBody.innerHTML = '';

    document.getElementById('itemsModalLabel').textContent = `Items in Collection: ${escapeHtml(collection.name)}`;
    itemsModal.show();

    try {
      const itemIds = collection.item_ids;
      if (itemIds.length === 0) {
        itemsLoading.style.display = 'none';
        itemsError.style.display = 'block';
        itemsError.textContent = 'Diese Collection enthält keine Items.';
        return;
      }

      const itemsData = [];
      for (const itemId of itemIds) {
        const res = await fetch(`/searchItems?q=&limit=1000`);
        if (res.ok) {
          const allItems = await res.json();
          const item = allItems.find((it) => it.item_id === itemId);
          if (item) {
            itemsData.push(item);
          }
        }
      }

      itemsLoading.style.display = 'none';
      if (itemsData.length === 0) {
        itemsError.style.display = 'block';
        itemsError.textContent = 'Keine Items gefunden.';
        return;
      }

      itemsTableBody.innerHTML = '';
      for (const item of itemsData) {
        const fragestellung = typeof item.fragestellung === 'string'
          ? item.fragestellung.substring(0, 80) + (item.fragestellung.length > 80 ? '...' : '')
          : '—';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${item.item_id}</td>
          <td title="${escapeHtml(item.fragestellung ?? '')}">${escapeHtml(fragestellung)}</td>
          <td>${item.question_type ?? '—'}</td>
          <td>${item.status ?? '—'}</td>
        `;
        itemsTableBody.appendChild(tr);
      }

      itemsTable.style.display = 'table';
    } catch (err) {
      itemsLoading.style.display = 'none';
      itemsError.style.display = 'block';
      itemsError.textContent = 'Fehler beim Laden der Items.';
    }
  }

  async function deleteCollection(collectionId) {
    try {
      const res = await fetch(`/deleteItemCollection/${collectionId}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        const data = await res.json();
        alert(`Fehler beim Löschen: ${data.detail ?? res.statusText}`);
        return;
      }

      alert('Collection gelöscht');
      loadCollections();
    } catch (err) {
      alert('Fehler beim Löschen der Collection');
    }
  }

  saveCollectionBtn.addEventListener('click', async () => {
    const name = collectionNameInput.value.trim();
    const itemIdsStr = collectionItemIdsInput.value.trim();

    if (!name) {
      alert('Bitte gib einen Collection-Namen ein');
      return;
    }

    let itemIds = [];
    if (itemIdsStr) {
      try {
        itemIds = itemIdsStr.split(',').map((id) => parseInt(id.trim(), 10));
        if (itemIds.some(isNaN)) throw new Error();
      } catch {
        alert('Item-IDs müssen Zahlen sein, komma-getrennt');
        return;
      }
    }

    if (itemIds.length === 0) {
      alert('Bitte gib mindestens eine Item-ID an');
      return;
    }

    const payload = { name, item_ids: itemIds };
    const method = editingCollectionId ? 'PUT' : 'POST';
    const url = editingCollectionId ? `/updateItemCollection/${editingCollectionId}` : '/createItemCollection';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Fehler: ${data.detail ?? res.statusText}`);
        return;
      }

      alert(editingCollectionId ? 'Collection aktualisiert' : 'Collection erstellt');
      collectionModal.hide();
      collectionForm.reset();
      editingCollectionId = null;
      loadCollections();
    } catch (err) {
      alert('Fehler beim Speichern der Collection');
    }
  });

  newCollectionLink.addEventListener('click', (e) => {
    e.preventDefault();
    editingCollectionId = null;
    collectionForm.reset();
    document.getElementById('collectionModalLabel').textContent = 'Neue Collection';
    collectionModal.show();
  });

  // Initial load
  loadCollections();
});

