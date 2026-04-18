/**
 * main.js — Core application bootstrap
 * Handles: component loading, scroll effects, animations, toasts, typed text
 */

// ─────────────────────────────────────────────
// COMPONENT LOADER
// Load HTML partials into named slots: <div data-component="navbar">
// ─────────────────────────────────────────────

/**
 * Load an HTML file and inject it into the target element.
 * @param {string} path - relative path to HTML partial
 * @param {HTMLElement} target
 * @returns {Promise<void>}
 */
async function loadComponent(path, target) {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Failed to load: ${path}`);
    const html = await response.text();
    target.innerHTML = html;
  } catch (err) {
    console.warn(`[main.js] Component load error: ${err.message}`);
  }
}

/**
 * Discover all [data-component] slots and load their partials.
 * Base path is resolved relative to /components/.
 */
async function loadAllComponents() {
  const slots = document.querySelectorAll('[data-component]');
  const basePath = getBasePath() + 'components/';

  await Promise.all(
    Array.from(slots).map(slot => {
      const name = slot.dataset.component;
      return loadComponent(basePath + name + '.html', slot);
    })
  );
}

/**
 * Compute base path from the current location so components
 * load correctly regardless of which subfolder the page is in.
 */
function getBasePath() {
  const path = window.location.pathname;
  const depth = (path.match(/\//g) || []).length - 1;
  return depth <= 1 ? './' : '../'.repeat(depth - 1);
}

// ─────────────────────────────────────────────
// NAVBAR EFFECTS
// ─────────────────────────────────────────────

function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  // Scroll shadow
  const onScroll = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  };
  window.addEventListener('scroll', onScroll, { passive: true });

  // Active link highlighting
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href') || '';
    if (href.includes(currentPage) || (currentPage === 'index.html' && href.endsWith('index.html'))) {
      link.classList.add('active');
    }
  });

  // Mobile hamburger
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobile-nav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => {
      const open = hamburger.classList.toggle('open');
      mobileNav.classList.toggle('open', open);
      hamburger.setAttribute('aria-expanded', open);
    });

    // Close mobile nav on link click
    mobileNav.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        hamburger.classList.remove('open');
        mobileNav.classList.remove('open');
      });
    });
  }

  // Wire theme toggle
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.addEventListener('click', toggleTheme);
  });

  // Sync icon
  syncThemeIcon();
}

// ─────────────────────────────────────────────
// SCROLL REVEAL
// ─────────────────────────────────────────────

function initScrollReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ─────────────────────────────────────────────
// SKILL BARS ANIMATION
// ─────────────────────────────────────────────

function initSkillBars() {
  const fills = document.querySelectorAll('.skill-fill[data-pct]');
  if (!fills.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const fill = entry.target;
          fill.style.width = fill.dataset.pct + '%';
          observer.unobserve(fill);
        }
      });
    },
    { threshold: 0.3 }
  );

  fills.forEach(fill => observer.observe(fill));
}

// ─────────────────────────────────────────────
// TYPED TEXT EFFECT
// ─────────────────────────────────────────────

/**
 * @param {HTMLElement} el  - element to type into
 * @param {string[]} words  - array of strings to cycle
 * @param {number} speed    - ms per character
 */
function initTyped(el, words, speed = 80) {
  if (!el) return;
  let wordIdx = 0;
  let charIdx = 0;
  let deleting = false;
  let pauseTimer = null;

  function tick() {
    const word = words[wordIdx];
    if (!deleting) {
      el.textContent = word.slice(0, ++charIdx);
      if (charIdx === word.length) {
        deleting = true;
        pauseTimer = setTimeout(tick, 1800);
        return;
      }
    } else {
      el.textContent = word.slice(0, --charIdx);
      if (charIdx === 0) {
        deleting = false;
        wordIdx = (wordIdx + 1) % words.length;
      }
    }
    setTimeout(tick, deleting ? speed / 2 : speed);
  }

  tick();
}

// ─────────────────────────────────────────────
// COUNTER ANIMATION
// ─────────────────────────────────────────────

function animateCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    const suffix = el.dataset.suffix || '';
    const duration = 1800;
    const step = Math.ceil(target / (duration / 16));
    let current = 0;

    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current + suffix;
        if (current >= target) clearInterval(timer);
      }, 16);
    }, { threshold: 0.5 });

    observer.observe(el);
  });
}

// ─────────────────────────────────────────────
// TOAST NOTIFICATION
// ─────────────────────────────────────────────

const TOAST_ICONS = { success: '✅', info: 'ℹ️', warning: '⚠️', error: '❌' };

function showToast(message, type = 'info', duration = 3500) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${TOAST_ICONS[type] || 'ℹ️'}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}

// ─────────────────────────────────────────────
// LOADING SCREEN
// ─────────────────────────────────────────────

function hideLoading() {
  const screen = document.getElementById('loading-screen');
  if (screen) {
    screen.classList.add('hidden');
    setTimeout(() => screen.remove(), 500);
  }
}

// ─────────────────────────────────────────────
// SKILLS DATA & RENDERER
// ─────────────────────────────────────────────

const SKILLS_DATA = [
  {
    group: '🖥️ Frontend',
    skills: [
      { name: 'React / Next.js', pct: 90 },
      { name: 'TypeScript', pct: 85 },
      { name: 'CSS / Tailwind', pct: 88 },
      { name: 'Vue.js', pct: 72 },
    ],
  },
  {
    group: '⚙️ Backend',
    skills: [
      { name: 'Node.js / Express', pct: 88 },
      { name: 'Python / FastAPI', pct: 82 },
      { name: 'Go', pct: 65 },
      { name: 'GraphQL', pct: 70 },
    ],
  },
  {
    group: '🗄️ Databases',
    skills: [
      { name: 'PostgreSQL', pct: 84 },
      { name: 'MongoDB', pct: 80 },
      { name: 'Redis', pct: 74 },
      { name: 'Firebase', pct: 78 },
    ],
  },
  {
    group: '☁️ Cloud & DevOps',
    skills: [
      { name: 'Docker / Kubernetes', pct: 76 },
      { name: 'AWS (EC2, S3, Lambda)', pct: 72 },
      { name: 'GitHub Actions', pct: 85 },
      { name: 'Linux / Bash', pct: 80 },
    ],
  },
];

function renderSkills(containerSelector) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  container.innerHTML = '';

  SKILLS_DATA.forEach((group, gi) => {
    const groupEl = document.createElement('div');
    groupEl.className = 'skill-group reveal';
    groupEl.style.transitionDelay = `${gi * 0.1}s`;

    const skillsHTML = group.skills.map(skill => `
      <div class="skill-item">
        <div class="skill-info">
          <span class="skill-name">${skill.name}</span>
          <span class="skill-pct">${skill.pct}%</span>
        </div>
        <div class="skill-bar">
          <div class="skill-fill" data-pct="${skill.pct}" style="width:0%"></div>
        </div>
      </div>
    `).join('');

    groupEl.innerHTML = `
      <div class="skill-group-title">${group.group}</div>
      ${skillsHTML}
    `;

    container.appendChild(groupEl);
  });

  // Re-run observers for newly added elements
  initScrollReveal();
  initSkillBars();
}

// ─────────────────────────────────────────────
// ACHIEVEMENTS DATA & RENDERER
// ─────────────────────────────────────────────

const ACHIEVEMENTS_DATA = [
  {
    icon: '🏆',
    iconClass: 'gold',
    title: 'Smart India Hackathon 2024 — Winner',
    sub: 'National-level competition, 1st place among 4,200 teams',
    date: 'August 2024',
  },
  {
    icon: '⭐',
    iconClass: 'accent',
    title: 'Google Summer of Code 2023',
    sub: 'Selected for FOSSEE IIT Bombay; open-source contribution',
    date: 'June 2023',
  },
  {
    icon: '🥇',
    iconClass: 'primary',
    title: 'ACM-ICPC Regional Qualifier',
    sub: 'Ranked 28th in the Asia-Pacific region qualifiers',
    date: 'October 2023',
  },
  {
    icon: '🎓',
    iconClass: 'gold',
    title: 'Dean\'s List — 5 consecutive semesters',
    sub: 'Maintained CGPA ≥ 9.0 throughout the program',
    date: '2022 – 2024',
  },
  {
    icon: '🌟',
    iconClass: 'silver',
    title: 'GitHub Star Developer',
    sub: 'CLI Toolkit project reached 800+ GitHub stars',
    date: 'February 2024',
  },
  {
    icon: '📜',
    iconClass: 'accent',
    title: 'AWS Certified Solutions Architect',
    sub: 'Associate-level certification with 85% score',
    date: 'March 2024',
  },
];

function renderAchievements(containerSelector) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  container.innerHTML = '';

  ACHIEVEMENTS_DATA.forEach((a, i) => {
    const card = document.createElement('div');
    card.className = 'card reveal';
    card.style.transitionDelay = `${i * 0.08}s`;

    card.innerHTML = `
      <div class="achievement-card">
        <div class="achievement-icon ${a.iconClass}">${a.icon}</div>
        <div>
          <div class="achievement-title">${a.title}</div>
          <div class="achievement-sub">${a.sub}</div>
          <div class="achievement-date">${a.date}</div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });

  initScrollReveal();
}

// ─────────────────────────────────────────────
// EDUCATION DATA & RENDERER
// ─────────────────────────────────────────────

const EDUCATION_DATA = [
  {
    icon: '🏫',
    institution: 'Indian Institute of Technology, Bombay',
    degree: 'B.Tech in Computer Science & Engineering',
    year: '2021 – 2025',
    cgpa: '9.24 / 10',
    location: 'Mumbai, Maharashtra',
  },
  {
    icon: '🏫',
    institution: 'Delhi Public School, RK Puram',
    degree: 'Senior Secondary — CBSE Science (PCM + CS)',
    year: '2019 – 2021',
    cgpa: '96.2%',
    location: 'New Delhi',
  },
  {
    icon: '🏫',
    institution: 'Delhi Public School, RK Puram',
    degree: 'Secondary — CBSE',
    year: '2009 – 2019',
    cgpa: '98.4%',
    location: 'New Delhi',
  },
];

function renderEducation(containerSelector) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  container.innerHTML = '';

  EDUCATION_DATA.forEach((edu, i) => {
    const card = document.createElement('div');
    card.className = 'card reveal';
    card.style.transitionDelay = `${i * 0.1}s`;

    card.innerHTML = `
      <div class="edu-card">
        <div class="edu-icon">${edu.icon}</div>
        <div class="edu-body">
          <div class="edu-institution">${edu.institution}</div>
          <div class="edu-degree">${edu.degree}</div>
          <div class="edu-meta">
            <span class="edu-badge">📅 ${edu.year}</span>
            <span class="edu-badge edu-cgpa">⭐ ${edu.cgpa}</span>
            <span class="edu-badge">📍 ${edu.location}</span>
          </div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });

  initScrollReveal();
}

// ─────────────────────────────────────────────
// BOOTSTRAP
// Application entry point
// ─────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Load all HTML components
  await loadAllComponents();

  // 2. Init navbar (must be after navbar component loads)
  initNavbar();

  // 3. Hide loading screen
  hideLoading();

  // 4. Page-specific init
  const page = document.body.dataset.page;

  if (page === 'portfolio') {
    initTyped(
      document.getElementById('typed-text'),
      ['Student Developer', 'Project Builder', 'Portfolio Owner'],
      75
    );
    animateCounters();
  }

  if (page === 'home' || page === 'profile') {
    // Hero typed text
    initTyped(
      document.getElementById('typed-text'),
      ['Full-Stack Developer', 'ML Enthusiast', 'Open Source Contributor', 'Problem Solver'],
      75
    );
    animateCounters();
    renderSkills('#skills-grid');
    renderAchievements('#achievements-grid');
    renderProjects('#projects-preview', 'All', 3);
    renderExperience('#home-experience-timeline', 3);
  }

  if (page === 'projects') {
    initProjects();
  }

  if (page === 'experience') {
    initExperience();
  }

  if (page === 'education') {
    renderEducation('#education-list');
    renderSkills('#skills-grid');
  }

  // 5. Global scroll reveal
  initScrollReveal();

  // 6. Smooth page-entrance animation for main content
  requestAnimationFrame(() => {
    document.querySelector('main')?.classList.add('visible');
  });
});
