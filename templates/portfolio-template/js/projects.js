
/**
 * projects.js — Project data store & rendering logic
 * Simulates a backend data source with rich project metadata.
 */

// ─────────────────────────────────────────────
// DATA: Student Projects
// ─────────────────────────────────────────────
const PROJECTS_DATA = [
  {
    id: 1,
    title: 'AI Study Companion',
    description: 'An intelligent study assistant powered by NLP that generates quizzes, summarizes lecture notes, and tracks student progress over time using spaced-repetition algorithms.',
    tech: ['React', 'Python', 'FastAPI', 'OpenAI', 'PostgreSQL'],
    category: 'AI/ML',
    emoji: '🤖',
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
    year: '2025',
    status: 'Production',
    // highlights: [
    //   'Reduced revision time by 37% for a beta cohort of 220 students',
    //   'Generated 12k adaptive quiz questions with concept-level tracking',
    // ],
    // impact: [
    //   { label: 'Active users', value: '2.3k' },
    //   { label: 'Accuracy gain', value: '+21%' },
    // ],
    liveUrl: '#',
    githubUrl: '#',
    featured: true,
  },
  {
    id: 2,
    title: 'Campus Connect',
    description: 'A social networking platform for college students to discover clubs, events, and peer opportunities. Features real-time messaging using WebSockets.',
    tech: ['Next.js', 'Node.js', 'Socket.io', 'MongoDB', 'Tailwind'],
    category: 'Full Stack',
    emoji: '🎓',
    gradient: 'linear-gradient(135deg, #f093fb, #f5576c)',
    year: '2024',
    status: 'Live',
    // highlights: [
    //   'Implemented event matchmaking based on interests and attendance history',
    //   'Shipped real-time campus rooms with delivery status and moderation tools',
    // ],
    // impact: [
    //   { label: 'Communities', value: '75+' },
    //   { label: 'Messages/day', value: '18k' },
    // ],
    liveUrl: '#',
    githubUrl: '#',
    featured: true,
  },
  {
    id: 3,
    title: 'DevOps Pipeline Manager',
    description: 'A CI/CD dashboard for small teams. Integrates with GitHub webhooks to provide real-time build status, deployment logs, and performance metrics.',
    tech: ['Vue.js', 'Go', 'Docker', 'Redis', 'GitHub API'],
    category: 'DevOps',
    emoji: '⚙️',
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
    year: '2024',
    status: 'Internal',
    // highlights: [
    //   'Connected 40+ repositories through webhook-driven pipelines',
    //   'Introduced release quality gates and automated rollback triggers',
    // ],
    // impact: [
    //   { label: 'Deploy speed', value: '2.1x' },
    //   { label: 'MTTR', value: '-31%' },
    // ],
    liveUrl: '#',
    githubUrl: '#',
    featured: false,
  },
  {
    id: 4,
    title: 'Blockchain Voting DApp',
    description: 'A decentralized voting application on Ethereum ensuring tamper-proof, transparent elections. Uses smart contracts written in Solidity with MetaMask integration.',
    tech: ['Solidity', 'React', 'Web3.js', 'Hardhat', 'IPFS'],
    category: 'Web3',
    emoji: '🗳️',
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)',
    year: '2023',
    status: 'Prototype',
    // highlights: [
    //   'Designed tamper-resistant voting with wallet-based identity checks',
    //   'Added verifiable tally proofs and immutable vote receipts',
    // ],
    impact: [
      { label: 'Gas saved', value: '28%' },
      { label: 'Test voters', value: '4k' },
    ],
    liveUrl: '#',
    githubUrl: '#',
    featured: false,
  },
  {
    id: 5,
    title: 'Health Tracker Mobile App',
    description: 'A cross-platform mobile app for tracking nutrition, workouts, and wellness. Features ML-powered meal recognition via device camera and personalized insights.',
    tech: ['React Native', 'TensorFlow Lite', 'Firebase', 'Expo'],
    category: 'Mobile',
    emoji: '💪',
    gradient: 'linear-gradient(135deg, #fa709a, #fee140)',
    year: '2023',
    status: 'Beta',
    // highlights: [
    //   'Built on-device meal recognition for low-latency nutrition logging',
    //   'Added adaptive plans based on exercise consistency and sleep trends',
    // ],
    impact: [
      { label: '7-day retention', value: '64%' },
      { label: 'Meals scanned', value: '30k+' },
    ],
    liveUrl: '#',
    githubUrl: '#',
    featured: false,
  },
  {
    id: 6,
    title: 'Open Source CLI Toolkit',
    description: 'A collection of productivity CLI tools for developers: auto-formatter, project scaffolder, and git commit generator. 800+ GitHub stars.',
    tech: ['Node.js', 'Python', 'Bash', 'GitHub Actions'],
    category: 'Open Source',
    emoji: '🛠️',
    gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)',
    year: '2022-2025',
    status: 'OSS',
    // highlights: [
    //   'Built extensible command architecture with plugin support',
    //   'Automated semantic release and changelog workflows for contributors',
    // ],
    // impact: [
    //   { label: 'GitHub stars', value: '800+' },
    //   { label: 'Contributors', value: '29' },
    // ],
    liveUrl: '#',
    githubUrl: '#',
    featured: false,
  },
];

// ─────────────────────────────────────────────
// RENDER HELPERS
// ─────────────────────────────────────────────

/**
 * Create a project card DOM element.
 * @param {Object} project
 * @returns {HTMLElement}
 */
function createProjectCard(project) {
  const card = document.createElement('div');
  card.className = 'card project-card reveal';
  card.dataset.category = project.category;

  const techBadges = project.tech.map(t =>
    `<span class="tech-badge">${t}</span>`
  ).join('');

  const statBadges = (project.impact || []).map(stat =>
    `<span class="project-stat"><strong>${stat.value}</strong><small>${stat.label}</small></span>`
  ).join('');

  const highlights = (project.highlights || []).slice(0, 2).map(text =>
    `<li>${text}</li>`
  ).join('');

  card.innerHTML = `
    <div class="project-card-image" style="background: ${project.gradient}">
      <span style="color: white; font-size: 3rem; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3))">${project.emoji}</span>
      ${project.featured ? '<span class="project-featured-badge">★ FEATURED</span>' : ''}
      <div class="project-status-chip">${project.status || 'Active'}</div>
    </div>
    <div class="project-meta-row">
      <span class="project-category">${project.category}</span>
      <span class="project-year">${project.year || ''}</span>
    </div>
    <h3 class="project-card-title">${project.title}</h3>
    <p class="project-card-desc">${project.description}</p>
    <ul class="project-highlights">${highlights}</ul>
    <div class="project-stats">${statBadges}</div>
    <div class="tech-stack">${techBadges}</div>
    <div class="project-links">
      <a href="${project.liveUrl}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">
        🚀 Live Demo
      </a>
      <a href="${project.githubUrl}" class="btn btn-ghost btn-sm" target="_blank" rel="noopener">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/></svg>
        GitHub
      </a>
    </div>
  `;

  return card;
}

/**
 * Get unique categories from project data.
 * @returns {string[]}
 */
function getProjectCategories() {
  return ['All', ...new Set(PROJECTS_DATA.map(p => p.category))];
}

/**
 * Render all projects (or filtered subset) to a container.
 * @param {string} containerSelector
 * @param {string} filterCategory - 'All' or a specific category
 * @param {number} maxItems - optional maximum number of cards to render
 */
function renderProjects(containerSelector, filterCategory = 'All', maxItems) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  let filtered = filterCategory === 'All'
    ? PROJECTS_DATA
    : PROJECTS_DATA.filter(p => p.category === filterCategory);

  if (typeof maxItems === 'number') {
    filtered = filtered.slice(0, maxItems);
  }

  container.innerHTML = '';

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <div class="empty-state-icon">🔍</div>
        <p>No projects found in this category.</p>
      </div>`;
    return;
  }

  filtered.forEach((project, i) => {
    const card = createProjectCard(project);
    card.style.transitionDelay = `${i * 0.08}s`;
    container.appendChild(card);
  });

  // Trigger reveal animations
  requestAnimationFrame(() => {
    container.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
  });
}

/**
 * Render filter pills and wire up filtering.
 * @param {string} pillsContainerSelector
 * @param {string} projectsContainerSelector
 */
function renderProjectFilters(pillsContainerSelector, projectsContainerSelector) {
  const container = document.querySelector(pillsContainerSelector);
  if (!container) return;

  const categories = getProjectCategories();
  container.innerHTML = '';

  categories.forEach(cat => {
    const pill = document.createElement('button');
    pill.className = `filter-pill${cat === 'All' ? ' active' : ''}`;
    pill.textContent = cat;
    pill.addEventListener('click', () => {
      container.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      renderProjects(projectsContainerSelector, cat);
    });
    container.appendChild(pill);
  });
}

// ─────────────────────────────────────────────
// INIT: called on DOMContentLoaded for projects page
// ─────────────────────────────────────────────
function initProjects() {
  renderProjectFilters('#project-filters', '#projects-grid');
  renderProjects('#projects-grid');
}
