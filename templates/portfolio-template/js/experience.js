/**
 * experience.js — Experience & internship data store and renderer
 */

// ─────────────────────────────────────────────
// DATA: Work Experience
// ─────────────────────────────────────────────
const EXPERIENCE_DATA = [
  {
    id: 1,
    company: 'Google',
    role: 'Software Engineering Intern',
    type: 'Internship',
    location: 'Bangalore, India',
    duration: 'May 2024 – Aug 2024',
    emoji: '🔵',
    logo: null,
    description:
      'Contributed to the Google Maps backend serving 1B+ users. Designed an A/B testing pipeline that improved route accuracy by 12%. Collaborated with senior engineers in weekly design reviews and reduced latency by 18% via cache-layer optimizations.',
    responsibilities: [
      'Built experimentation pipelines and result dashboards for routing model evaluation.',
      'Optimized cache interactions and request paths for high-throughput services.',
    ],
    skills: ['Go', 'Kubernetes', 'gRPC', 'BigQuery', 'Python', 'Spanner'],
    link: 'https://google.com',
  },
  {
    id: 2,
    company: 'Razorpay',
    role: 'Frontend Developer Intern',
    type: 'Internship',
    location: 'Bengaluru, India (Remote)',
    duration: 'Dec 2023 – Feb 2024',
    emoji: '💙',
    logo: null,
    description:
      'Built and shipped three new UI components for the merchant dashboard used by 8M+ businesses. Implemented micro-interactions improving task completion rate by 9%. Participated in code reviews and documented component APIs.',
    responsibilities: [
      'Implemented reusable dashboard components with Storybook-driven documentation.',
      'Partnered with design and QA to improve usability and release confidence.',
    ],
    skills: ['React', 'TypeScript', 'Storybook', 'Figma', 'Jest', 'CSS Modules'],
    link: 'https://razorpay.com',
  },
  {
    id: 3,
    company: 'Open Source — FOSSEE, IIT Bombay',
    role: 'GSoC Contributor',
    type: 'Open Source',
    location: 'Remote',
    duration: 'Jun 2023 – Sep 2023',
    emoji: '🌐',
    logo: null,
    description:
      'Selected among 1,200 applicants for Google Summer of Code. Migrated a legacy Python 2 data-analysis toolkit to Python 3, added 60+ unit tests achieving 94% coverage, and reduced build time by 35%.',
    responsibilities: [
      'Migrated core modules and established a modern Python packaging workflow.',
      'Expanded test coverage and CI checks to reduce regressions in releases.',
    ],
    skills: ['Python', 'NumPy', 'Pytest', 'GitHub Actions', 'Sphinx'],
    link: 'https://summerofcode.withgoogle.com',
  },
  {
    id: 4,
    company: 'StartupX Labs',
    role: 'Full-Stack Developer',
    type: 'Part-time',
    location: 'Mumbai, India',
    duration: 'Jan 2023 – May 2023',
    emoji: '🚀',
    logo: null,
    description:
      'Sole developer for an early-stage EdTech SaaS product. Architected the entire backend API (Node.js + PostgreSQL) and built the React dashboard from scratch. Met 100% of sprint commitments across 5 releases.',
    responsibilities: [
      'Owned backend architecture, API contracts, and database modeling end-to-end.',
      'Delivered product increments across five releases with full observability setup.',
    ],
    skills: ['Node.js', 'React', 'PostgreSQL', 'AWS EC2', 'Stripe API', 'Nginx'],
    link: '#',
  },
];

// ─────────────────────────────────────────────
// RENDER HELPERS
// ─────────────────────────────────────────────

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function safeExternalUrl(url) {
  if (typeof url !== 'string') return null;
  const trimmed = url.trim();
  if (!trimmed || trimmed === '#') return null;

  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
    return parsed.href;
  } catch {
    return null;
  }
}

/**
 * Returns badge HTML for experience type.
 * @param {string} type
 */
function getTypeBadge(type) {
  const map = {
    'Internship': { bg: 'rgba(175,12,62,0.10)', color: 'var(--primary)', border: 'rgba(175,12,62,0.2)' },
    'Open Source': { bg: 'rgba(34,211,238,0.10)', color: '#0891B2', border: 'rgba(34,211,238,0.2)' },
    'Part-time': { bg: 'rgba(245,158,11,0.10)', color: '#D97706', border: 'rgba(245,158,11,0.2)' },
    'Full-time': { bg: 'rgba(34,197,94,0.10)', color: '#16A34A', border: 'rgba(34,197,94,0.2)' },
  };
  const style = map[type] || map['Internship'];
  const safeType = escapeHtml(type);
  return `<span style="background:${style.bg}; color:${style.color}; border: 1px solid ${style.border}; font-size:0.7rem; font-weight:700; padding:0.2rem 0.55rem; border-radius:99px; letter-spacing:0.06em;">${safeType}</span>`;
}

/**
 * Create a timeline experience item with advanced alternating layout.
 * @param {Object} exp
 * @param {number} index - For alternating left/right positioning
 * @param {boolean} compact - Show compact version for previews
 * @returns {HTMLElement}
 */
function createExperienceItem(exp, index = 0, compact = false) {
  const item = document.createElement('div');
  const position = index % 2 === 0 ? 'left' : 'right';
  item.className = `timeline-item timeline-item-${position} reveal`;

  const role = escapeHtml(exp.role);
  const company = escapeHtml(exp.company);
  const type = String(exp.type ?? '');
  const description = escapeHtml(exp.description);
  const location = escapeHtml(exp.location);
  const duration = escapeHtml(exp.duration);
  const emoji = escapeHtml(exp.emoji || '💼');

  const skills = Array.isArray(exp.skills) ? exp.skills : [];
  const skillBadges = skills.map(s =>
    `<span class="exp-skill">${escapeHtml(s)}</span>`
  ).join('');

  const responsibilities = (Array.isArray(exp.responsibilities) ? exp.responsibilities : []).map(point =>
    `<li>${escapeHtml(point)}</li>`
  ).join('');

  const linkUrl = safeExternalUrl(exp.link);
  const linkCta = linkUrl
    ? `<a class="exp-link" href="${linkUrl}" target="_blank" rel="noopener noreferrer" aria-label="Open ${company} link">↗</a>`
    : '';

  item.innerHTML = `
    <div class="timeline-dot"></div>
    <div class="timeline-connector" aria-hidden="true"></div>
    <div class="timeline-card timeline-card-advanced">
      <div class="exp-badge-wrap">
        <div class="exp-icon-badge" aria-hidden="true">${emoji}</div>
      </div>
      
      <div class="exp-content">
        <div class="exp-header-advanced">
          <div>
            <h3 class="exp-role-main">${role}</h3>
            <p class="exp-company-sub">${company}</p>
          </div>
          <div class="exp-header-actions">
            ${getTypeBadge(type)}
            ${linkCta}
          </div>
        </div>
        
        <p class="exp-desc">${description}</p>
        
        ${compact ? '' : `<ul class="exp-responsibilities">${responsibilities}</ul>`}
        
        <div class="exp-footer">
          <div class="exp-skills">${skillBadges}</div>
          <div class="exp-meta-footer">
            <span>📍 ${location}</span>
            <span>📅 ${duration}</span>
          </div>
        </div>
      </div>
    </div>
  `;

  return item;
}

/**
 * Render all experience to a timeline container.
 * @param {string} containerSelector
 */
function renderExperience(containerSelector, maxItems) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  const data = typeof maxItems === 'number'
    ? EXPERIENCE_DATA.slice(0, maxItems)
    : EXPERIENCE_DATA;
  const compact = typeof maxItems === 'number';

  container.innerHTML = '';
  data.forEach((exp, i) => {
    const item = createExperienceItem(exp, i, compact);
    item.style.transitionDelay = `${i * 0.1}s`;
    container.appendChild(item);
  });

  requestAnimationFrame(() => {
    container.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
  });
}

// Main init
function initExperience() {
  renderExperience('#experience-timeline');
}
