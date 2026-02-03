/**
 * WeeklyAI - Navigation
 * Routing and section switching
 */

const Navigation = {
    sections: ['discover', 'trending', 'blogs', 'leaders', 'search', 'product'],
    activeSection: 'discover',

    init() {
        this.initNavLinks();
        this.initScrollHighlight();
        this.handleInitialRoute();
    },

    initNavLinks() {
        const navLinks = document.querySelectorAll('.nav-link[data-section]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.switchSection(section);
                history.pushState({ section }, '', `#${section}`);
            });
        });

        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            const section = e.state?.section || this.getSectionFromHash() || 'discover';
            this.switchSection(section, false);
        });
    },

    initScrollHighlight() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        window.addEventListener('scroll', Utils.throttle(() => {
            if (window.scrollY > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, 100));
    },

    handleInitialRoute() {
        const section = this.getSectionFromHash();
        if (section && this.sections.includes(section)) {
            this.switchSection(section);
        }
    },

    getSectionFromHash() {
        const hash = window.location.hash.slice(1);
        return hash || null;
    },

    switchSection(section, updateNav = true) {
        // Hide all sections
        this.sections.forEach(s => {
            const el = document.getElementById(`${s}Section`);
            if (el) el.style.display = 'none';
        });

        // Show target section
        const targetSection = document.getElementById(`${section}Section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // Special handling for discover - also show darkhorse and trending
        if (section === 'discover') {
            const darkhorseSection = document.getElementById('darkhorseSection');
            const trendingSection = document.getElementById('trendingSection');
            if (darkhorseSection && AppState.ui.hasDarkhorseData) {
                darkhorseSection.style.display = 'block';
            }
            if (trendingSection) {
                trendingSection.style.display = 'block';
            }
        }

        // Update nav active state
        if (updateNav) {
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.toggle('active', link.dataset.section === section);
            });
        }

        this.activeSection = section;

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    getActiveSection() {
        return this.activeSection;
    },

    showSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) section.style.display = 'block';
    },

    hideSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) section.style.display = 'none';
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Navigation;
} else {
    window.Navigation = Navigation;
}
