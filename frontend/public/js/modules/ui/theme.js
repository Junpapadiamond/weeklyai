/**
 * WeeklyAI - Theme Toggle
 * Dark/Light mode management
 */

const Theme = {
    STORAGE_KEY: 'weeklyai_theme',

    init() {
        const toggle = document.getElementById('themeToggle');
        if (!toggle) return;

        // Load saved theme or use system preference
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

        this.setTheme(theme);

        // Toggle button click
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
            localStorage.setItem(this.STORAGE_KEY, newTheme);
        });

        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.STORAGE_KEY)) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.innerHTML = theme === 'dark'
                ? '<i data-lucide="sun"></i>'
                : '<i data-lucide="moon"></i>';

            // Refresh lucide icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    },

    getTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    },

    isDark() {
        return this.getTheme() === 'dark';
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Theme;
} else {
    window.Theme = Theme;
}
