document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('createItemForm');
  const messageBox = document.getElementById('messageBox');
  const creatorSelect = document.getElementById('author_id');
  const databaseSelect = document.getElementById('database_id');
  const licenseSelect = document.getElementById('license');
  const statusSelect = document.getElementById('status');
  const questionTypeSelect = document.getElementById('question_type');

  // Creator modal elements
  const createCreatorForm = document.getElementById('createCreatorForm');
  const submitCreateCreator = document.getElementById('submitCreateCreator');
  const createCreatorMessage = document.getElementById('createCreatorMessage');
  const newCreatorName = document.getElementById('new_creator_name');
  const newCreatorEmail = document.getElementById('new_creator_email');
  const newCreatorRole = document.getElementById('new_creator_role');
  const newCreatorOrganisation = document.getElementById('new_creator_organisation');

  const endpoints = {
    creators: '/getAllCreator',
    databases: '/getAllDatabases',
    licenses: '/getAllAvailableLicenseTypes',
    statuses: '/getAllAvailableStatusTypes',
    questionTypes: '/getAllAvailableQuestionTypes',
    organisations: '/getAllOrganisations',
    createCreator: '/createCreator',
  };

  function showMessage(type, text) {
    messageBox.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${escapeHtml(text)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Schließen"></button>
      </div>
    `;
  }

  function showInlineCreatorMessage(type, text) {
    createCreatorMessage.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${escapeHtml(text)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Schließen"></button>
      </div>
    `;
  }

  function escapeHtml(unsafe) {
    return String(unsafe)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function setOptions(select, items, placeholder, valueKey, labelResolver) {
    select.innerHTML = '';
    if (placeholder !== null) {
      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.textContent = placeholder;
      select.appendChild(emptyOption);
    }

    for (const item of items) {
      const option = document.createElement('option');
      option.value = item[valueKey];
      option.textContent = labelResolver(item);
      select.appendChild(option);
    }
  }

  async function loadSelectData() {
    // Fetch enums first (these don't require DB)
    let licenses = null, statuses = null, questionTypes = null;
    try {
      const [licensesRes, statusesRes, questionTypesRes] = await Promise.all([
        fetch(endpoints.licenses),
        fetch(endpoints.statuses),
        fetch(endpoints.questionTypes),
      ]);
      if (licensesRes.ok) licenses = await licensesRes.json();
      if (statusesRes.ok) statuses = await statusesRes.json();
      if (questionTypesRes.ok) questionTypes = await questionTypesRes.json();
    } catch (err) {
      // ignore; we'll show a message below if none available
    }

    if (licenses) setOptions(licenseSelect, licenses.map((v) => ({ value: v })), null, 'value', (i) => i.value);
    else showMessage('warning', 'Lizenztypen konnten nicht geladen werden.');

    if (statuses) setOptions(statusSelect, statuses.map((v) => ({ value: v })), null, 'value', (i) => i.value);
    else showMessage('warning', 'Status-Typen konnten nicht geladen werden.');

    if (questionTypes) setOptions(questionTypeSelect, questionTypes.map((v) => ({ value: v })), null, 'value', (i) => i.value);
    else showMessage('warning', 'Fragetypen konnten nicht geladen werden.');

    // Now try DB-backed endpoints; failures here shouldn't prevent enums
    let creators = null, databases = null, organisations = null;
    const dbErrors = [];
    try {
      const creatorsRes = await fetch(endpoints.creators);
      if (creatorsRes.ok) creators = await creatorsRes.json();
      else dbErrors.push('Creators');
    } catch (err) { dbErrors.push('Creators'); }

    try {
      const databasesRes = await fetch(endpoints.databases);
      if (databasesRes.ok) databases = await databasesRes.json();
      else dbErrors.push('Databases');
    } catch (err) { dbErrors.push('Databases'); }

    try {
      const orgsRes = await fetch(endpoints.organisations);
      if (orgsRes.ok) organisations = await orgsRes.json();
      else dbErrors.push('Organisations');
    } catch (err) { dbErrors.push('Organisations'); }

    if (creators) {
      setOptions(creatorSelect, creators, 'Creator auswählen', 'author_id', (creator) => creator.name ? `${creator.name}` : creator.author_id);
    } else {
      // leave select empty but keep disabled message
      creatorSelect.innerHTML = '';
      const opt = document.createElement('option'); opt.value = ''; opt.textContent = 'Creators nicht verfügbar'; creatorSelect.appendChild(opt);
      creatorSelect.disabled = true;
    }

    if (databases) {
      setOptions(databaseSelect, databases, 'Keine Zuordnung', 'database_id', (database) => {
        const parts = [];
        if (database.database_id !== undefined && database.database_id !== null) parts.push(`ID ${database.database_id}`);
        if (database.version) parts.push(database.version);
        if (database.dialect) parts.push(database.dialect);
        if (database.description) parts.push(database.description);
        return parts.length ? parts.join(' · ') : `Datenbank ${database.database_id}`;
      });
    } else {
      databaseSelect.innerHTML = '';
      const opt = document.createElement('option'); opt.value = ''; opt.textContent = 'Datenbanken nicht verfügbar'; databaseSelect.appendChild(opt);
      databaseSelect.disabled = true;
    }

    if (organisations) {
      setOptions(newCreatorOrganisation, organisations, 'Organisation auswählen', 'id', (org) => org.name || String(org.id));
      submitCreateCreator.disabled = false;
    } else {
      newCreatorOrganisation.innerHTML = '';
      const opt = document.createElement('option'); opt.value = ''; opt.textContent = 'Orgs nicht verfügbar'; newCreatorOrganisation.appendChild(opt);
      submitCreateCreator.disabled = true;
      showInlineCreatorMessage('warning', 'Organisationen nicht erreichbar. Neue Creator können nicht angelegt werden.');
    }

    if (dbErrors.length) {
      showMessage('warning', `Einige DB-gebundene Dropdowns konnten nicht geladen werden: ${dbErrors.join(', ')}.`);
    }
  }

  // Create creator inline
  submitCreateCreator.addEventListener('click', async () => {
    const name = newCreatorName.value.trim();
    const email = newCreatorEmail.value.trim();
    const role = Number(newCreatorRole.value) || 0;
    const organisation_id = newCreatorOrganisation.value || null;

    if (!name || !organisation_id) {
      showInlineCreatorMessage('warning', 'Name und Organisation sind erforderlich.');
      return;
    }

    const payload = {
      name,
      email: email || null,
      role,
      organisation_id: organisation_id,
    };

    try {
      // Use fetch to create the creator
      const res = await fetch(endpoints.createCreator, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || res.statusText);
      }
      const created = await res.json();
      // append to creator select and choose it
      const option = document.createElement('option');
      option.value = created.author_id;
      option.textContent = created.name || created.author_id;
      creatorSelect.appendChild(option);
      creatorSelect.value = created.author_id;

      // close modal
      const modalEl = document.getElementById('createCreatorModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal.hide();

      // cleanup
      createCreatorForm.reset();
      showMessage('success', `Creator ${created.name || created.author_id} angelegt.`);
    } catch (err) {
      showInlineCreatorMessage('danger', `Creator konnte nicht erstellt werden: ${err.message || err}`);
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const fragestellung = document.getElementById('fragestellung').value.trim();
    const question_type = questionTypeSelect.value;
    const license = licenseSelect.value;
    const status = statusSelect.value;
    const author_id = creatorSelect.value;
    const databaseValue = databaseSelect.value;
    const solution = document.getElementById('solution').value.trim();
    const metadataRaw = document.getElementById('item_metadata').value.trim();

    if (!fragestellung || !question_type || !license || !status || !author_id) {
      showMessage('warning', 'Bitte die Pflichtfelder ausfüllen.');
      return;
    }

    let item_metadata = null;
    if (metadataRaw) {
      try {
        item_metadata = JSON.parse(metadataRaw);
      } catch (error) {
        showMessage('warning', 'Das JSON in den Metadaten ist ungültig.');
        return;
      }
    }

    const payload = {
      fragestellung,
      question_type,
      license,
      status,
      author_id,
      solution: solution || null,
      item_metadata,
      database_id: databaseValue ? Number(databaseValue) : null,
    };

    try {
      const response = await fetch('/createItem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || response.statusText);
      }

      const created = await response.json();
      showMessage('success', `Item ${created.item_id} wurde erfolgreich gespeichert.`);
      form.reset();
      databaseSelect.value = '';
    } catch (error) {
      showMessage('danger', `Speichern fehlgeschlagen: ${error.message || error}`);
    }
  });

  loadSelectData();
});
