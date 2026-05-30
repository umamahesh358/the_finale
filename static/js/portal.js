/* =============================================
   CIET PORTAL — MAIN JAVASCRIPT v2.0
   Full drawer + toast system for all pages
   ============================================= */

'use strict';

/* ─────────────────────────────────────
   SIDEBAR TOGGLE (Mobile)
───────────────────────────────────── */
function initSidebar() {
  const hamburger = document.getElementById('hamburger');
  const sidebar   = document.querySelector('.sidebar');
  const overlay   = document.getElementById('sidebar-overlay');
  if (!hamburger) return;
  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
  });
  if (overlay) overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
}

/* ─────────────────────────────────────
   TAB SWITCHING
───────────────────────────────────── */
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      const parent = btn.closest('[data-tabs-parent]') || document;
      parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      parent.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const pane = parent.querySelector(`#${target}`);
      if (pane) pane.classList.add('active');
    });
  });
}

/* ─────────────────────────────────────
   FLIP CARDS
───────────────────────────────────── */
function initFlipCards() {
  document.querySelectorAll('.flip-card').forEach(card => {
    card.addEventListener('click', () => card.classList.toggle('flipped'));
  });
}

/* ─────────────────────────────────────
   ACTIVE NAV LINK
───────────────────────────────────── */
function setActiveNav() {
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-item').forEach(item => {
    const href     = item.getAttribute('href') || '';
    const hrefPage = href.split('/').pop();
    const target   = item.dataset.page || hrefPage;
    if (target && target === page) item.classList.add('active');
  });
}

/* ─────────────────────────────────────
   ANIMATE PROGRESS BARS
───────────────────────────────────── */
function animateBars() {
  document.querySelectorAll('[data-width]').forEach(bar => {
    setTimeout(() => { bar.style.width = bar.dataset.width; }, 200);
  });
}

/* ─────────────────────────────────────
   TOAST NOTIFICATIONS
───────────────────────────────────── */
function showToast(msg, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;';
    document.body.appendChild(container);
  }
  const colors = { success:'#16a34a', error:'#dc2626', info:'#0891b2', warn:'#d97706' };
  const icons  = { success:'✓', error:'✕', info:'ℹ', warn:'⚠' };
  const toast  = document.createElement('div');
  toast.style.cssText = `
    background:#fff;border:1px solid #e2e8f0;border-left:4px solid ${colors[type]||colors.info};
    border-radius:10px;padding:12px 16px;font-size:13px;font-weight:500;color:#0f172a;
    box-shadow:0 4px 20px rgba(0,0,0,.12);max-width:320px;pointer-events:auto;
    display:flex;align-items:center;gap:10px;
    animation:slideInRight .25s ease;
  `;
  toast.innerHTML = `<span style="color:${colors[type]};font-weight:700;">${icons[type]}</span>${msg}`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity='0'; toast.style.transition='opacity .3s'; setTimeout(() => toast.remove(), 300); }, 3200);
}

/* ─────────────────────────────────────
   DRAWER SYSTEM
───────────────────────────────────── */
function initDrawer() {
  if (document.getElementById('portal-drawer')) return;
  document.body.insertAdjacentHTML('beforeend', `
    <div id="drawer-backdrop" style="display:none;position:fixed;inset:0;background:rgba(15,23,42,0.4);z-index:400;backdrop-filter:blur(3px);transition:opacity .25s;"></div>
    <div id="portal-drawer" style="display:none;position:fixed;top:0;right:0;height:100%;width:100%;max-width:440px;background:#fff;z-index:500;box-shadow:-8px 0 48px rgba(0,0,0,.14);overflow-y:auto;transition:transform .3s cubic-bezier(.4,0,.2,1);transform:translateX(100%);font-family:'Inter',sans-serif;">
      <div id="drawer-header" style="padding:24px 28px 20px;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:#fff;z-index:1;">
        <div>
          <h2 id="drawer-title" style="font-size:16px;font-weight:700;color:#0f172a;margin:0;"></h2>
          <p id="drawer-subtitle" style="font-size:12px;color:#64748b;margin:4px 0 0;"></p>
        </div>
        <button id="drawer-close" style="width:34px;height:34px;border-radius:8px;background:#f8fafc;border:1px solid #e2e8f0;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:16px;flex-shrink:0;transition:background .15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#f8fafc'">✕</button>
      </div>
      <div id="drawer-body" style="padding:24px 28px 32px;"></div>
    </div>
  `);
  document.getElementById('drawer-close').addEventListener('click', closeDrawer);
  document.getElementById('drawer-backdrop').addEventListener('click', closeDrawer);
}

function openDrawer(title, subtitle, bodyHTML, onSave = null) {
  const drawer   = document.getElementById('portal-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  document.getElementById('drawer-title').textContent    = title;
  document.getElementById('drawer-subtitle').textContent = subtitle || '';
  document.getElementById('drawer-body').innerHTML       = bodyHTML;
  backdrop.style.display = 'block';
  drawer.style.display   = 'block';
  requestAnimationFrame(() => {
    backdrop.style.opacity = '1';
    drawer.style.transform = 'translateX(0)';
  });
  drawer.querySelectorAll('.dropzone-area').forEach(dz => initDropzone(dz));

  const saveBtn = document.getElementById('drawer-save-btn');
  if (saveBtn) {
    saveBtn.onclick = () => {
      let close = true;
      if (onSave) { close = onSave() !== false; }
      if (close) {
        showToast(saveBtn.getAttribute('data-toast'), saveBtn.getAttribute('data-toast-type'));
        closeDrawer();
      }
    };
  }
}

function closeDrawer() {
  const drawer   = document.getElementById('portal-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  if (!drawer) return;
  drawer.style.transform = 'translateX(100%)';
  backdrop.style.opacity = '0';
  setTimeout(() => {
    drawer.style.display   = 'none';
    backdrop.style.display = 'none';
  }, 300);
}

/* ─────────────────────────────────────
   FILE DROPZONE HELPER
───────────────────────────────────── */
function initDropzone(dz) {
  if (!dz || dz.dataset.initialized) return;
  dz.dataset.initialized = '1';
  const input  = dz.querySelector('input[type="file"]');
  const label  = dz.querySelector('.dz-label');
  const preview = dz.querySelector('.dz-preview');

  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dz-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dz-over'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('dz-over');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0], preview, label);
  });
  dz.addEventListener('click', () => input && input.click());
  if (input) input.addEventListener('change', () => {
    if (input.files[0]) handleFile(input.files[0], preview, label);
  });
}

function handleFile(file, preview, label) {
  if (!file) return;
  if (label) label.textContent = file.name;
  if (!preview) return;
  const isImage = file.type.startsWith('image/');
  if (isImage) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.innerHTML = `<img src="${e.target.result}" style="width:100%;max-height:160px;object-fit:contain;border-radius:8px;margin-top:8px;">`;
    };
    reader.readAsDataURL(file);
  } else {
    preview.innerHTML = `<div style="margin-top:8px;padding:10px 14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;font-size:12px;color:#15803d;">✓ ${file.name} (${(file.size/1024).toFixed(1)} KB) ready to upload</div>`;
  }
}

/* ─────────────────────────────────────
   SHARED DRAWER HELPERS
───────────────────────────────────── */
function field(label, inputHTML) {
  return `<div class="df-group"><label class="df-label">${label}</label>${inputHTML}</div>`;
}
function textInput(placeholder, value='') {
  return `<input type="text" class="df-input" placeholder="${placeholder}" value="${value}">`;
}
function dateInput(value='') {
  return `<input type="date" class="df-input" value="${value}">`;
}
function textarea(placeholder, value='', rows=4) {
  return `<textarea class="df-input df-textarea" placeholder="${placeholder}" rows="${rows}">${value}</textarea>`;
}
function select(options, value='') {
  const opts = options.map(([v,l]) => `<option value="${v}"${v===value?' selected':''}>${l}</option>`).join('');
  return `<select class="df-input df-select"><option value="" disabled${!value?' selected':''}>Choose...</option>${opts}</select>`;
}
function dropzone(label='Drop certificate image / PDF here, or click to browse', accept='image/*,.pdf') {
  return `
    <div class="dropzone-area" style="border:2px dashed #cbd5e1;border-radius:10px;padding:28px;text-align:center;cursor:pointer;transition:border-color .2s,background .2s;position:relative;">
      <input type="file" accept="${accept}" style="display:none;">
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" style="margin-bottom:10px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      <p class="dz-label" style="font-size:13px;color:#64748b;margin:0;">${label}</p>
      <p style="font-size:11px;color:#94a3b8;margin:6px 0 0;">PNG, JPG, PDF · Max 5 MB</p>
      <div class="dz-preview"></div>
    </div>`;
}
function drawerFooter(saveTxt='Save', toast='Saved successfully!', toastType='success') {
  return `
    <div style="display:flex;gap:10px;margin-top:24px;padding-top:20px;border-top:1px solid #e2e8f0;">
      <button onclick="closeDrawer()" class="df-btn-outline" style="flex:1;">Cancel</button>
      <button id="drawer-save-btn" data-toast="${toast}" data-toast-type="${toastType}" class="df-btn-primary" style="flex:1;">${saveTxt}</button>
    </div>`;
}

const PortalStore = {
  data: { internships: [], education: [], projects: [], publications: [], certifications: [] },
  load() {
    const stored = localStorage.getItem('ciet_portal_data');
    if (stored) { try { this.data = JSON.parse(stored); } catch(e){} }
  },
  save() { localStorage.setItem('ciet_portal_data', JSON.stringify(this.data)); if (typeof renderDashboard === 'function') renderDashboard(); },
  add(type, item) {
    item.id = Date.now().toString();
    this.data[type].unshift(item);
    this.save();
    return item;
  },
  remove(type, id) {
    this.data[type] = this.data[type].filter(i => i.id !== id);
    this.save();
  },
  init() {
    this.load();
    const page = location.pathname.split('/').pop() || 'index.html';
    if (page === 'internships.html') {
      const infoBanner = document.querySelector('.info-banner');
      const main = document.querySelector('.main-content');
      this.data.internships.forEach(item => {
        const card = createInternshipCard(item);
        if (infoBanner) infoBanner.insertAdjacentElement('afterend', card);
        else if (main) main.insertBefore(card, main.children[1]);
      });
    } else if (page === 'projects.html') {
      const grid = document.querySelector('.projects-grid');
      if (grid) this.data.projects.forEach(item => grid.insertBefore(createProjectCard(item), grid.firstChild));
    } else if (page === 'certifications.html') {
      const grid = document.querySelector('.certs-grid');
      if (grid) this.data.certifications.forEach(item => grid.insertBefore(createCertCard(item), grid.firstChild));
    } else if (page === 'education.html') {
      const timeline = document.querySelector('.timeline');
      if (timeline) this.data.education.forEach(item => timeline.insertBefore(createEduCard(item), timeline.firstChild));
    } else if (page === 'research.html') {
      const twoCol = document.querySelector('.two-col-grid');
      if (twoCol) this.data.publications.forEach(item => twoCol.insertAdjacentElement('afterend', createResearchCard(item)));
    }
  }
};

function createInternshipCard(item) {
  const card = document.createElement('div'); card.className = 'intern-card'; card.dataset.id = item.id; card.dataset.type = 'internships';
  card.innerHTML = `<div class="intern-header"><div class="intern-left"><div class="company-icon">${item.company.charAt(0).toUpperCase()}</div><div><div class="intern-title">${item.role}</div><div class="intern-company">${item.company}</div><div class="intern-meta">${item.location}</div></div></div><span class="tag tag-green"><span class="status-dot"></span>Current</span></div><div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:6px;">${item.skills.map(s => '<span class="tag tag-primary">'+s+'</span>').join('')}</div><div style="margin-top:16px;display:flex;gap:8px;border-top:1px solid var(--border);padding-top:12px;"><button class="btn-ghost" data-action="edit">Edit</button><button class="btn-ghost" style="color:#dc2626;" data-action="delete">Delete</button></div>`; return card;
}
function createProjectCard(item) {
  const card = document.createElement('div'); card.className = 'project-card'; card.dataset.id = item.id; card.dataset.type = 'projects';
  card.innerHTML = `<div class="project-header"><div class="project-name">${item.title}</div></div><p class="project-desc">${item.desc}</p><div class="project-stack">${item.skills.map(s => '<span class="tag tag-primary">'+s+'</span>').join('')}</div><div style="margin-top:12px;display:flex;gap:8px;border-top:1px solid var(--border);padding-top:10px;"><button class="btn-ghost" style="flex:1;justify-content:center;font-size:12px;padding:6px;" data-action="edit">Edit</button><button class="btn-ghost" style="flex:1;justify-content:center;font-size:12px;padding:6px;color:#dc2626;" data-action="delete">Delete</button></div>`; return card;
}
function createCertCard(item) {
  const card = document.createElement('div'); card.className = 'flip-card'; card.title = 'Click to flip'; card.dataset.id = item.id; card.dataset.type = 'certifications';
  card.innerHTML = `<div class="flip-inner"><div class="flip-front"><div class="cert-front-icon" ${item.img ? 'style="background:url('+item.img+') center/contain no-repeat #fff;"' : ''}>${!item.img ? '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>' : ''}</div><div class="cert-name">${item.title}</div><div class="cert-org">${item.org}</div></div><div class="flip-back" style="background:#1e293b;"><div class="cert-detail-label">Certification</div><div class="cert-detail-val">${item.title}</div><div style="margin-top:auto;display:flex;gap:8px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.2);"><button class="btn-ghost" style="flex:1;color:#fff;border-color:rgba(255,255,255,0.4);" data-action="edit">Edit</button><button class="btn-ghost" style="flex:1;color:#fca5a5;border-color:rgba(255,255,255,0.4);" data-action="delete">Delete</button></div></div></div>`;
  card.addEventListener('click', (e) => { if(!e.target.closest('button')) card.classList.toggle('flipped'); }); return card;
}
function createEduCard(item) {
  const card = document.createElement('div'); card.className = 'edu-card'; card.dataset.id = item.id; card.dataset.type = 'education';
  card.innerHTML = `<div class="edu-icon"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0v6m0-6V8m0 6l9-5-9-5-9 5 9 5zm0-6V2"/></svg></div><div class="edu-body"><div class="edu-degree">${item.level} in ${item.stream}</div><div class="edu-inst">${item.institution}</div><div class="edu-meta"><span class="edu-chip">${item.start} - ${item.end}</span></div><div style="margin-top:12px;display:flex;gap:8px;border-top:1px solid var(--border);padding-top:12px;"><button class="btn-ghost" data-action="edit">Edit</button><button class="btn-ghost" style="color:#dc2626;" data-action="delete">Delete</button></div></div><div class="edu-badge">${item.grade}</div>`; return card;
}
function createResearchCard(item) {
  const card = document.createElement('div'); card.className = 'research-card'; card.dataset.id = item.id; card.dataset.type = 'publications';
  card.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;"><span class="research-type">${item.type}</span><span class="tag tag-green">${item.status}</span></div><div class="research-title">${item.title}</div><div class="research-abstract">${item.abstract}</div><div class="research-meta"><span>Co-Authors: <strong>${item.authors}</strong></span><span>Venue: <strong>${item.venue}</strong></span></div><div style="margin-top:14px;display:flex;gap:8px;"><button class="btn-ghost" style="flex:1;border-color:var(--border);" data-action="edit">Edit</button><button class="btn-ghost" style="flex:1;color:var(--danger);border-color:var(--border);" data-action="delete">Delete</button></div>`; return card;
}

/* ─────────────────────────────────────
   DRAWER DEFINITIONS (per page / button)
───────────────────────────────────── */
const DRAWERS = {

  'add-internship': () => openDrawer('Log a New Internship', 'Your real-world impact builds your career story.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Role / Title *', textInput('e.g. Frontend Developer Intern'))}
      ${field('Company / Organisation *', textInput('e.g. Google India'))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Type', select([['internship','Internship'],['contract','Contract'],['part-time','Part-time'],['remote','Remote Internship']]))}
        ${field('Location', textInput('e.g. Hyderabad (Hybrid)'))}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Start Date', dateInput())}
        ${field('End Date <span style="color:#94a3b8;font-weight:400;">(leave blank if current)</span>', dateInput())}
      </div>
      ${field('Key Contributions', textarea('• Developed a REST API that reduced latency by 20%\n• Collaborated in an Agile team of 6', '', 5))}
      ${field('Skills Applied <span style="color:#94a3b8;font-weight:400;">(comma-separated)</span>', textInput('e.g. React, Node.js, Agile'))}
      ${field('Stipend <span style="color:#94a3b8;font-weight:400;">(optional)</span>', textInput('e.g. ₹15,000 / month'))}
      ${drawerFooter('+ Add Internship', 'Internship added to your timeline!')}
    </div>`, () => {
    const inputs = document.querySelectorAll('#drawer-body .df-input');
    const item = {
      role: inputs[0].value || 'New Role',
      company: inputs[1].value || 'New Company',
      location: inputs[3].value || 'Remote',
      skills: inputs[7] ? inputs[7].value.split(',').map(s => s.trim()).filter(s => s) : []
    };
    PortalStore.add('internships', item);
    const card = createInternshipCard(item);
    const main = document.querySelector('.main-content');
    const infoBanner = main ? main.querySelector('.info-banner') : null;
    if (infoBanner) infoBanner.insertAdjacentElement('afterend', card);
    else if (main) main.insertBefore(card, main.children[1]);
}),

  'add-education': () => openDrawer('Add Academic Record', 'Build a complete picture of your academic journey.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Level *', select([['ug','B.Tech / UG'],['pg','M.Tech / PG'],['inter','Intermediate (12th)'],['ssc','10th / SSC'],['cert','Diploma / Certificate']]))}
      ${field('Institution Name *', textInput('e.g. Chalapathi Institute of Engineering and Technology'))}
      ${field('Board / University', textInput('e.g. JNTUA, CBSE, State Board'))}
      ${field('Field of Study / Stream', textInput('e.g. Computer Science & Engineering'))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Start Year', textInput('e.g. 2022'))}
        ${field('End Year / Expected', textInput('e.g. 2026'))}
      </div>
      <div>
        <label class="df-label">Grading System</label>
        <div style="display:flex;gap:16px;margin-top:8px;">
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer;"><input type="radio" name="grade-type" value="cgpa" checked onchange="document.getElementById('grade-input').placeholder='e.g. 9.2'"> CGPA</label>
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer;"><input type="radio" name="grade-type" value="pct" onchange="document.getElementById('grade-input').placeholder='e.g. 94%'"> Percentage</label>
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer;"><input type="radio" name="grade-type" value="rank" onchange="document.getElementById('grade-input').placeholder='e.g. 3 (out of 62)'"> Rank</label>
        </div>
      </div>
      ${field('Score / Grade', `<input type="text" id="grade-input" class="df-input" placeholder="e.g. 9.2">`)}
      ${drawerFooter('+ Add Record', 'Academic record added!')}
    </div>`, () => { const inputs = document.querySelectorAll('#drawer-body .df-input'); const item = { level: inputs[0].value || 'Degree', institution: inputs[1].value || 'Institution', stream: inputs[3].value || 'Stream', start: inputs[4].value || '2022', end: inputs[5].value || '2026', grade: document.querySelector('#grade-input').value || 'A' }; PortalStore.add('education', item); const card = createEduCard(item); const timeline = document.querySelector('.timeline'); if (timeline) timeline.insertBefore(card, timeline.firstChild); }),

  'deploy-project': () => openDrawer('Deploy a New Project', 'Your engineering proof-of-work. Build, deploy, impress.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Project Title *', textInput('e.g. Smart Traffic Management System'))}
      ${field('Description *', textarea('What does this project do? What problem does it solve?', '', 4))}
      ${field('Status', select([['in-progress','In Progress'],['completed','Completed / Deployed'],['archived','Archived']]))}
      ${field('Tech Stack <span style="color:#94a3b8;font-weight:400;">(comma-separated)</span>', textInput('e.g. React, Node.js, MongoDB, AWS'))}
      ${field('GitHub Repository URL', textInput('https://github.com/username/repo'))}
      ${field('Live Demo URL <span style="color:#94a3b8;font-weight:400;">(optional)</span>', textInput('https://your-app.vercel.app'))}
      ${field('Key Features / Highlights', textarea('• Reduced latency by 30%\n• Supports 10K concurrent users', '', 3))}
      ${drawerFooter('🚀 Deploy Project', 'Project deployed to your portfolio!')}
    </div>`, () => {
    const inputs = document.querySelectorAll('#drawer-body .df-input');
    const item = { title: inputs[0].value || 'New Project', desc: (inputs[1].value || 'Project description.').substring(0, 100), skills: inputs[3].value.split(',').map(s=>s.trim()).filter(s=>s) }; PortalStore.add('projects', item); const card = createProjectCard(item); const grid = document.querySelector('.projects-grid'); if (grid) grid.insertBefore(card, grid.firstChild); }),

  'add-publication': () => openDrawer('Add Research / Publication', 'Academic rigor that impresses R&D recruiters.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Publication Type', select([['journal','Journal Article'],['conference','Conference Paper'],['thesis','Thesis / Dissertation'],['whitepaper','Whitepaper'],['patent','Patent']]))}
      ${field('Status', select([['published','Published'],['ongoing','Ongoing / In Progress'],['submitted','Submitted'],['under-review','Under Review'],['accepted','Accepted']]))}
      ${field('Title *', textInput('e.g. Federated Learning for Privacy-Preserving Healthcare Analytics'))}
      ${field('Co-Authors <span style="color:#94a3b8;font-weight:400;">(comma-separated)</span>', textInput('e.g. Dr. A. Sharma, Jane Doe'))}
      ${field('Venue / Conference / Journal', textInput('e.g. IEEE Transactions on Neural Networks, 2026'))}
      ${field('Publication Date', dateInput())}
      ${field('Abstract / Summary', textarea('Brief summary of the research, methodology, and outcomes...', '', 5))}
      ${field('DOI / URL <span style="color:#94a3b8;font-weight:400;">(optional)</span>', textInput('https://doi.org/...'))}
      ${drawerFooter('+ Add Publication', 'Research publication added!')}
    </div>`, () => { const inputs = document.querySelectorAll('#drawer-body .df-input'); const item = { type: inputs[0].value || 'Publication', status: inputs[1].value || 'Published', title: inputs[2].value || 'Title', authors: inputs[3].value || 'Authors', venue: inputs[4].value || 'Venue', abstract: inputs[6].value || 'Abstract' }; PortalStore.add('publications', item); const card = createResearchCard(item); const twoCol = document.querySelector('.two-col-grid'); if (twoCol) twoCol.insertAdjacentElement('afterend', card); }),

  'add-certification': () => openDrawer('Add New Certification', 'Verified credentials that set you apart.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Certificate Title *', textInput('e.g. AWS Certified Cloud Practitioner'))}
      ${field('Issuing Organisation *', textInput('e.g. Amazon Web Services'))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Issue Date', dateInput())}
        ${field('Expiry Date <span style="color:#94a3b8;font-weight:400;">(optional)</span>', dateInput())}
      </div>
      ${field('Credential ID <span style="color:#94a3b8;font-weight:400;">(optional)</span>', textInput('e.g. AWS-CLF-12345'))}
      ${field('Credential / Verify URL', textInput('https://www.credly.com/badges/...'))}
      ${field('Skills Unlocked <span style="color:#94a3b8;font-weight:400;">(comma-separated)</span>', textInput('e.g. Cloud Computing, S3, EC2, IAM'))}
      <div>
        <label class="df-label">Certificate Image / PDF <span style="color:#94a3b8;font-weight:400;">(optional)</span></label>
        ${dropzone('Drop certificate image or PDF here, or click to browse', 'image/*,.pdf')}
      </div>
      ${drawerFooter('+ Add Certification', 'Certification added to your trophy case! 🏆')}
    </div>`, () => {
    const inputs = document.querySelectorAll('#drawer-body .df-input');
    const item = { title: inputs[0].value || 'New Certification', org: inputs[1].value || 'Issuing Org', img: document.querySelector('#drawer-body .dz-preview img')?.src || null }; PortalStore.add('certifications', item); const card = createCertCard(item); const grid = document.querySelector('.certs-grid'); if (grid) grid.insertBefore(card, grid.firstChild); }),

  'join-cohort': (name='') => openDrawer('Join a Cohort', 'Connect with peers who share your goals.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${name ? `<div style="padding:14px;background:#fdf2f5;border:1px solid rgba(175,12,62,0.15);border-radius:10px;font-size:13px;font-weight:600;color:#AF0C3E;">Joining: ${name}</div>` : ''}
      ${field('Search or Browse Cohorts', textInput('e.g. AI/ML Club, DevOps Crew...'))}
      <div style="font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin-top:4px;">Open Cohorts</div>
      ${['Full-Stack Builders', 'Startup Sprint', 'AI/ML Research Collective', 'Open Source Contributors', 'Campus Community Service'].map(c => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;gap:8px;">
          <div style="font-size:13px;font-weight:600;">${c}</div>
          <button onclick="showToast('Join request sent for ${c}!','success');" style="padding:6px 14px;background:#AF0C3E;color:#fff;border:none;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;">Join</button>
        </div>`).join('')}
      ${drawerFooter('Browse All Cohorts', 'Cohort joined! Welcome aboard 🎉')}
    </div>`),

  'edit-profile': () => openDrawer('Edit Profile', 'Customize how recruiters and peers see you.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      <div style="display:flex;align-items:center;gap:16px;padding:16px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
        <div style="width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#AF0C3E,#8F0830);color:#fff;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;flex-shrink:0;">J</div>
        <div style="flex:1;">
          <p style="font-size:13px;font-weight:600;color:#0f172a;margin:0 0 8px;">Profile Photo</p>
          ${dropzone('Click to upload a profile photo', 'image/*')}
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('First Name', textInput('e.g. John', 'John'))}
        ${field('Last Name', textInput('e.g. Student', 'Student'))}
      </div>
      ${field('Tagline / Bio', textarea('"Aspiring Full-Stack Developer passionate about building scalable products."', '"Aspiring Full-Stack Developer passionate about building scalable products."', 3))}
      ${field('Location', textInput('e.g. Hyderabad, Andhra Pradesh', 'Hyderabad, Andhra Pradesh'))}
      ${field('Skills <span style="color:#94a3b8;font-weight:400;">(comma-separated)</span>', textInput('e.g. React, Node.js, Python, Cloud', 'React, Node.js, Python, Cloud'))}
      ${field('LinkedIn URL', textInput('https://linkedin.com/in/...'))}
      ${field('GitHub URL', textInput('https://github.com/...'))}
      ${field('LeetCode URL', textInput('https://leetcode.com/u/...'))}
      ${drawerFooter('Save Profile', 'Profile updated successfully!')}
    </div>`),

  'add-event': () => openDrawer('Log Event / Achievement', 'Your extracurriculars prove leadership to recruiters.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Event Name *', textInput('e.g. Smart India Hackathon 2024'))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Scope', select([['campus','Campus'],['national','National'],['international','International'],['online','Online']]))}
        ${field('Role', select([['participant','Participant'],['winner','Winner'],['organizer','Organizer'],['volunteer','Volunteer'],['speaker','Speaker'],['mentor','Mentor']]))}
      </div>
      ${field('Position / Achievement <span style="color:#94a3b8;font-weight:400;">(optional)</span>', textInput('e.g. 1st Place, Best UI Award, Finalist'))}
      ${field('Organizer / Body', textInput('e.g. IEEE, CSE Department, Ministry of Education'))}
      ${field('Location / Mode', textInput('e.g. Main Auditorium / Online'))}
      ${field('Event Date', dateInput())}
      ${field('Certificate / Proof Image', dropzone('Click to upload certificate or proof image', 'image/*,.pdf'))}
      ${drawerFooter('+ Log Event', 'Event added to your portfolio!')}
    </div>`),

  'edit-internship': (title='', company='') => openDrawer(`Edit: ${title}`, `${company}`, `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Role / Title', textInput('', title))}
      ${field('Company', textInput('', company))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Start Date', dateInput())}
        ${field('End Date', dateInput())}
      </div>
      ${field('Location', textInput('e.g. Hyderabad (Hybrid)'))}
      ${field('Key Contributions', textarea('', '', 5))}
      ${field('Skills Applied', textInput('e.g. React, Node.js, Agile'))}
      <div style="display:flex;gap:10px;margin-top:24px;padding-top:20px;border-top:1px solid #e2e8f0;">
        <button onclick="showToast('Internship deleted.','error');closeDrawer();" style="padding:9px 16px;background:#fef2f2;border:1.5px solid #fecaca;border-radius:8px;font-size:13px;font-weight:600;color:#dc2626;cursor:pointer;">Delete</button>
        <button onclick="closeDrawer()" class="df-btn-outline" style="flex:1;">Cancel</button>
        <button onclick="showToast('Internship updated!','success');closeDrawer();" class="df-btn-primary" style="flex:1;">Save Changes</button>
      </div>
    </div>`),
  'view-cohort': (name, desc) => openDrawer(`Cohort: ${name}`, 'Group Hub — Materials & Reference Links', `
    <div style="display:flex;flex-direction:column;gap:0;">
      <div style="display:flex;gap:0;border-bottom:1px solid #e2e8f0;margin-bottom:18px;">
        <button onclick="document.querySelectorAll('.ch-tab').forEach(t=>t.classList.remove('ch-active'));this.classList.add('ch-active');document.querySelectorAll('.ch-pane').forEach(p=>p.style.display='none');document.getElementById('ch-overview').style.display='block';" class="ch-tab ch-active" style="padding:10px 16px;font-size:12px;font-weight:700;background:none;border:none;border-bottom:2px solid #AF0C3E;color:#AF0C3E;cursor:pointer;">Overview</button>
        <button onclick="document.querySelectorAll('.ch-tab').forEach(t=>t.classList.remove('ch-active'));this.classList.add('ch-active');document.querySelectorAll('.ch-pane').forEach(p=>p.style.display='none');document.getElementById('ch-materials').style.display='block';" class="ch-tab" style="padding:10px 16px;font-size:12px;font-weight:700;background:none;border:none;border-bottom:2px solid transparent;color:#64748b;cursor:pointer;">Materials & Links</button>
      </div>
      
      <div id="ch-overview" class="ch-pane">
        <div style="font-size:13px;color:#334155;background:#f8fafc;padding:14px;border-radius:8px;border:1px solid #e2e8f0;line-height:1.6;margin-bottom:14px;">${desc}</div>
        <button class="df-btn-primary" style="width:100%;margin-top:10px;" onclick="closeDrawer()">Close</button>
      </div>

      <div id="ch-materials" class="ch-pane" style="display:none;">
        <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px;">
          <h3 style="font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin:0 0 4px;">Uploaded Materials</h3>
          
          <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <div style="width:36px;height:36px;border-radius:8px;background:rgba(220,38,38,0.1);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:#dc2626;flex-shrink:0;">PDF</div>
            <div style="flex:1;"><div style="font-size:13px;font-weight:600;">project-brief.pdf</div><div style="font-size:11px;color:#94a3b8;">245 KB</div></div>
            <button onclick="showToast('Downloading...','info');" style="padding:5px 10px;font-size:11px;font-weight:600;background:#fff;border:1px solid #e2e8f0;border-radius:6px;cursor:pointer;">Download</button>
          </div>
          <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <div style="width:36px;height:36px;border-radius:8px;background:rgba(37,99,235,0.1);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:#2563eb;flex-shrink:0;">DOC</div>
            <div style="flex:1;"><div style="font-size:13px;font-weight:600;">api-design-doc.docx</div><div style="font-size:11px;color:#94a3b8;">88 KB</div></div>
            <button onclick="showToast('Downloading...','info');" style="padding:5px 10px;font-size:11px;font-weight:600;background:#fff;border:1px solid #e2e8f0;border-radius:6px;cursor:pointer;">Download</button>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          <h3 style="font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin:0 0 4px;">Reference Links</h3>

          <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;">
            <div style="width:36px;height:36px;border-radius:8px;background:rgba(22,163,74,0.1);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:#16a34a;flex-shrink:0;">LINK</div>
            <div style="flex:1;"><div style="font-size:13px;font-weight:600;">React Documentation</div><div style="font-size:11px;color:#64748b;">react.dev/learn</div></div>
            <button onclick="window.open('https://react.dev/learn', '_blank');" style="padding:5px 10px;font-size:11px;font-weight:600;background:#fff;border:1px solid #16a34a;color:#16a34a;border-radius:6px;cursor:pointer;">Open</button>
          </div>
          <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;">
            <div style="width:36px;height:36px;border-radius:8px;background:rgba(22,163,74,0.1);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:#16a34a;flex-shrink:0;">LINK</div>
            <div style="flex:1;"><div style="font-size:13px;font-weight:600;">Node.js Best Practices</div><div style="font-size:11px;color:#64748b;">github.com/goldbergyoni...</div></div>
            <button onclick="window.open('https://github.com/goldbergyoni/nodebestpractices', '_blank');" style="padding:5px 10px;font-size:11px;font-weight:600;background:#fff;border:1px solid #16a34a;color:#16a34a;border-radius:6px;cursor:pointer;">Open</button>
          </div>
        </div>
        <button class="df-btn-primary" style="width:100%;margin-top:24px;" onclick="closeDrawer()">Close</button>
      </div>
    </div>`),

  'edit-internship-full': (card) => {
    const role = card.querySelector('.intern-title')?.textContent || '';
    const company = card.querySelector('.intern-company')?.textContent || '';
    const loc = card.querySelector('.intern-meta')?.textContent || '';
    const skills = Array.from(card.querySelectorAll('.tag-primary')).map(t=>t.textContent).join(', ');
    openDrawer('Edit Internship', company, `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Role / Title *', textInput('e.g. Frontend Developer Intern', role))}
      ${field('Company / Organisation *', textInput('e.g. Google India', company))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Type', select([['internship','Internship'],['contract','Contract'],['part-time','Part-time'],['remote','Remote Internship']]))}
        ${field('Location', textInput('e.g. Hyderabad (Hybrid)', loc))}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Start Date', dateInput())}
        ${field('End Date', dateInput())}
      </div>
      ${field('Key Contributions', textarea('• Developed a REST API...', '', 4))}
      ${field('Skills Applied', textInput('e.g. React, Node.js', skills))}
      ${field('Stipend (optional)', textInput('e.g. ₹15,000 / month'))}
      ${drawerFooter('Save Changes', 'Internship updated!','success')}
    </div>`, () => {
      const inputs = document.querySelectorAll('#drawer-body .df-input');
      const newRole = inputs[0].value || role;
      const newComp = inputs[1].value || company;
      const newLoc  = inputs[3].value || loc;
      const newSkills = inputs[7].value.split(',').map(s=>s.trim()).filter(s=>s);
      if(card.querySelector('.intern-title'))   card.querySelector('.intern-title').textContent   = newRole;
      if(card.querySelector('.intern-company')) card.querySelector('.intern-company').textContent = newComp;
      if(card.querySelector('.intern-meta'))    card.querySelector('.intern-meta').textContent    = newLoc;
      const tagsDiv = card.querySelector('[style*="flex-wrap"]');
      if(tagsDiv) tagsDiv.innerHTML = newSkills.map(s=>`<span class="tag tag-primary">${s}</span>`).join('');
      if(card.dataset.id){const st=PortalStore.data.internships.find(i=>i.id===card.dataset.id);if(st){st.role=newRole;st.company=newComp;st.location=newLoc;st.skills=newSkills;PortalStore.save();}}
    });
  },

  'edit-project-full': (card) => {
    const title = card.querySelector('.project-name')?.textContent || '';
    const desc  = card.querySelector('.project-desc')?.textContent || '';
    const skills = Array.from(card.querySelectorAll('.project-stack .tag-primary')).map(t=>t.textContent).join(', ');
    openDrawer('Edit Project', title, `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Project Title *', textInput('e.g. Smart Traffic System', title))}
      ${field('Description *', textarea('What does this project do?', desc, 4))}
      ${field('Status', select([['in-progress','In Progress'],['completed','Completed / Deployed'],['archived','Archived']]))}
      ${field('Tech Stack (comma-separated)', textInput('e.g. React, Node.js, MongoDB', skills))}
      ${field('GitHub Repository URL', textInput('https://github.com/username/repo'))}
      ${field('Live Demo URL (optional)', textInput('https://your-app.vercel.app'))}
      ${field('Key Features / Highlights', textarea('• Feature 1\n• Feature 2', '', 3))}
      ${drawerFooter('Save Changes', 'Project updated!','success')}
    </div>`, () => {
      const inputs = document.querySelectorAll('#drawer-body .df-input');
      const newTitle  = inputs[0].value || title;
      const newDesc   = inputs[1].value || desc;
      const newSkills = inputs[3].value.split(',').map(s=>s.trim()).filter(s=>s);
      if(card.querySelector('.project-name')) card.querySelector('.project-name').textContent = newTitle;
      if(card.querySelector('.project-desc')) card.querySelector('.project-desc').textContent = newDesc;
      const tagsDiv = card.querySelector('.project-stack');
      if(tagsDiv) tagsDiv.innerHTML = newSkills.map(s=>`<span class="tag tag-primary">${s}</span>`).join('');
      if(card.dataset.id){const st=PortalStore.data.projects.find(i=>i.id===card.dataset.id);if(st){st.title=newTitle;st.desc=newDesc;st.skills=newSkills;PortalStore.save();}}
    });
  },

  'edit-cert-full': (card) => {
    const title = card.querySelector('.cert-name')?.textContent || '';
    const org   = card.querySelector('.cert-org')?.textContent  || '';
    openDrawer('Edit Certification', title, `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Certificate Title *', textInput('e.g. AWS Certified Cloud Practitioner', title))}
      ${field('Issuing Organisation *', textInput('e.g. Amazon Web Services', org))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Issue Date', dateInput())}
        ${field('Expiry Date (optional)', dateInput())}
      </div>
      ${field('Credential ID (optional)', textInput('e.g. AWS-CLF-12345'))}
      ${field('Credential / Verify URL', textInput('https://www.credly.com/badges/...'))}
      ${field('Skills Unlocked (comma-separated)', textInput('e.g. Cloud Computing, S3, EC2'))}
      <div>
        <label class="df-label">Certificate Image / PDF (optional)</label>
        ${dropzone('Drop new certificate image or PDF here', 'image/*,.pdf')}
      </div>
      ${drawerFooter('Save Changes', 'Certification updated!','success')}
    </div>`, () => {
      const inputs = document.querySelectorAll('#drawer-body .df-input');
      const newTitle = inputs[0].value || title;
      const newOrg   = inputs[1].value || org;
      const newImg   = document.querySelector('#drawer-body .dz-preview img')?.src || null;
      if(card.querySelector('.cert-name'))       card.querySelector('.cert-name').textContent       = newTitle;
      if(card.querySelector('.cert-detail-val')) card.querySelector('.cert-detail-val').textContent = newTitle;
      if(card.querySelector('.cert-org'))        card.querySelector('.cert-org').textContent        = newOrg;
      if(newImg){const icon=card.querySelector('.cert-front-icon');if(icon){icon.style.background=`url(${newImg}) center/contain no-repeat #fff`;icon.innerHTML='';}}
      if(card.dataset.id){const st=PortalStore.data.certifications.find(i=>i.id===card.dataset.id);if(st){st.title=newTitle;st.org=newOrg;if(newImg)st.img=newImg;PortalStore.save();}}
    });
  },

  'edit-edu-full': (card) => {
    const degree = card.querySelector('.edu-degree')?.textContent || '';
    const inst   = card.querySelector('.edu-inst')?.textContent   || '';
    const chip   = card.querySelector('.edu-chip')?.textContent   || '';
    const grade  = card.querySelector('.edu-badge')?.textContent  || '';
    const parts  = degree.split(' in ');
    const halves = chip.split(' - ');
    openDrawer('Edit Education', inst, `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Level *', select([['ug','B.Tech / UG'],['pg','M.Tech / PG'],['inter','Intermediate (12th)'],['ssc','10th / SSC'],['cert','Diploma / Certificate']], 'ug'))}
      ${field('Institution Name *', textInput('e.g. CIET', inst))}
      ${field('Board / University', textInput('e.g. JNTUA'))}
      ${field('Field of Study / Stream', textInput('e.g. Computer Science & Engineering', parts[1]||''))}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        ${field('Start Year', textInput('e.g. 2022', (halves[0]||'').trim()))}
        ${field('End Year / Expected', textInput('e.g. 2026', (halves[1]||'').trim()))}
      </div>
      ${field('Score / Grade', '<input type="text" class="df-input" id="grade-input" placeholder="e.g. 9.2" value="' + grade + '">')}
      ${drawerFooter('Save Changes', 'Education updated!','success')}
    </div>`, () => {
      const inputs = document.querySelectorAll('#drawer-body .df-input');
      const newInst   = inputs[1].value || inst;
      const newStream = inputs[3].value || (parts[1]||'');
      const newStart  = inputs[4].value || (halves[0]||'').trim();
      const newEnd    = inputs[5].value || (halves[1]||'').trim();
      const newGrade  = document.querySelector('#grade-input')?.value || grade;
      if(card.querySelector('.edu-degree')) card.querySelector('.edu-degree').textContent = (parts[0]||'Degree') + ' in ' + newStream;
      if(card.querySelector('.edu-inst'))   card.querySelector('.edu-inst').textContent   = newInst;
      if(card.querySelector('.edu-chip'))   card.querySelector('.edu-chip').textContent   = newStart + ' - ' + newEnd;
      if(card.querySelector('.edu-badge'))  card.querySelector('.edu-badge').textContent  = newGrade;
      if(card.dataset.id){const st=PortalStore.data.education.find(i=>i.id===card.dataset.id);if(st){st.institution=newInst;st.stream=newStream;st.start=newStart;st.end=newEnd;st.grade=newGrade;PortalStore.save();}}
    });
  },

  'edit-research-full': (card) => {
    const titleTxt = card.querySelector('.research-title')?.textContent    || '';
    const absTxt   = card.querySelector('.research-abstract')?.textContent || '';
    openDrawer('Edit Publication', titleTxt, `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Publication Type', select([['journal','Journal Article'],['conference','Conference Paper'],['thesis','Thesis'],['whitepaper','Whitepaper'],['patent','Patent']]))}
      ${field('Status', select([['published','Published'],['ongoing','Ongoing'],['submitted','Submitted'],['under-review','Under Review'],['accepted','Accepted']]))}
      ${field('Title *', textInput('Publication title', titleTxt))}
      ${field('Co-Authors (comma-separated)', textInput('e.g. Dr. A. Sharma'))}
      ${field('Venue / Conference / Journal', textInput('e.g. IEEE Transactions'))}
      ${field('Publication Date', dateInput())}
      ${field('Abstract / Summary', textarea('Brief summary...', absTxt, 5))}
      ${field('DOI / URL (optional)', textInput('https://doi.org/...'))}
      ${drawerFooter('Save Changes', 'Publication updated!','success')}
    </div>`, () => {
      const inputs   = document.querySelectorAll('#drawer-body .df-input');
      const newTitle = inputs[2].value || titleTxt;
      const newAbs   = inputs[6].value || absTxt;
      if(card.querySelector('.research-title'))    card.querySelector('.research-title').textContent    = newTitle;
      if(card.querySelector('.research-abstract')) card.querySelector('.research-abstract').textContent = newAbs;
      if(card.dataset.id){const st=PortalStore.data.publications.find(i=>i.id===card.dataset.id);if(st){st.title=newTitle;st.abstract=newAbs;PortalStore.save();}}
    });
  },

  'edit-about': (textEl) => openDrawer('Edit About Me', 'Update your personal bio.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Bio / About Me *', textarea('Write a compelling bio...', textEl ? textEl.textContent : '', 6))}
      ${field('Tagline', textInput('e.g. Aspiring Full-Stack Developer'))}
      ${field('Location', textInput('e.g. Hyderabad, Andhra Pradesh'))}
      ${drawerFooter('Save Changes', 'About Me updated!','success')}
    </div>`, () => {
      const inputs = document.querySelectorAll('#drawer-body .df-input');
      if(textEl) textEl.textContent = inputs[0].value || textEl.textContent;
    }),

  'edit-contact': (section) => openDrawer('Edit Contact & Links', 'Update your contact information and social links.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
      ${field('Email', textInput('your@email.com', 'john.student@ciet.ac.in'))}
      ${field('LinkedIn URL', textInput('https://linkedin.com/in/...', 'linkedin.com/in/john-student'))}
      ${field('GitHub URL', textInput('https://github.com/...', 'github.com/john-student'))}
      ${field('LeetCode / Portfolio URL', textInput('https://leetcode.com/u/...'))}
      ${field('Location', textInput('e.g. Hyderabad, Andhra Pradesh', 'Hyderabad, Andhra Pradesh'))}
      ${drawerFooter('Save Changes', 'Contact info updated!','success')}
    </div>`, () => {
      const inputs = document.querySelectorAll('#drawer-body .df-input');
      if(section) {
        const rows = section.querySelectorAll('div');
        const textNodes = [];
        rows.forEach(r => { if(r.children.length === 0 && r.textContent.trim()) textNodes.push(r); });
      }
    }),

  'generic-edit': (title, cardRef) => openDrawer(`Edit ${title}`, 'Update details.', `
    <div style="display:flex;flex-direction:column;gap:14px;">
       ${field('Name / Title', textInput('', title))}
       ${drawerFooter('Save Changes', 'Updated successfully!')}
    </div>`, () => {
        const newVal = document.querySelector('#drawer-body .df-input').value;
        if(cardRef.querySelector('.intern-title')) cardRef.querySelector('.intern-title').textContent = newVal;
        if(cardRef.querySelector('.project-name')) cardRef.querySelector('.project-name').textContent = newVal;
        if(cardRef.querySelector('.cert-name'))   cardRef.querySelector('.cert-name').textContent   = newVal;
    }),
};

/* ─────────────────────────────────────
   INJECT DRAWER COMPONENT CSS
───────────────────────────────────── */
function injectDrawerStyles() {
  if (document.getElementById('df-styles')) return;
  const s = document.createElement('style');
  s.id = 'df-styles';
  s.textContent = `
    @keyframes slideInRight { from{transform:translateX(24px);opacity:0} to{transform:translateX(0);opacity:1} }

    .df-group { display:flex;flex-direction:column;gap:5px; }
    .df-label { font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em; }
    .df-input {
      padding:9px 12px;border:1.5px solid #e2e8f0;border-radius:8px;
      font-size:13px;color:#0f172a;background:#fff;outline:none;
      transition:border-color .2s,box-shadow .2s;font-family:'Inter',sans-serif;width:100%;box-sizing:border-box;
    }
    .df-input:focus { border-color:#AF0C3E;box-shadow:0 0 0 3px rgba(175,12,62,.08); }
    .df-textarea { resize:vertical;min-height:80px; }
    .df-select { appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:32px;cursor:pointer; }

    .df-btn-primary {
      display:inline-flex;align-items:center;justify-content:center;gap:6px;
      padding:9px 16px;background:#AF0C3E;color:#fff;border:none;border-radius:8px;
      font-size:13px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;
      transition:background .15s,transform .1s;
    }
    .df-btn-primary:hover { background:#8F0830; }
    .df-btn-primary:active { transform:scale(.98); }

    .df-btn-outline {
      display:inline-flex;align-items:center;justify-content:center;gap:6px;
      padding:9px 16px;background:#fff;color:#0f172a;border:1.5px solid #e2e8f0;border-radius:8px;
      font-size:13px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;
      transition:border-color .15s;
    }
    .df-btn-outline:hover { border-color:#AF0C3E;color:#AF0C3E; }

    .dropzone-area:hover,.dropzone-area.dz-over {
      border-color:#AF0C3E !important;background:rgba(175,12,62,.03);
    }
    .dropzone-area.dz-over { transform:scale(.99); }
  `;
  document.head.appendChild(s);
}

/* ─────────────────────────────────────
   WIRE ALL BUTTONS PER PAGE
───────────────────────────────────── */
function wireButtons() {
  document.addEventListener('click', e => {
    const delBtn = e.target.closest('[data-action="delete"]');
    if (delBtn) {
      e.stopPropagation();
      const card = delBtn.closest('.intern-card, .project-card, .flip-card, .edu-card, .research-card'); if (card) { if (card.dataset.id && card.dataset.type) { PortalStore.remove(card.dataset.type, card.dataset.id); } card.remove(); showToast('Item deleted successfully.', 'info'); }
      return;
    }
    
    const editBtn = e.target.closest('[data-action="edit"]');
    if (editBtn) {
      e.stopPropagation();
      const card = editBtn.closest('.intern-card, .project-card, .flip-card, .edu-card, .research-card');
      if (card) {
        if (card.classList.contains('intern-card'))    { DRAWERS['edit-internship-full'](card); return; }
        if (card.classList.contains('project-card'))   { DRAWERS['edit-project-full'](card);    return; }
        if (card.classList.contains('flip-card'))      { DRAWERS['edit-cert-full'](card);       return; }
        if (card.classList.contains('edu-card'))       { DRAWERS['edit-edu-full'](card);        return; }
        if (card.classList.contains('research-card'))  { DRAWERS['edit-research-full'](card);   return; }
      }
      return;
    }
    
    const viewBtn = e.target.closest('[data-action="view-cohort"]');
    if (viewBtn) {
      e.stopPropagation();
      const card = viewBtn.closest('.cohort-card');
      const name = card.querySelector('.cohort-name').textContent;
      const desc = card.querySelector('.cohort-desc').textContent;
      DRAWERS['view-cohort'](name, desc);
      return;
    }
  });


  const page = location.pathname.split('/').pop() || 'index.html';

  // ── Dashboard (index.html) ──
  if (page === 'index.html') {
    // "Add Internship to boost" button inside the profile banner
    document.querySelectorAll('.btn-boost, [data-action="add-internship"]').forEach(btn => {
      btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-internship'](); });
    });
  }

  // ── Education ──
  if (page === 'education.html') {
    document.querySelectorAll('.btn-primary, [data-action="add-education"]').forEach(btn => {
      if (/add|education|rank/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-education'](); });
      }
    });
    // dashed "Add Education / Rank" placeholder card/button
    document.querySelectorAll('[onclick*="education"], .add-edu-btn').forEach(btn => {
      btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-education'](); });
    });
  }

  // ── Internships ──
  if (page === 'internships.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/add|internship/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-internship'](); });
      }
    });
    // Edit icons on intern cards
    document.querySelectorAll('.intern-card [data-action="edit"]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const card = btn.closest('.intern-card');
        DRAWERS['edit-internship-full'](card);
      });
    });
    // Delete buttons on intern cards
    document.querySelectorAll('.intern-card [data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const card = btn.closest('.intern-card');
        if (card) {
          if (card.dataset.id && card.dataset.type) { PortalStore.remove(card.dataset.type, card.dataset.id); }
          card.remove();
          showToast('Internship deleted.', 'info');
        }
      });
    });
  }

  // ── Projects ──
  if (page === 'projects.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/deploy|add|project/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['deploy-project'](); });
      }
    });
  }

  // ── Research ──
  if (page === 'research.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/add|publication|research/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-publication'](); });
      }
    });
  }

  // ── Certifications ──
  if (page === 'certifications.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/add|certification|cert/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-certification'](); });
      }
    });
  }

  // ── Events ──
  if (page === 'events.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/register|add|event/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-event'](); });
      }
    });
  }

  // ── Cohorts ──
  if (page === 'cohorts.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/join|cohort/i.test(btn.textContent)) {
        btn.addEventListener('click', e => {
          e.preventDefault();
          DRAWERS['join-cohort']();
        });
      }
    });
    // "Join This Cohort" inside individual cards
    document.querySelectorAll('.cohort-card .btn-primary').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const cohortName = btn.closest('.cohort-card')?.querySelector('.cohort-name')?.textContent || '';
        DRAWERS['join-cohort'](cohortName);
      });
    });
  }

  // ── Profile ──
  if (page === 'profile.html') {
    // Main "Edit Profile" button
    document.querySelectorAll('.btn-primary, .btn-ghost').forEach(btn => {
      if (/edit profile/i.test(btn.textContent)) {
        btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['edit-profile'](); });
      }
    });
    // Section-specific Edit buttons
    document.querySelectorAll('.card .btn-ghost').forEach(btn => {
      if (btn.textContent.trim() === 'Edit') {
        btn.addEventListener('click', e => {
          e.preventDefault();
          const card = btn.closest('.card');
          const heading = card?.querySelector('h2')?.textContent?.trim() || '';
          if (/about/i.test(heading)) {
            const textEl = card.querySelector('p');
            DRAWERS['edit-about'](textEl);
          } else if (/contact|link/i.test(heading)) {
            DRAWERS['edit-contact'](card.querySelector('.card-body'));
          } else {
            openDrawer('Edit ' + heading, 'Update your profile information.', `
              <div style="display:flex;flex-direction:column;gap:14px;">
                ${field('Content', textarea('Update your information here...', '', 5))}
                ${drawerFooter('Save Changes', heading + ' updated!')}
              </div>`);
          }
        });
      }
    });
  }

  // ── Settings ──
  if (page === 'settings.html') {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      if (/save|update/i.test(btn.textContent)) {
        btn.addEventListener('click', e => {
          e.preventDefault();
          showToast('Settings saved successfully!', 'success');
        });
      }
    });
  }

  // ── Universal: dashboard "boost" button ──
  document.querySelectorAll('.btn-boost').forEach(btn => {
    btn.addEventListener('click', e => { e.preventDefault(); DRAWERS['add-internship'](); });
  });

  // ── Universal: keyboard escape ──
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeDrawer();
  });
}

/* ─────────────────────────────────────
   NOTIFICATIONS
───────────────────────────────────── */
function initNotifications() {
  // Empty to prevent glitch with redirect.
}

/* ─────────────────────────────────────
   MID-TERM DROPDOWN
───────────────────────────────────── */
function initMidTermDropdown() {
  const select = document.getElementById('midterm-semester-select');
  const grid = document.getElementById('midterm-grid');
  if (!select || !grid) return;

  const midTermData = {
    '4': [
      { subject: 'Advanced Data Structures', code: 'CS401 · Core', mid1: 28, mid2: 29 },
      { subject: 'Operating Systems', code: 'CS402 · Core', mid1: 25, mid2: 22 },
      { subject: 'Database Management', code: 'CS403 · Core', mid1: 29, mid2: null }
    ],
    '3': [
      { subject: 'Computer Networks', code: 'CS301 · Core', mid1: 27, mid2: 28 },
      { subject: 'Algorithms', code: 'CS302 · Core', mid1: 24, mid2: 26 },
      { subject: 'Software Engineering', code: 'CS303 · Core', mid1: 28, mid2: 27 }
    ],
    '2': [
      { subject: 'Object Oriented Programming', code: 'CS201 · Core', mid1: 29, mid2: 30 },
      { subject: 'Data Structures', code: 'CS202 · Core', mid1: 26, mid2: 28 },
      { subject: 'Discrete Mathematics', code: 'MA201 · Core', mid1: 25, mid2: 24 }
    ],
    '1': [
      { subject: 'Programming in C', code: 'CS101 · Core', mid1: 28, mid2: 27 },
      { subject: 'Engineering Mathematics I', code: 'MA101 · Core', mid1: 30, mid2: 29 },
      { subject: 'Engineering Physics', code: 'PH101 · Core', mid1: 22, mid2: 25 }
    ]
  };

  select.addEventListener('change', (e) => {
    const sem = e.target.value;
    const data = midTermData[sem] || [];
    grid.innerHTML = data.map(item => {
      const avg = item.mid2 !== null ? ((item.mid1 + item.mid2) / 2).toFixed(1) : item.mid1.toFixed(1);
      const m2color = item.mid2 === null ? 'var(--muted)' : (item.mid2 >= 28 ? 'var(--green)' : (item.mid2 >= 25 ? 'var(--primary)' : 'var(--amber)'));
      const m1color = item.mid1 >= 28 ? 'var(--green)' : (item.mid1 >= 25 ? 'var(--primary)' : 'var(--amber)');
      const m2display = item.mid2 !== null ? item.mid2 : '--';

      return `
        <div style="background:var(--bg);border-radius:10px;padding:16px;border:1px solid var(--border);">
          <div style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:4px;">${item.subject}</div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:16px;">${item.code}</div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="text-align:center;">
              <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;font-weight:600;">Mid 1</div>
              <div style="font-size:18px;font-weight:800;color:${m1color};">${item.mid1} <span style="font-size:12px;color:var(--muted);font-weight:500;">/ 30</span></div>
            </div>
            <div style="width:1px;height:30px;background:var(--border);"></div>
            <div style="text-align:center;">
              <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;font-weight:600;">Mid 2</div>
              <div style="font-size:18px;font-weight:800;color:${m2color};">${m2display} <span style="font-size:12px;color:var(--muted);font-weight:500;">/ 30</span></div>
            </div>
            <div style="width:1px;height:30px;background:var(--border);"></div>
            <div style="text-align:center;">
              <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;font-weight:600;">Total Avg</div>
              <div style="font-size:18px;font-weight:800;color:var(--text);">${avg}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  });
}

/* ─────────────────────────────────────
   INIT
───────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  injectDrawerStyles();
  initSidebar();
  initTabs();
  initFlipCards();
  setActiveNav();
  animateBars();
  initDrawer();
  wireButtons();
  initNotifications();
  initMidTermDropdown();
  PortalStore.init();
});

/* ─────────────────────────────────────
   RENDER DASHBOARD DATA
───────────────────────────────────── */
function renderDashboard() {
  const container = document.getElementById('activity-feed-container');
  if (!container) return;

  const allItems = [];
  const mapItem = (type, titleField, descField, item) => ({
    type,
    id: Number(item.id),
    title: item[titleField],
    desc: item[descField] || '',
    item
  });

  PortalStore.data.projects.forEach(p => allItems.push(mapItem('Project', 'title', 'desc', p)));
  PortalStore.data.internships.forEach(p => allItems.push(mapItem('Internship', 'role', 'company', p)));
  PortalStore.data.certifications.forEach(p => allItems.push(mapItem('Certification', 'title', 'org', p)));
  PortalStore.data.education.forEach(p => allItems.push(mapItem('Education', 'institution', 'stream', p)));
  PortalStore.data.publications.forEach(p => allItems.push(mapItem('Publication', 'title', 'abstract', p)));

  allItems.sort((a,b) => b.id - a.id);

  if (allItems.length > 0) {
    // Generate feed items
    container.innerHTML = `<div style="display:flex;flex-direction:column;gap:16px;padding:20px;">
      ${allItems.slice(0, 5).map(item => {
        let icon = ''; let color = '';
        if (item.type === 'Project') { icon = '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>'; color = '#AF0C3E'; }
        if (item.type === 'Internship') { icon = '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>'; color = '#2563eb'; }
        if (item.type === 'Certification') { icon = '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'; color = '#16a34a'; }
        if (item.type === 'Education') { icon = '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>'; color = '#f59e0b'; }
        if (item.type === 'Publication') { icon = '<path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/>'; color = '#9333ea'; }

        return `<div style="display:flex;gap:14px;align-items:flex-start;">
          <div style="width:36px;height:36px;border-radius:50%;background:${color}1a;color:${color};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${icon}</svg>
          </div>
          <div>
            <div style="font-size:11px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:2px;">Added ${item.type}</div>
            <div style="font-size:14px;font-weight:600;margin-bottom:4px;">${item.title}</div>
            <div style="font-size:12px;color:#64748b;line-height:1.5;">${item.desc.substring(0,80)}${item.desc.length>80?'...':''}</div>
            <div style="font-size:11px;color:#cbd5e1;margin-top:6px;">Just now</div>
          </div>
        </div>`;
      }).join('<div style="height:1px;background:#e2e8f0;margin:6px 0;"></div>')}
    </div>`;
    container.classList.remove('empty-state');
  }

  // Update counts
  const projCount = document.querySelector('.projects-active');
  if (projCount) {
    projCount.innerHTML = `${PortalStore.data.projects.length} <span>Active</span>`;
  }
  const projGrid = document.querySelector('.project-dots');
  if (projGrid) {
    let dotsHtml = '';
    for (let i = 0; i < 6; i++) {
       if (i < PortalStore.data.projects.length) dotsHtml += '<div class="project-dot dot-filled"></div>';
       else dotsHtml += '<div class="project-dot dot-empty"></div>';
    }
    projGrid.innerHTML = dotsHtml;
  }

  const certCount = document.querySelector('.cert-verified strong');
  if (certCount) {
    certCount.textContent = PortalStore.data.certifications.length;
  }
}
