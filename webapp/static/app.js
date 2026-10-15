'use strict';

(() => {
  const content = document.querySelector('#content');
  const notice = document.querySelector('#notice');
  const runId = document.body.dataset.runId;
  const drafts = new Map();
  let currentRun = null;
  let pollTimer = null;
  let requestPending = false;
  let staleDraft = false;
  const statusNames = {
    queued: 'Queued', analysing: 'Checking evidence', awaiting_scope: 'Scope decision needed',
    planning: 'Preparing audit plan', awaiting_signoff: 'Signoff needed', signed_off: 'Signed off',
    returned: 'Returned for revision', failed: 'Review stopped', requires_model: 'No risks retained'
  };
  const number = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 2 });
  const money = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 2 });

  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value === undefined || value === null) continue;
      if (key === 'class') node.className = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else if (key === 'checked' || key === 'disabled' || key === 'required') node[key] = Boolean(value);
      else node.setAttribute(key, String(value));
    }
    for (const child of children.flat()) {
      if (child !== undefined && child !== null) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }
  function showNotice(message, error = false) {
    notice.textContent = message;
    notice.classList.toggle('error', error);
    notice.hidden = false;
  }
  function clearNotice() { notice.hidden = true; notice.textContent = ''; }
  function readable(value) {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'number') return number.format(value);
    if (Array.isArray(value)) return value.map(readable).join(', ');
    if (typeof value === 'object') return Object.entries(value).map(([k, v]) => `${label(k)}: ${readable(v)}`).join('; ');
    return String(value);
  }
  function label(value) { return String(value).replaceAll('_', ' ').replace(/^./, c => c.toUpperCase()); }
  function time(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? readable(value) : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }
  function safeURL(value) {
    if (typeof value !== 'string') return null;
    try {
      const url = new URL(value, location.origin);
      return url.origin === location.origin && ['http:', 'https:'].includes(url.protocol) ? url.href : null;
    } catch { return null; }
  }
  function errorDetail(data, fallback) {
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.map(item => {
      const field = Array.isArray(item.loc) ? item.loc.filter(x => x !== 'body').join(' · ') : '';
      return `${field ? `${label(field)}: ` : ''}${item.msg || 'Check this entry.'}`;
    }).join(' ');
    return fallback;
  }
  async function api(path, options = {}) {
    const response = await fetch(path, { credentials: 'same-origin', ...options,
      headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(errorDetail(data, `The request could not be completed (${response.status}). Try again.`));
      error.status = response.status;
      throw error;
    }
    return data;
  }
  function panel(title, ...children) { return el('section', { class: 'panel' }, el('h2', {}, title), ...children); }
  function status(run) {
    const good = run.status === 'signed_off';
    const bad = ['failed', 'returned', 'requires_model'].includes(run.status);
    const waiting = ['awaiting_scope', 'awaiting_signoff'].includes(run.status);
    return el('span', { class: `status${good ? ' good' : bad ? ' error' : waiting ? ' waiting' : ''}` }, statusNames[run.status] || label(run.status));
  }
  function field(text, input, hint) {
    return el('div', { class: 'field' }, el('label', { for: input.id }, text), input, hint ? el('span', { class: 'muted' }, hint) : null);
  }
  function getDraft(id) {
    if (!drafts.has(id)) drafts.set(id, { scope: { reviewer: '', date: '', decisions: {} }, signoff: { reviewer: '', date: '', comment: '', decision: 'sign_off' } });
    return drafts.get(id);
  }

  async function loadHistory() {
    const target = document.querySelector('#run-history');
    try {
      const data = await api('/api/runs');
      target.replaceChildren(...(data.runs?.length ? data.runs.map(run => el('a', {
        class: 'history-link', href: `/runs/${encodeURIComponent(run.id)}`, 'aria-current': run.id === runId ? 'page' : null
      }, run.title || 'Untitled review', el('span', {}, statusNames[run.status] || label(run.status)))) : [el('p', { class: 'muted' }, 'No reviews yet. Start one to record your scope decisions.') ]));
    } catch (error) { target.replaceChildren(el('p', { class: 'muted' }, 'Review history is unavailable. ', error.message)); }
  }
  async function loadSources() {
    const config = await api('/api/config');
    const data = config.dataset || {};
    document.querySelector('#source-summary').textContent = [data.label, data.period, data.original_rows !== undefined ? `${number.format(data.original_rows)} original rows` : ''].filter(Boolean).join(' · ');
    document.querySelector('#source-list').replaceChildren(...(data.source_files || []).map(file => el('li', {}, safeURL(file.url) ? el('a', {href:safeURL(file.url),download:''},file.name) : file.name, el('small', {}, label(file.kind || 'Source document')))));
    return config;
  }
  function provenance() {
    document.querySelector('#run-provenance').replaceChildren(el('strong',{},'Claude audit workflow'),
      el('span',{},'New risk assessment, planning and team review. Fixed source extractions are reused and verified.'));
  }
  function renderHome(config) {
    const live=config.live_available===true;
    provenance();
    const title=el('input',{id:'review-title',name:'title',required:true,maxlength:100,placeholder:'e.g. Procurement audit review',autocomplete:'off'});
    const submit=el('button',{class:'button',type:'submit',disabled:!live},'Start review');
    const form=el('form',{onsubmit:async event=>{
      event.preventDefault();if(requestPending||!live||!form.reportValidity())return;
      requestPending=true;submit.disabled=true;clearNotice();
      try{
        const run=await api('/api/runs',{method:'POST',body:JSON.stringify({title:title.value.trim(),mode:'live'})});
        location.assign(`/runs/${encodeURIComponent(run.id)}`);
      }catch(error){showNotice(error.message,true);requestPending=false;submit.disabled=false;}
    }},field('Review title',title),
      el('p',{},'Recompute the supplied data and generate a risk assessment. After you decide the scope, the planning team prepares and checks an audit plan.'),submit,
      el('p',{class:'check-note'},'Every review starts with blank scope decisions and no signature.'));
    content.replaceChildren(el('div',{class:'intro'},el('div',{class:'eyebrow'},'Procurement audit planning'),
      el('h1',{},'From evidence to an agreed audit plan.'),el('p',{},'Assess the risks, decide the scope, review the team’s work and record your final decision.'),
      el('a',{class:'button secondary',href:'/example/'},'View completed example')),
      el('div',{class:'create-grid'},panel('Start a review',form),panel('How the review works',
        el('ol',{},el('li',{},'Verify sources and recompute payment indicators.'),el('li',{},'Review the cited risk register and decide the scope.'),
          el('li',{},'Prepare the plan, resolve challenges and run four checks.'),el('li',{},'Inspect the working papers, sign off or request revision.')),
        !live?el('p',{class:'notice'},'The server needs an Anthropic API key before reviews can start.'):null)));
  }

  function workflow(run) {
    const position = { queued: 0, analysing: 0, awaiting_scope: 1, planning: 2, awaiting_signoff: 3, signed_off: 4, returned: 3 }[run.status] ?? (run.decisions ? 2 : 0);
    const steps = ['Check evidence', 'Decide scope', 'Prepare plan', 'Review & sign off'];
    return el('ol', { class: 'workflow', 'aria-label': 'Review workflow' }, steps.map((text, index) => el('li', {
      class: index < position ? 'complete' : index === position ? 'current' : '', 'aria-current': index === position ? 'step' : null
    }, el('span', { class: 'step-number', 'aria-hidden': 'true' }, index < position ? '✓' : index + 1),
    el('span', {}, text, el('span', { class: 'visually-hidden' }, index < position ? ' — complete' : index === position ? ' — current step' : ' — upcoming')))));
  }
  function metrics(run) {
    const data = run.dataset_summary;
    if (!data || Object.keys(data).length === 0) return null;
    const values = [
      ['Original rows', readable(data.rows_raw), 'Before cleaning'], ['Retained rows', readable(data.rows_retained), 'After cleaning'],
      ['Retained spend', typeof data.total_gbp === 'number' ? money.format(data.total_gbp) : readable(data.total_gbp), 'GBP'],
      ['Months covered', Array.isArray(data.months) ? data.months.length : readable(data.months), Array.isArray(data.months) ? data.months.join(', ') : 'Source period']
    ];
    return el('dl', { class: 'metric-grid', 'aria-label': 'Dataset summary' }, values.map(([title, value, hint]) => el('div', { class: 'metric' }, el('dt', {}, title), el('dd', {}, value), el('small', {}, hint))));
  }
  function riskContext(risk) {
    return [el('span', { class: 'risk-id' }, risk.id), el('span', { class: 'risk-title' }, risk.title || risk.risk),
      risk.title && risk.risk ? el('p', { class: 'risk-description' }, risk.risk) : null,
      risk.proposed_focus ? el('p', { class: 'risk-focus' }, el('strong', {}, 'Proposed focus: '), readable(risk.proposed_focus)) : null];
  }
  function rating(risk) {
    return el('div', { class: 'risk-rating', 'aria-label': 'Risk assessment' }, el('span', {}, 'Likelihood ', readable(risk.likelihood)), el('span', {}, 'Impact ', readable(risk.impact)), el('span', {}, 'Score ', readable(risk.score)), risk.band ? el('strong', { class: 'band' }, risk.band) : null);
  }
  function reviewerFields(draft, prefix) {
    const reviewer = el('input', { id: `${prefix}-reviewer`, name: 'reviewer', required: true, maxlength: 100, autocomplete: 'off', value: draft.reviewer, oninput: event => { draft.reviewer = event.target.value; } });
    const date = el('input', { id: `${prefix}-date`, name: 'date', type: 'date', required: true, value: draft.date, oninput: event => { draft.date = event.target.value; } });
    return el('div', { class: 'reviewer-fields' }, field('Reviewer name', reviewer), field('Decision date', date));
  }
  function renderScope(run) {
    const draft = getDraft(run.id).scope;
    const rowControls = [];
    const rows = (run.risks || []).map((risk, index) => {
      const id = String(risk.id);
      if (!draft.decisions[id]) draft.decisions[id] = { id: risk.id, decision: '', comment: '', in_scope: risk.recommend_in_scope !== false };
      const decision = draft.decisions[id];
      const select = el('select', { id: `risk-${index}-decision`, required: true, 'aria-label': `Decision for ${risk.id}` },
        [['', 'Choose a decision'], ['approve', 'Approve'], ['amend', 'Amend scope'], ['reject', 'Reject']].map(([value, text]) => el('option', { value }, text)));
      select.value = decision.decision;
      const include = el('input', { type: 'checkbox', id: `risk-${index}-include`, checked: decision.in_scope, onchange: event => { decision.in_scope = event.target.checked; } });
      const comment = el('textarea', { id: `risk-${index}-comment`, rows: 2, maxlength: 2000, placeholder: 'Add a reason or scope note', oninput: event => { decision.comment = event.target.value; } }, decision.comment);
      const sync = () => {
        include.disabled = select.value !== 'amend';
        comment.required = select.value === 'reject';
        if (select.value === 'reject') { include.checked = false; decision.in_scope = false; }
        else if (select.value === 'approve') { include.checked = risk.recommend_in_scope !== false; decision.in_scope = include.checked; }
      };
      select.addEventListener('change', () => { decision.decision = select.value; sync(); selectionNote.textContent = 'Review every decision, add your name and date, then confirm scope.'; });
      sync(); rowControls.push({ select, sync, decision });
      return el('tr', {}, el('td', {}, ...riskContext(risk)), el('td', {}, rating(risk)), el('td', {},
        field('Decision', select), el('div', { class: 'field' }, el('label', { class: 'checkbox-label', for: include.id }, include, 'Include in audit scope')),
        field('Comment (required when rejecting)', comment)));
    });
    const approveAll = el('button', { class: 'button small secondary', type: 'button', onclick: () => {
      rowControls.forEach(({ select, sync, decision }) => { select.value = 'approve'; decision.decision = 'approve'; sync(); });
      selectionNote.textContent = 'Approve selected for every risk. Review the entries, add your name and date, then confirm scope.';
    } }, 'Select approve for all');
    const selectionNote = el('p', { class: 'check-note', role: 'status' }, 'Selecting approve for all does not confirm scope.');
    const submit = el('button', { class: 'button', type: 'submit' }, 'Confirm scope & prepare plan');
    const form = el('form', { onsubmit: async event => {
      event.preventDefault();
      if (requestPending || !form.reportValidity()) return;
      const decisions = (run.risks || []).map(risk => ({ ...draft.decisions[String(risk.id)], comment: draft.decisions[String(risk.id)].comment.trim() }));
      if (!decisions.length) { showNotice('Risk assessment is unavailable. Refresh the review before confirming scope.', true); return; }
      if (decisions.some(item => item.decision === 'reject' && !item.comment)) { showNotice('Add a reason for every rejected risk.', true); return; }
      await mutate(run, `/api/runs/${encodeURIComponent(run.id)}/scope`, { expected_version: run.version, reviewer: draft.reviewer.trim(), date: draft.date, decisions }, form);
    } }, el('div', { class: 'panel-heading' }, el('div', {}, el('h2', {}, 'Decide the audit scope'),
      el('p', { class: 'muted' }, 'Make an explicit decision on every risk. Amend scope to change inclusion, or reject a risk with a reason.')), approveAll),
      el('div', { class: 'table-wrap' }, el('table', { class: 'risk-table' }, el('caption', { class: 'visually-hidden' }, 'Risk assessment and scope decisions'),
        el('thead', {}, el('tr', {}, el('th', { scope: 'col' }, 'Risk & proposed focus'), el('th', { scope: 'col' }, 'Assessment'), el('th', { scope: 'col' }, 'Your scope decision'))), el('tbody', {}, rows))),
      selectionNote, el('div', { class: 'form-footer' }, reviewerFields(draft, 'scope'), submit));
    return el('section', { class: 'panel' }, form);
  }
  function decisionsPanel(run) {
    if (!run.decisions?.length) return null;
    const risks = new Map((run.risks || []).map(risk => [String(risk.id), risk]));
    return el('details', {}, el('summary', {}, 'Confirmed scope decisions'), el('div', { class: 'panel details-body' },
      el('ul', { class: 'decision-list' }, run.decisions.map(item => {
        const risk = risks.get(String(item.id));
        return el('li', {}, el('strong', {}, `${item.id}${risk?.title ? ` · ${risk.title}` : ''}`),
          ` — ${label(item.decision)} · ${item.in_scope ? 'In scope' : 'Excluded from scope'}`, item.comment ? el('p', { class: 'muted' }, item.comment) : null);
      }))));
  }
  function qaPanel(run) {
    if (!run.qa?.length) return null;
    const rows = run.qa.map(check => el('tr', {},
      el('td', {}, check.name),
      el('td', {}, el('span', { class: `qa-result ${/^(pass|passed|ok)$/i.test(check.result) ? 'pass' : /fail/i.test(check.result) ? 'fail' : ''}` }, readable(check.result))),
      el('td', {}, readable(check.summary))));
    return panel('Quality checks', el('p', { class: 'muted' }, 'Results from the checks run for this review.'),
      el('div', { class: 'table-wrap' }, el('table', {}, el('caption', { class: 'visually-hidden' }, 'Exact quality check results'),
        el('thead', {}, el('tr', {}, ['Check', 'Result', 'Summary'].map(text => el('th', { scope: 'col' }, text)))),
        el('tbody', {}, rows))));
  }
  function figurePanel(run) {
    if (!run.figures || Object.keys(run.figures).length === 0) return null;
    const leaves = [];
    const names = { sample_occurrences: 'Sample occurrences', unique_payments: 'Unique payments', unique_sample_gbp: 'Unique sample amount (GBP)', controls: 'Controls', tests: 'Audit tests', pbc_requests: 'PBC requests' };
    function walk(data, prefix = '') {
      for (const [key, value] of Object.entries(data)) {
        const name = `${prefix}${names[key] || label(key)}`;
        if (value && typeof value === 'object' && !Array.isArray(value)) walk(value, `${name} · `);
        else leaves.push(el('div', {}, el('dt', {}, name), el('dd', {}, key === 'unique_sample_gbp' && typeof value === 'number' ? money.format(value) : readable(value))));
      }
    }
    walk(run.figures);
    return el('details', { open: '' }, el('summary', {}, 'Evidence figures & sample basis'), el('section', { class: 'panel details-body' },
      el('p', { class: 'muted' }, 'Figures keep their source labels. Risk occurrences may overlap; occurrence counts and totals are not unique transaction counts or spend.'), el('dl', { class: 'figure-list' }, leaves)));
  }
  function artifactsPanel(run) {
    if (!run.artifacts?.length) return null;
    const names = { 'risk-register.md':'Risk register', 'auditor-comments.md':'Scope decisions',
      'planning-memo.md':'Planning memo', 'risk-control-matrix.md':'Risk-control matrix',
      'audit-program.md':'Audit program & document requests', 'review.md':'Quality review & sign-off',
      'challenges.md':'Independent challenge review', 'scope-result.md':'Scope decision result' };
    function rows(items) {
      return el('ul', { class:'artifact-list' }, items.map(artifact => {
        const url = safeURL(artifact.url); const preview = safeURL(artifact.view_url);
        const title = names[artifact.name] || artifact.name;
        return el('li', {}, el('div', {}, el('span', { class:'artifact-name' }, title), el('span', { class:'artifact-kind' }, label(artifact.kind || 'Document'))),
          el('div', { class:'artifact-actions' }, preview ? el('button', { class:'button small secondary',type:'button',
            'aria-label':`Preview ${title}`,onclick:()=>openDocument(title,preview) }, 'Preview') : null,
            url ? el('a', {href:url,download:'','aria-label':`Download ${title}`}, 'Download') : el('span',{class:'muted'},'File unavailable')));
      }));
    }
    const main = run.artifacts.filter(x=>names[x.name]);
    const supporting = run.artifacts.filter(x=>!names[x.name]);
    return panel('Working papers', el('p',{class:'muted'},'Review the scope and planning papers before signing off.'), rows(main),
      supporting.length ? el('details',{},el('summary',{},'Supporting data, samples & validation files'),rows(supporting)) : null);
  }
  function openDocument(name, url) {
    const dialog = document.querySelector('#document-dialog');
    document.querySelector('#document-title').textContent = name || 'Document preview';
    document.querySelector('#document-frame').src = url;
    dialog.showModal();
  }
  document.querySelector('#close-document').addEventListener('click', () => document.querySelector('#document-dialog').close());
  document.querySelector('#document-dialog').addEventListener('close', () => { document.querySelector('#document-frame').removeAttribute('src'); });

  function signoffPanel(run) {
    const draft = getDraft(run.id).signoff;
    const choice = el('select', { id: 'signoff-decision', required: true, onchange: event => { draft.decision = event.target.value; update(); } },
      el('option', { value: 'sign_off' }, 'Sign off the working papers'), el('option', { value: 'return' }, 'Return for revision'));
    choice.value = draft.decision;
    const comment = el('textarea', { id: 'signoff-comment', rows: 3, maxlength: 2000, oninput: event => { draft.comment = event.target.value; } }, draft.comment);
    const submit = el('button', { class: 'button', type: 'submit' });
    const explanation = el('p', { class: 'muted' });
    function update() {
      const returning = choice.value === 'return';
      comment.required = returning;
      submit.textContent = returning ? 'Return for revision' : 'Sign off working papers';
      submit.classList.toggle('danger', returning);
      explanation.textContent = returning ? 'Returning sends your comments back to the planning team. The revised pack will need another sign-off.' : 'Signoff records your name and decision date, and makes the complete ZIP available.';
    }
    update();
    const form = el('form', { onsubmit: async event => {
      event.preventDefault();
      if (requestPending || !form.reportValidity()) return;
      if (draft.decision === 'return' && !draft.comment.trim()) { showNotice('Add a comment explaining the revision needed.', true); return; }
      await mutate(run, `/api/runs/${encodeURIComponent(run.id)}/signoff`, { expected_version: run.version, reviewer: draft.reviewer.trim(), date: draft.date, decision: draft.decision, comment: draft.comment.trim() }, form);
    } }, el('h2', {}, 'Review & sign off'), el('p', { class: 'muted' }, 'Review the scope, working papers and quality checks before recording your decision.'),
      field('Final decision', choice), explanation, run.auditor_points?.length?el('div',{class:'notice'},el('strong',{},'Points requiring your decision'),el('ul',{},run.auditor_points.map(x=>el('li',{},x.challenge+' '+x.response))),el('p',{},'Explain your decision in the comment before signing off.')):null, reviewerFields(draft, 'signoff'), field('Comment (required when returning)', comment), submit);
    return el('section', { class: 'panel' }, form);
  }
  function statePanel(run) {
    const texts = {
      queued: ['Review queued', 'The review is waiting to start. This page updates automatically.'],
      analysing: ['Checking the supplied evidence', 'The data checks and a new model risk assessment are running. This page updates automatically.'],
      planning: ['Preparing the scoped audit plan', 'The plan is being prepared using your confirmed scope decisions. This page updates automatically.'],
      signed_off: ['Working papers signed off', 'Your signoff is recorded. The complete review package is ready to download.'],
      returned: ['Returned for revision', 'Your return decision is recorded. This review is paused. A connected model is required to revise the analysis and plan.'],
      requires_model: ['No risks remain in scope', 'All proposed risks were excluded. Start a new assessment to propose a different scope.'],
      failed: ['The review could not finish', 'Review the error below. You can start a new review from the navigation.']
    };
    const text = texts[run.status];
    if (!text) return null;
    const signature = run.signoff;
    return el('section', { class: `panel state-panel${run.status === 'failed' ? ' error-state' : ['returned', 'requires_model'].includes(run.status) ? ' waiting-state' : ''}` },
      el('h2', {}, text[0]), el('p', {}, text[1]), run.error ? el('p', { class: 'notice error' }, run.error) : null,
      signature ? el('div', { class: 'terminal-signature' }, `Recorded by ${readable(signature.reviewer)} · ${readable(signature.date)}`, signature.comment ? el('p', {}, signature.comment) : null) : null,
      run.status === 'signed_off' ? el('a', { class: 'button', href: `/api/runs/${encodeURIComponent(run.id)}/download`, download: '' }, 'Download signed-off package (.zip)') : null);
  }
  function eventsPanel(run) {
    if (!run.events?.length) return null;
    return el('details', {}, el('summary', {}, 'Review activity'), el('div', { class: 'panel details-body' },
      el('ol', { class: 'event-list' }, run.events.map(event => el('li', {}, el('time', { datetime: event.at }, time(event.at)), el('span', {}, event.label))))));
  }
  function preservedDraft(run) {
    if (!staleDraft) return null;
    const draft = getDraft(run.id);
    return el('details', {}, el('summary', {}, 'Your preserved unsent entries'), el('div', { class: 'panel details-body' },
      el('p', { class: 'muted' }, 'These entries were kept after the review changed. They have not been submitted.'),
      draft.scope.reviewer || draft.scope.date || Object.values(draft.scope.decisions).some(item => item.decision) ? el('div', {},
        el('h3', {}, 'Scope decision draft'), el('p', {}, [draft.scope.reviewer, draft.scope.date].filter(Boolean).join(' · ') || 'Reviewer and date not entered'),
        el('ul', { class: 'decision-list' }, Object.values(draft.scope.decisions).filter(item => item.decision || item.comment).map(item =>
          el('li', {}, `${item.id} · ${item.decision ? label(item.decision) : 'No decision selected'} · ${item.in_scope ? 'In scope' : 'Excluded from scope'}`, item.comment ? el('p', {}, item.comment) : null)))) : null,
      draft.signoff.reviewer || draft.signoff.date || draft.signoff.comment ? el('div', {}, el('h3', {}, 'Final decision draft'),
        el('p', {}, [draft.signoff.reviewer, draft.signoff.date, draft.signoff.decision === 'return' ? 'Return for revision' : 'Sign off'].filter(Boolean).join(' · ')),
        draft.signoff.comment ? el('p', {}, draft.signoff.comment) : null) : null));
  }
  function renderRun(run) {
    currentRun = run;
    provenance(run.mode);
    document.title = `${run.title || 'Procurement review'} · Working papers`;
    const sections = [el('div', { class: 'page-heading' }, el('div', {}, el('div', { class: 'run-meta' }, `REVIEW ${run.id} · Updated ${time(run.updated_at)}`), el('h1', {}, run.title || 'Procurement review')), status(run)),
      workflow(run), metrics(run), statePanel(run),
      ...(run.status === 'awaiting_scope' ? [renderScope(run), artifactsPanel(run), qaPanel(run), figurePanel(run)] :
        [artifactsPanel(run), qaPanel(run), figurePanel(run), decisionsPanel(run), run.status === 'awaiting_signoff' ? signoffPanel(run) : null]),
      preservedDraft(run), eventsPanel(run)];
    content.replaceChildren(...sections.filter(Boolean));
    schedulePoll(run);
  }
  function schedulePoll(run) {
    clearTimeout(pollTimer);
    if (['queued', 'analysing', 'planning'].includes(run.status)) pollTimer = setTimeout(refreshRun, 1800);
  }
  async function refreshRun() {
    try {
      const run = await api(`/api/runs/${encodeURIComponent(runId)}`);
      const changed = !currentRun || run.version !== currentRun.version || run.status !== currentRun.status;
      if (changed) { renderRun(run); await loadHistory(); }
      else schedulePoll(run);
    } catch (error) {
      showNotice(`Automatic refresh stopped. ${error.message} Reload the page to try again.`, true);
    }
  }
  async function mutate(run, path, payload, form) {
    requestPending = true;
    const controls = [...form.querySelectorAll('button, input, textarea, select')];
    const disabled = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    form.setAttribute('aria-busy', 'true'); clearNotice();
    try {
      const updated = await api(path, { method: 'POST', body: JSON.stringify(payload) });
      staleDraft = false;
      renderRun(updated);
      await loadHistory();
    } catch (error) {
      if (error.status === 409) {
        staleDraft = true;
        try { renderRun(await api(`/api/runs/${encodeURIComponent(run.id)}`)); }
        catch { /* Keep the displayed form and its entries if refresh also fails. */ }
        showNotice(`${error.message} Your unsent entries are preserved. Review the current state and confirm again if this step is still available. No decision was submitted.`, true);
      } else showNotice(error.message, true);
    } finally {
      requestPending = false;
      controls.forEach((control, index) => { control.disabled = disabled[index]; });
      form.removeAttribute('aria-busy');
    }
  }
  async function init() {
    await loadHistory();
    try {
      const config = await loadSources();
      if (runId) renderRun(await api(`/api/runs/${encodeURIComponent(runId)}`));
      else renderHome(config);
    } catch (error) {
      content.replaceChildren(panel('Working papers are unavailable', el('p', {}, error.message), el('button', { class: 'button secondary', type: 'button', onclick: () => location.reload() }, 'Reload page')));
    }
  }
  init();
})();
