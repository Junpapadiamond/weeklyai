/**
 * WeeklyAI - Main Entry Point
 * Initializes all modules and coordinates the application
 *
 * Module Dependencies (load order matters):
 * 1. state.js      - Global state management
 * 2. utils.js      - Utility functions
 * 3. api.js        - API client
 * 4. ui/*.js       - UI components
 * 5. sections/*.js - Page sections
 * 6. main.js       - This file (initialization)
 */

const App = {
    /**
     * Initialize the application
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.bootstrap());
        } else {
            this.bootstrap();
        }
    },

    /**
     * Bootstrap all modules
     */
    bootstrap() {
        console.log('🚀 WeeklyAI initializing...');

        // Initialize Lucide icons first
        this.initLucide();

        // Initialize UI modules
        Theme.init();
        Navigation.init();
        Modal.init();
        Animations.initHeroGlow();

        // Initialize section modules
        Favorites.init();
        Discovery.init();
        DarkHorse.init();
        Trending.init();
        Search.init();
        Blogs.init();
        Leaders.init();

        // Load data freshness indicator
        this.loadDataFreshness();

        console.log('✅ WeeklyAI ready!');
    },

    /**
     * Initialize Lucide icons
     */
    initLucide() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        } else {
            // Retry after a short delay if lucide isn't loaded yet
            setTimeout(() => {
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }, 500);
        }
    },

    /**
     * Load and display data freshness indicator
     */
    async loadDataFreshness() {
        const el = document.getElementById('dataFreshness');
        if (!el) return;

        try {
            const response = await API.getLastUpdated();

            if (response.success) {
                const hoursAgo = response.hours_ago || 0;
                const lastUpdated = response.last_updated || '';

                let statusText = '';
                let statusClass = '';

                if (hoursAgo < 1) {
                    statusText = '📡 数据刚刚更新';
                    statusClass = 'fresh';
                } else if (hoursAgo < 6) {
                    statusText = `📡 ${Math.round(hoursAgo)} 小时前更新`;
                    statusClass = 'recent';
                } else if (hoursAgo < 24) {
                    statusText = `📡 ${Math.round(hoursAgo)} 小时前更新`;
                    statusClass = 'normal';
                } else {
                    const days = Math.round(hoursAgo / 24);
                    statusText = `📡 ${days} 天前更新`;
                    statusClass = 'stale';
                }

                el.innerHTML = `<span class="freshness-status freshness-status--${statusClass}">${statusText}</span>`;
            }
        } catch (error) {
            console.error('Failed to load data freshness:', error);
            el.innerHTML = '<span class="freshness-status freshness-status--unknown">📡 数据状态未知</span>';
        }
    }
};

// Global function exports for inline event handlers (backward compatibility)
// These will be removed once all inline handlers are converted to addEventListener

function handleLogoError(img, initial) {
    img.onerror = null;
    img.outerHTML = `<div class="product-logo-placeholder">${initial}</div>`;
}

function openProduct(url) {
    if (url) window.open(url, '_blank');
}

// Start the application
App.init();

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = App;
} else {
    window.App = App;
}
