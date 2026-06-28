document.addEventListener('DOMContentLoaded', () => {
  const $ = (id) => document.getElementById(id);

  const form = $('createItemForm');
  const messageBox = $('messageBox');

  const creatorSelect = $('author_id');
  const databaseSelect = $('database_id');
  const licenseSelect = $('license');
  const statusSelect = $('status');
  const questionTypeSelect = $('question_type');

  const programmingOutputGroup = $('programmingOutputGroup');
  const solutionOutputInput = $('solution_output');

  // Creator modal
  const createCreatorForm = $('createCreatorForm');
  const submitCreateCreator = $('submitCreateCreator');
  const createCreatorMessage = $('createCreatorMessage');
  const newCreatorName = $('new_creator_name');
  const newCreatorEmail = $('new_creator_email');
  const newCreatorRole = $('new_creator_role');
  const newCreatorOrganisation = $('new_creator_organisation');

  const endpoints = {
    creators: '/getAllCreator',
    databases: '/getAllDatabases',
    licenses: '/getAllAvailableLicenseTypes',
    statuses: '/getAllAvailableStatusTypes',
    questionTypes: '/getAllAvailableQuestionsTypes',
    organisations: '/getAllOrganisations',
    createCreator: '/createCreator',
  };

  const isProgramming = () => questionTypeSelect.value === 'PROGRAMMIERUNG';
  const isSingleChoice = () => questionTypeSelect.value === 'SINGLECHOICE';
  const isMultipleChoice = () => questionTypeSelect.value === 'MULTIPLECHOICE';
  const isChoiceType = () => isSingleChoice() || isMultipleChoice();

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

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

  function ensureChoiceInputMode() {
    const inputs = document.querySelectorAll('.mc-correct-option');

    if (isSingleChoice()) {
      let firstCheckedFound = false;
      inputs.forEach((input) => {
        input.type = 'radio';
        input.name = 'mc_correct_option_group';
        if (input.checked) {
          if (firstCheckedFound) input.checked = false;
          firstCheckedFound = true;
        }
      });
      return;
    }

    inputs.forEach((input) => {
      input.type = 'checkbox';
      input.removeAttribute('name');
    });
  }

  function addMcOption() {
    const container = $('mcOptionsContainer');
    const optionIndex = container.querySelectorAll('[data-option-index]').length;

    const inputType = isSingleChoice() ? 'radio' : 'checkbox';
    const checkboxId = `mc_correct_${optionIndex}`;
    const radioAttrs = isSingleChoice() ? 'name="mc_correct_option_group"' : '';

    const optionDiv = document.createElement('div');
    optionDiv.className = 'input-group mb-2';
    optionDiv.setAttribute('data-option-index', optionIndex);
    optionDiv.innerHTML = `
      <input type="${inputType}" class="form-check-input mc-correct-option" id="${checkboxId}" ${radioAttrs} style="margin-left: 0.5rem;">
      <label class="form-check-label" for="${checkboxId}" style="margin-right: 0.5rem; margin-left: 0.25rem;">Richtig</label>
      <span class="input-group-text mc-option-number">${optionIndex + 1}</span>
      <input type="text" class="form-control mc-option-text" placeholder="Optionstext">
      <button type="button" class="btn btn-outline-danger" onclick="removeMcOption(this)">Löschen</button>
    `;
    container.appendChild(optionDiv);
    renumberMcOptions();
  }

  function renumberMcOptions() {
    const rows = Array.from(document.querySelectorAll('#mcOptionsContainer [data-option-index]'));
    rows.forEach((row, index) => {
      row.setAttribute('data-option-index', String(index));

      const numberBadge = row.querySelector('.mc-option-number');
      if (numberBadge) numberBadge.textContent = String(index + 1);

      const correctInput = row.querySelector('.mc-correct-option');
      const correctLabel = row.querySelector('.form-check-label');
      if (correctInput && correctLabel) {
        const newId = `mc_correct_${index}`;
        correctInput.id = newId;
        correctLabel.setAttribute('for', newId);
      }
    });
  }

  function rebuildMcUi() {
    const container = $('mcOptionsContainer');
    const existingCount = container.querySelectorAll('[data-option-index]').length;
    if (existingCount === 0) {
      addMcOption();
      addMcOption();
    }
  }

  function updateUiByQuestionType() {
    programmingOutputGroup.classList.toggle('d-none', !isProgramming());

    // Eine gemeinsame Fragestellungs-Textarea für alle Typen
    $('fragestellungMultipleChoice').classList.toggle('d-none', !isChoiceType());

    // Musterlösung ausblenden bei Choice-Typen
    $('solutionText').classList.toggle('d-none', isChoiceType());

    if (isChoiceType()) {
      rebuildMcUi();
      ensureChoiceInputMode();
    }
  }

  async function loadSelectData() {
    let licenses = null;
    let statuses = null;
    let questionTypes = null;

    try {
      const [licensesRes, statusesRes, questionTypesRes] = await Promise.all([
        fetch(endpoints.licenses),
        fetch(endpoints.statuses),
        fetch(endpoints.questionTypes),
      ]);
      if (licensesRes.ok) licenses = await licensesRes.json();
      if (statusesRes.ok) statuses = await statusesRes.json();
      if (questionTypesRes.ok) questionTypes = await questionTypesRes.json();
    } catch (_) {
      // ignore; warnings below
    }

    if (licenses) setOptions(licenseSelect, licenses.map((v) => ({ value: v })), null, 'value', (i) => i.value);
    else showMessage('warning', 'Lizenztypen konnten nicht geladen werden.');

    if (statuses) setOptions(statusSelect, statuses.map((v) => ({ value: v })), null, 'value', (i) => i.value);
    else showMessage('warning', 'Status-Typen konnten nicht geladen werden.');

    if (questionTypes) setOptions(questionTypeSelect, questionTypes.map((v) => ({ value: v })), null, 'value', (i) => i.value);
    else showMessage('warning', 'QuestionTypes konnten nicht geladen werden.');

    updateUiByQuestionType();

    let creators = null;
    let databases = null;
    let organisations = null;
    const dbErrors = [];

    try {
      const res = await fetch(endpoints.creators);
      if (res.ok) creators = await res.json();
      else dbErrors.push('Creators');
    } catch (_) { dbErrors.push('Creators'); }

    try {
      const res = await fetch(endpoints.databases);
      if (res.ok) databases = await res.json();
      else dbErrors.push('Databases');
    } catch (_) { dbErrors.push('Databases'); }

    try {
      const res = await fetch(endpoints.organisations);
      if (res.ok) organisations = await res.json();
      else dbErrors.push('Organisations');
    } catch (_) { dbErrors.push('Organisations'); }

    if (creators) {
      setOptions(creatorSelect, creators, 'Creator auswählen', 'author_id', (creator) =>
        creator.name ? `${creator.name}` : creator.author_id
      );
    } else {
      creatorSelect.innerHTML = '';
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Creators nicht verfügbar';
      creatorSelect.appendChild(opt);
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
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Datenbanken nicht verfügbar';
      databaseSelect.appendChild(opt);
      databaseSelect.disabled = true;
    }

    if (organisations) {
      setOptions(newCreatorOrganisation, organisations, 'Organisation auswählen', 'id', (org) => org.name || String(org.id));
      submitCreateCreator.disabled = false;
    } else {
      newCreatorOrganisation.innerHTML = '';
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Orgs nicht verfügbar';
      newCreatorOrganisation.appendChild(opt);
      submitCreateCreator.disabled = true;
      showInlineCreatorMessage('warning', 'Organisationen nicht erreichbar. Neue Creator können nicht angelegt werden.');
    }

    if (dbErrors.length) {
      showMessage('warning', `Einige DB-gebundene Dropdowns konnten nicht geladen werden: ${dbErrors.join(', ')}.`);
    }
  }

  // global für inline onclick
  window.removeMcOption = function removeMcOption(btn) {
    btn.closest('[data-option-index]').remove();
    renumberMcOptions();
  };

  submitCreateCreator.addEventListener('click', async () => {
    const name = newCreatorName.value.trim();
    const email = newCreatorEmail.value.trim();
    const role = Number(newCreatorRole.value) || 0;
    const organisation_id = newCreatorOrganisation.value || null;

    if (!name || !organisation_id) {
      showInlineCreatorMessage('warning', 'Name und Organisation sind erforderlich.');
      return;
    }

    const payload = { name, email: email || null, role, organisation_id };

    try {
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
      const option = document.createElement('option');
      option.value = created.author_id;
      option.textContent = created.name || created.author_id;
      creatorSelect.appendChild(option);
      creatorSelect.value = created.author_id;

      const modalEl = $('createCreatorModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal.hide();

      createCreatorForm.reset();
      showMessage('success', `Creator ${created.name || created.author_id} angelegt.`);
    } catch (err) {
      showInlineCreatorMessage('danger', `Creator konnte nicht erstellt werden: ${err.message || err}`);
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const question_type = questionTypeSelect.value;
    const license = licenseSelect.value;
    const status = statusSelect.value;
    const author_id = creatorSelect.value;
    const databaseValue = databaseSelect.value;
    const metadataRaw = $('item_metadata').value.trim();
    const solutionOutput = solutionOutputInput.value.trim();

    let fragestellung = null;
    let solution = null;

    if (isChoiceType()) {
      const prompt = $('fragestellung').value.trim();
      if (!prompt) {
        showMessage('warning', 'Bitte den Fragetext eingeben.');
        return;
      }

      const optionElements = document.querySelectorAll('[data-option-index]');
      if (optionElements.length < 2) {
        showMessage('warning', 'Mindestens 2 Antwortoptionen erforderlich.');
        return;
      }

      const options = Array.from(optionElements).map((div, index) => ({
        option_id: String(index + 1),
        text: div.querySelector('.mc-option-text').value || '',
      }));

      if (options.some((o) => !o.text.trim())) {
        showMessage('warning', 'Alle Optionen müssen einen Text haben.');
        return;
      }

      fragestellung = prompt;

      const correctOptionIds = Array.from(document.querySelectorAll('.mc-correct-option:checked')).map((cb) => {
        const div = cb.closest('[data-option-index]');
        const optionIndex = Number(div.getAttribute('data-option-index') || '0');
        return String(optionIndex + 1);
      });

      if (correctOptionIds.length === 0) {
        showMessage('warning', 'Bitte mindestens eine korrekte Option auswählen.');
        return;
      }

      solution = { options, correct_option_ids: correctOptionIds };
    } else {
      fragestellung = $('fragestellung').value.trim();
      if (!fragestellung) {
        showMessage('warning', 'Bitte die Fragestellung eingeben.');
        return;
      }

      const solutionText = $('solution').value.trim();
      if (isProgramming()) {
        if (solutionText) {
          solution = { text: solutionText, output: solutionOutput || null };
        }
      } else {
        solution = solutionText || null;
      }
    }

    if (!question_type || !license || !status || !author_id) {
      showMessage('warning', 'Bitte die Pflichtfelder ausfüllen.');
      return;
    }

    if (!metadataRaw) {
      showMessage('warning', 'Bitte `item_metadata` als JSON angeben (Pflichtfeld inkl. `bloomlevel`).');
      return;
    }

    let item_metadata = null;
    try {
      item_metadata = JSON.parse(metadataRaw);
    } catch (_) {
      showMessage('warning', 'Das JSON in den Metadaten ist ungültig.');
      return;
    }

    if (!item_metadata || typeof item_metadata !== 'object' || Array.isArray(item_metadata)) {
      showMessage('warning', '`item_metadata` muss ein JSON-Objekt sein.');
      return;
    }

    const bloomlevel = item_metadata.bloomlevel;
    if (bloomlevel === undefined || bloomlevel === null || (typeof bloomlevel === 'string' && !bloomlevel.trim())) {
      showMessage('warning', '`item_metadata.bloomlevel` muss gesetzt sein.');
      return;
    }

    const payload = {
      fragestellung,
      question_type,
      license,
      status,
      author_id,
      solution,
      item_metadata,
      database_id: databaseValue ? Number(databaseValue) : null,
    };

    console.log('[createItem] payload:', payload);

    try {
      const response = await fetch('/createItem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || response.statusText);
      }

      const created = await response.json();
      showMessage('success', `Item wurde erfolgreich gespeichert.`);

      form.reset();
      databaseSelect.value = '';
      solutionOutputInput.value = '';
      $('mcOptionsContainer').innerHTML = '';
      updateUiByQuestionType();
    } catch (error) {
      showMessage('danger', `Speichern fehlgeschlagen: ${error.message || error}`);
    }
  });

  questionTypeSelect.addEventListener('change', updateUiByQuestionType);

  document.addEventListener('click', (e) => {
    if (e.target && e.target.id === 'addMcOption') {
      addMcOption();
    }
  });

  loadSelectData();
});