/**
 * WeeklyAI - API Client
 * Centralized API calls with error handling
 */

const API = {
    /**
     * Fetch with timeout and error handling
     */
    async fetch(endpoint, options = {}) {
        const url = `${AppState.API_BASE_URL}${endpoint}`;
        const timeout = options.timeout || 10000;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                console.error(`API timeout: ${endpoint}`);
                throw new Error('Request timeout');
            }
            console.error(`API error: ${endpoint}`, error);
            throw error;
        }
    },

    /**
     * Get trending products
     */
    async getTrending(limit = 5) {
        return this.fetch(`/products/trending?limit=${limit}`);
    },

    /**
     * Get weekly top products
     */
    async getWeeklyTop(limit = 0) {
        return this.fetch(`/products/weekly-top?limit=${limit}`);
    },

    /**
     * Get dark horse products (4-5 score)
     */
    async getDarkHorses(limit = 10, minIndex = 4) {
        return this.fetch(`/products/dark-horses?limit=${limit}&min_index=${minIndex}`);
    },

    /**
     * Get rising stars (2-3 score)
     */
    async getRisingStars(limit = 20) {
        return this.fetch(`/products/rising-stars?limit=${limit}`);
    },

    /**
     * Get today's picks
     */
    async getTodayPicks(limit = 10, hours = 48) {
        return this.fetch(`/products/today?limit=${limit}&hours=${hours}`);
    },

    /**
     * Get product by ID
     */
    async getProduct(productId) {
        return this.fetch(`/products/${encodeURIComponent(productId)}`);
    },

    /**
     * Search products
     */
    async search(keyword, options = {}) {
        const params = new URLSearchParams({
            q: keyword,
            categories: options.categories || '',
            type: options.type || 'all',
            sort: options.sort || 'trending',
            page: options.page || 1,
            limit: options.limit || 15
        });
        return this.fetch(`/search?${params}`);
    },

    /**
     * Get blogs/news
     */
    async getBlogs(limit = 30, source = '') {
        const params = new URLSearchParams({ limit });
        if (source) params.append('source', source);
        return this.fetch(`/products/blogs?${params}`);
    },

    /**
     * Get industry leaders
     */
    async getIndustryLeaders() {
        return this.fetch('/products/industry-leaders');
    },

    /**
     * Get last updated timestamp
     */
    async getLastUpdated() {
        return this.fetch('/products/last-updated');
    },

    /**
     * Get related products
     */
    async getRelated(productId, limit = 6) {
        return this.fetch(`/products/${encodeURIComponent(productId)}/related?limit=${limit}`);
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
} else {
    window.API = API;
}
