/**
 * WeeklyAI - Centralized State Management
 * All global state is managed here to avoid pollution
 */

const AppState = {
    // API configuration
    API_BASE_URL: 'http://localhost:5000/api/v1',

    // User preferences
    prefersReducedMotion: window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches,

    // UI state
    ui: {
        selectedCategories: new Set(),
        hasDarkhorseData: true,
        currentSort: 'score',
        currentTypeFilter: 'all',
        currentTier: 'all', // all, darkhorse, rising
        darkHorseFilter: 'all', // all, hardware, software
        discoverFilter: 'all',
        leadersActiveFilter: 'all',
        currentPage: 1,
    },

    // Data caches
    cache: {
        allProducts: [],
        discoveryProducts: [],
        darkHorses: [],
        leaderCategories: null,
    },

    // Pagination config
    PRODUCTS_PER_PAGE: 12,

    // LocalStorage keys
    FAVORITES_KEY: 'weeklyai_favorites',
    SWIPED_KEY: 'weeklyai_swiped',
    SWIPED_EXPIRY_DAYS: 7,

    // Industry leaders category order
    LEADERS_CATEGORY_ORDER: [
        '通用大模型',
        '中国大模型',
        '搜索引擎',
        '写作助手',
        '图像生成',
        '视频生成',
        '语音合成',
        '代码开发',
        '开发者工具',
        'AI角色/伴侣'
    ],

    // Reset UI state
    resetUI() {
        this.ui.currentPage = 1;
        this.ui.currentSort = 'score';
        this.ui.currentTypeFilter = 'all';
    },

    // Update cache
    updateCache(key, data) {
        if (this.cache.hasOwnProperty(key)) {
            this.cache[key] = data;
        }
    }
};

// Freeze to prevent accidental modifications to structure
Object.freeze(AppState.LEADERS_CATEGORY_ORDER);

// Export for ES modules (if used) or attach to window for script tags
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppState;
} else {
    window.AppState = AppState;
}
