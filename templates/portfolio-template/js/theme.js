/**
 * theme.js — Dark mode persistence & toggle logic
 * Reads/writes user preference to localStorage under key "portfolio-theme"
 */

const THEME_KEY = 'portfolio-theme';
const DARK_CLASS = 'dark';

// Apply theme instantly (before DOM paint to avoid flash)
(function applyStoredTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add(DARK_CLASS);
  }
})();

/**
 * Toggle between light and dark mode, persist to localStorage.
 */
function toggleTheme() {
  const isDark = document.documentElement.classList.toggle(DARK_CLASS);
  localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');

  // Sync all toggle button icons on the page
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    const icon = btn.querySelector('[data-icon]');
    if (icon) icon.textContent = isDark ? '☀️' : '🌙';
  });
}

/**
 * Get current theme string: "dark" | "light"
 */
function getCurrentTheme() {
  return document.documentElement.classList.contains(DARK_CLASS) ? 'dark' : 'light';
}

/**
 * Sync the toggle button icon to the current theme.
 * Call this after the navbar component is injected.
 */
function syncThemeIcon() {
  const isDark = getCurrentTheme() === 'dark';
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    const icon = btn.querySelector('[data-icon]');
    if (icon) icon.textContent = isDark ? '☀️' : '🌙';
  });
}

// System theme change listener (when preference changes externally)
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (!localStorage.getItem(THEME_KEY)) {
    document.documentElement.classList.toggle(DARK_CLASS, e.matches);
    syncThemeIcon();
  }
});
