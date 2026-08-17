document.addEventListener('DOMContentLoaded', () => {
    const $ = (id) => document.getElementById(id);

    const form = $('createItemForm');
    const messageBox = $('messageBox');

    const creatorSelect = $('author_id');
    const databaseSelect = $('database_id');
    const licenseSelect = $('license');
    const statusSelect = $('status');
    const themenbereichSelect = $('themenbereich_id');
    const questionTypeSelect = $('question_type');

    const licenseMessage = $('licenseMessage');
    const statusMessage = $('statusMessage');
    const themenbereichMessage = $('themenbereichMessage');

    // ContentPieces - shared across all block sections
    let availableContentPieces = [];

    const endpoints = {
        creators: '/getAllCreator',
        databases: '/getAllDatabases',
        licenses: '/getLicence',
        statuses: '/getStatus',
        themenbereiche: '/getThemenbereich',
        questionTypes: '/getAllAvailableQuestionsTypes',
        organisations: '/getAllOrganisations',
        contentPieces: '/getAllContentPieces',
        createCreator: '/createCreator',
        createLicense: '/createLicense',
        createStatus: '/createStatus',
        createThemenbereich: '/createThemenbereich',
    };

    // -----------------------------------------------------------------------
    // Utility helpers
    // -----------------------------------------------------------------------

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    function showMessage(type, text) {
        messageBox.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${escapeHtml(text)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Schließen"></button>
      </div>`;
    }

    function showInlineMessage(container, type, text) {
        container.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${escapeHtml(text)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Schließen"></button>
      </div>`;
    }

    function setFieldMessage(container, type, text) {
        if (!container) return;
        if (!text) {
            container.innerHTML = '';
            return;
        }
        const cls = type === 'danger' ? 'text-danger' : type === 'warning' ? 'text-warning' : 'text-muted';
        container.innerHTML = `<span class="${cls}">${escapeHtml(text)}</span>`;
    }

    function parseOptionalNumber(value) {
        if (value === null || value === undefined || value === '') return null;
        const parsed = Number(value);
        return Number.isInteger(parsed) ? parsed : null;
    }

    async function fetchJson(endpoint) {
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
        return res.json();
    }

    function setOptions(select, items, placeholder, valueKey, labelResolver) {
        select.innerHTML = '';
        if (placeholder !== null) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = placeholder;
            select.appendChild(opt);
        }
        for (const item of items) {
            const opt = document.createElement('option');
            opt.value = item[valueKey];
            opt.textContent = labelResolver(item);
            select.appendChild(opt);
        }
    }

    // -----------------------------------------------------------------------
    // Content-Block builder
    // -----------------------------------------------------------------------

    function buildContentPieceSelect(selectedId = null) {
        const sel = document.createElement('select');
        sel.className = 'form-select form-select-sm content-piece-select';

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = availableContentPieces.length
            ? 'ContentPiece auswählen …'
            : '⚠ Keine ContentPieces verfügbar';
        sel.appendChild(placeholder);

        for (const cp of availableContentPieces) {
            const opt = document.createElement('option');
            opt.value = cp.content_piece_id;
            const hint = cp.data_type_name ? ` [${cp.data_type_name}]` : '';
            opt.textContent = `${cp.name}${hint}`;
            if (cp.description) opt.title = cp.description;
            sel.appendChild(opt);
        }

        if (selectedId !== null) sel.value = String(selectedId);
        return sel;
    }

    function addContentBlock(containerId) {
        const container = $(containerId);
        const row = document.createElement('div');
        row.className = 'card card-body p-2';
        row.setAttribute('data-block', '');

        const header = document.createElement('div');
        header.className = 'd-flex gap-2 align-items-center mb-2';

        const pieceSelect = buildContentPieceSelect();
        pieceSelect.style.flex = '0 0 auto';
        pieceSelect.style.width = '50%';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-outline-danger btn-sm ms-auto';
        removeBtn.textContent = '✕';
        removeBtn.addEventListener('click', () => row.remove());

        header.appendChild(pieceSelect);
        header.appendChild(removeBtn);

        const valueArea = document.createElement('textarea');
        valueArea.className = 'form-control form-control-sm content-piece-value';
        valueArea.rows = 3;
        valueArea.placeholder = 'Wert für diesen Baustein …';

        row.appendChild(header);
        row.appendChild(valueArea);
        container.appendChild(row);
    }

    function readBlocks(containerId) {
        const container = $(containerId);
        const rows = container.querySelectorAll('[data-block]');
        const result = [];
        for (const row of rows) {
            const pieceId = parseOptionalNumber(row.querySelector('.content-piece-select').value);
            const raw = row.querySelector('.content-piece-value').value.trim();
            if (pieceId === null) return null; // indicates invalid selection
            // try to parse value as JSON, fall back to string
            let value;
            try {
                value = JSON.parse(raw);
            } catch {
                value = raw;
            }
            result.push({content_piece_id: pieceId, value});
        }
        return result;
    }

    // Expose for inline onclick (fallback safety; we use addEventListener now)
    window.addContentBlock = addContentBlock;

    // -----------------------------------------------------------------------
    // Drop-down loaders
    // -----------------------------------------------------------------------

    async function populateLicenseSelect(selectedId = null) {
        setFieldMessage(licenseMessage, 'info', 'Lizenzwerte werden geladen…');
        try {
            const licenses = await fetchJson(endpoints.licenses);
            setOptions(licenseSelect, licenses, null, 'license_id', (l) => l.name || String(l.license_id));
            if (selectedId !== null) licenseSelect.value = String(selectedId);
            setFieldMessage(licenseMessage, 'info', `Geladen: ${licenses.length} Lizenz(en).`);
            return licenses;
        } catch {
            setFieldMessage(licenseMessage, 'danger', 'Lizenzen konnten nicht geladen werden.');
            return [];
        }
    }

    async function populateStatusSelect(selectedId = null) {
        setFieldMessage(statusMessage, 'info', 'Statuswerte werden geladen…');
        try {
            const statuses = await fetchJson(endpoints.statuses);
            setOptions(statusSelect, statuses, null, 'status_id', (s) => s.name || String(s.status_id));
            if (selectedId !== null) statusSelect.value = String(selectedId);
            setFieldMessage(statusMessage, 'info', `Geladen: ${statuses.length} Statuswert(e).`);
            return statuses;
        } catch {
            setFieldMessage(statusMessage, 'danger', 'Statuswerte konnten nicht geladen werden.');
            return [];
        }
    }

    async function populateThemenbereichSelect(selectedId = null) {
        setFieldMessage(themenbereichMessage, 'info', 'Themenbereiche werden geladen…');
        try {
            const list = await fetchJson(endpoints.themenbereiche);
            setOptions(themenbereichSelect, list, 'Kein Themenbereich', 'themenbereich_id', (t) => t.name || String(t.themenbereich_id));
            if (selectedId !== null) themenbereichSelect.value = String(selectedId);
            setFieldMessage(themenbereichMessage, 'info', `Geladen: ${list.length} Themenbereich(e).`);
            return list;
        } catch {
            setFieldMessage(themenbereichMessage, 'danger', 'Themenbereiche konnten nicht geladen werden.');
            return [];
        }
    }

    async function loadContentPieces() {
        try {
            availableContentPieces = await fetchJson(endpoints.contentPieces);
            if (availableContentPieces.length === 0) {
                showMessage('warning', 'Noch keine ContentPieces vorhanden. Bitte zuerst ContentPieces anlegen.');
            }
        } catch {
            showMessage('warning', 'ContentPieces konnten nicht geladen werden. Block-Builder hat keine Auswahlmöglichkeiten.');
            availableContentPieces = [];
        }
    }

    async function loadSelectData() {
        await loadContentPieces();
        await Promise.all([
            populateLicenseSelect(),
            populateStatusSelect(),
            populateThemenbereichSelect(),
        ]);

        try {
            const qTypes = await fetchJson(endpoints.questionTypes);
            setOptions(questionTypeSelect, qTypes.map((v) => ({value: v})), null, 'value', (i) => i.value);
        } catch {
            showMessage('warning', 'Fragetypen konnten nicht geladen werden.');
        }

        const errors = [];
        try {
            const creators = await fetchJson(endpoints.creators);
            setOptions(creatorSelect, creators, 'Creator auswählen', 'author_id', (c) => c.name || c.author_id);
        } catch {
            errors.push('Creators');
        }

        try {
            const databases = await fetchJson(endpoints.databases);
            setOptions(databaseSelect, databases, 'Keine Zuordnung', 'database_id', (db) => {
                const parts = [];
                if (db.database_id != null) parts.push(`ID ${db.database_id}`);
                if (db.version) parts.push(db.version);
                if (db.dialect) parts.push(db.dialect);
                return parts.length ? parts.join(' · ') : `Datenbank ${db.database_id}`;
            });
        } catch {
            errors.push('Datenbanken');
        }

        try {
            const orgs = await fetchJson(endpoints.organisations);
            setOptions($('new_creator_organisation'), orgs, 'Organisation auswählen', 'id', (o) => o.name || String(o.id));
            $('submitCreateCreator').disabled = false;
        } catch {
            errors.push('Organisationen');
            $('submitCreateCreator').disabled = true;
        }

        if (errors.length) {
            showMessage('warning', `Einige Dropdowns konnten nicht geladen werden: ${errors.join(', ')}.`);
        }
    }

    // -----------------------------------------------------------------------
    // Block add buttons
    // -----------------------------------------------------------------------

    $('addStimuliBtn').addEventListener('click', () => addContentBlock('stimuliContainer'));
    $('addInteractionBtn').addEventListener('click', () => addContentBlock('interactionContainer'));
    $('addSolutionBtn').addEventListener('click', () => addContentBlock('solutionContainer'));

    // -----------------------------------------------------------------------
    // Enum / Creator modal handlers
    // -----------------------------------------------------------------------

    $('submitCreateCreator').addEventListener('click', async () => {
        const name = $('new_creator_name').value.trim();
        const email = $('new_creator_email').value.trim();
        const role = Number($('new_creator_role').value) || 0;
        const organisation_id = $('new_creator_organisation').value || null;
        const msgEl = $('createCreatorMessage');

        if (!name || !organisation_id) {
            showInlineMessage(msgEl, 'warning', 'Name und Organisation sind erforderlich.');
            return;
        }

        try {
            const res = await fetch(endpoints.createCreator, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, email: email || null, role, organisation_id}),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            const created = await res.json();
            const opt = document.createElement('option');
            opt.value = created.author_id;
            opt.textContent = created.name || created.author_id;
            creatorSelect.appendChild(opt);
            creatorSelect.value = created.author_id;
            bootstrap.Modal.getOrCreateInstance($('createCreatorModal')).hide();
            $('createCreatorForm').reset();
            showMessage('success', `Creator ${created.name || created.author_id} angelegt.`);
        } catch (err) {
            showInlineMessage(msgEl, 'danger', `Fehler: ${err.message || err}`);
        }
    });

    async function handleEnumCreate({
                                        endpoint,
                                        nameInputId,
                                        descInputId,
                                        msgId,
                                        submitId,
                                        modalId,
                                        formId,
                                        selectId,
                                        loader
                                    }) {
        const name = $(nameInputId).value.trim();
        const description = $(descInputId).value.trim();
        const submitBtn = $(submitId);
        if (!name) {
            showInlineMessage($(msgId), 'warning', 'Name ist erforderlich.');
            return;
        }
        submitBtn.disabled = true;
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, description: description || null}),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            const created = await res.json();
            await loader(created[selectId] ?? null);
            bootstrap.Modal.getOrCreateInstance($(modalId)).hide();
            $(formId).reset();
            showMessage('success', `'${name}' wurde angelegt.`);
        } catch (err) {
            showInlineMessage($(msgId), 'danger', `Fehler: ${err.message || err}`);
        } finally {
            submitBtn.disabled = false;
        }
    }

    $('submitCreateLicense').addEventListener('click', () => handleEnumCreate({
        endpoint: endpoints.createLicense, nameInputId: 'new_license_name', descInputId: 'new_license_description',
        msgId: 'createLicenseMessage', submitId: 'submitCreateLicense', modalId: 'createLicenseModal',
        formId: 'createLicenseForm', selectId: 'license_id', loader: populateLicenseSelect,
    }));

    $('submitCreateStatus').addEventListener('click', () => handleEnumCreate({
        endpoint: endpoints.createStatus, nameInputId: 'new_status_name', descInputId: 'new_status_description',
        msgId: 'createStatusMessage', submitId: 'submitCreateStatus', modalId: 'createStatusModal',
        formId: 'createStatusForm', selectId: 'status_id', loader: populateStatusSelect,
    }));

    $('submitCreateThemenbereich').addEventListener('click', () => handleEnumCreate({
        endpoint: endpoints.createThemenbereich,
        nameInputId: 'new_themenbereich_name',
        descInputId: 'new_themenbereich_description',
        msgId: 'createThemenbereichMessage',
        submitId: 'submitCreateThemenbereich',
        modalId: 'createThemenbereichModal',
        formId: 'createThemenbereichForm',
        selectId: 'themenbereich_id',
        loader: populateThemenbereichSelect,
    }));

    // -----------------------------------------------------------------------
    // Form submit
    // -----------------------------------------------------------------------

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        // --- basic fields ---
        const fragestellung = $('fragestellung').value.trim();
        if (!fragestellung) {
            showMessage('warning', 'Fragestellung ist erforderlich.');
            return;
        }

        const question_type = questionTypeSelect.value;
        const license = parseOptionalNumber(licenseSelect.value);
        const status_id = parseOptionalNumber(statusSelect.value);
        const themenbereich_id = parseOptionalNumber(themenbereichSelect.value);
        const author_id = creatorSelect.value;
        const database_id = parseOptionalNumber(databaseSelect.value);

        if (!question_type || license === null || status_id === null || !author_id) {
            showMessage('warning', 'Bitte alle Pflichtfelder ausfüllen (Fragetyp, Lizenz, Status, Creator).');
            return;
        }

        // --- metadata ---
        const metadataRaw = $('item_metadata').value.trim();
        if (!metadataRaw) {
            showMessage('warning', '`item_metadata` ist ein Pflichtfeld.');
            return;
        }
        let item_metadata;
        try {
            item_metadata = JSON.parse(metadataRaw);
        } catch {
            showMessage('warning', 'JSON in item_metadata ist ungültig.');
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

        // --- content blocks ---
        const stimuli_content = readBlocks('stimuliContainer');
        const interaction_content = readBlocks('interactionContainer');
        const solutionBlocks = readBlocks('solutionContainer');

        if (!stimuli_content || stimuli_content.length === 0) {
            $('stimuliMessage').classList.remove('d-none');
            showMessage('warning', 'Mindestens ein Stimuli-Baustein ist erforderlich.');
            return;
        }
        $('stimuliMessage').classList.add('d-none');

        if (!interaction_content || interaction_content.length === 0) {
            $('interactionMessage').classList.remove('d-none');
            showMessage('warning', 'Mindestens ein Interaction-Baustein ist erforderlich.');
            return;
        }
        $('interactionMessage').classList.add('d-none');

        // null return means a piece was selected as empty
        if (stimuli_content === null) {
            showMessage('warning', 'Alle Stimuli-Bausteine müssen ein ContentPiece auswählen.');
            return;
        }
        if (interaction_content === null) {
            showMessage('warning', 'Alle Interaction-Bausteine müssen ein ContentPiece auswählen.');
            return;
        }
        if (solutionBlocks === null) {
            showMessage('warning', 'Alle Lösungs-Bausteine müssen ein ContentPiece auswählen.');
            return;
        }

        const solution = (solutionBlocks && solutionBlocks.length > 0) ? solutionBlocks : null;

        const payload = {
            fragestellung,
            question_type,
            license,
            status_id,
            themenbereich_id,
            author_id,
            database_id,
            item_metadata,
            stimuli_content,
            interaction_content,
            solution,
        };

        console.log('[createItem] payload:', payload);

        try {
            const res = await fetch('/createItem', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(((await res.json().catch(() => ({}))).detail) || res.statusText);
            await res.json();
            showMessage('success', 'Item wurde erfolgreich gespeichert.');
            form.reset();
            $('stimuliContainer').innerHTML = '';
            $('interactionContainer').innerHTML = '';
            $('solutionContainer').innerHTML = '';
        } catch (err) {
            showMessage('danger', `Speichern fehlgeschlagen: ${err.message || err}`);
        }
    });

    // -----------------------------------------------------------------------
    // Init
    // -----------------------------------------------------------------------

    loadSelectData();
});