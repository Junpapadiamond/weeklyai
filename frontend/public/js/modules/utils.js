/**
 * WeeklyAI - Utility Functions
 * Shared helper functions used across modules
 */

const Utils = {
    /**
     * Debounce function execution
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function execution
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Shuffle array (Fisher-Yates)
     */
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    },

    /**
     * Parse funding string to number (in millions)
     */
    parseFunding(funding) {
        if (!funding) return 0;
        const str = String(funding).toLowerCase().replace(/,/g, '');

        // Handle billions
        const billionMatch = str.match(/([\d.]+)\s*b/);
        if (billionMatch) return parseFloat(billionMatch[1]) * 1000;

        // Handle millions
        const millionMatch = str.match(/([\d.]+)\s*m/);
        if (millionMatch) return parseFloat(millionMatch[1]);

        // Handle plain numbers (assume millions if > 1000)
        const numMatch = str.match(/\$?([\d.]+)/);
        if (numMatch) {
            const num = parseFloat(numMatch[1]);
            return num > 1000 ? num / 1000000 : num;
        }

        return 0;
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Clean description text (remove technical noise)
     */
    cleanDescription(desc) {
        if (!desc) return '';
        return desc
            .replace(/^(An?\s+)?(AI[- ]powered\s+)?/i, '')
            .replace(/\s*\([^)]*\)\s*/g, ' ')
            .replace(/https?:\/\/\S+/g, '')
            .trim();
    },

    /**
     * Truncate text with ellipsis
     */
    truncate(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    },

    /**
     * Check if product is recent (within 7 days)
     */
    isRecentProduct(product) {
        const dateStr = product.discovered_at || product.first_seen;
        if (!dateStr) return false;
        const productDate = new Date(dateStr);
        const now = new Date();
        const diffDays = (now - productDate) / (1000 * 60 * 60 * 24);
        return diffDays <= 7;
    },

    /**
     * Check if product is hardware
     */
    isHardware(product) {
        const categories = product.categories || [];
        const description = (product.description || '').toLowerCase();
        return categories.includes('hardware') ||
            product.category === 'hardware' ||
            product.is_hardware === true ||
            description.includes('chip') ||
            description.includes('robot') ||
            description.includes('device');
    },

    /**
     * Get favicon URL for a domain
     */
    getFaviconUrl(website) {
        if (!website) return null;
        try {
            const domain = new URL(website).hostname;
            return `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
        } catch {
            return null;
        }
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Generate unique key for product
     */
    getProductKey(product) {
        return product.website || product.name || product.slug || Math.random().toString(36);
    },

    /**
     * Get score badge HTML
     */
    getScoreBadge(score) {
        if (!score || score < 2) return '';
        const label = score >= 4 ? '黑马' : '潜力';
        return `<span class="score-badge score-badge--${score}">${score}分 ${label}</span>`;
    },

    /**
     * Get source badge HTML
     */
    getSourceBadge(source, isNew = false) {
        if (isNew) {
            return '<span class="source-badge source-badge--new">🆕 New</span>';
        }
        const badges = {
            'producthunt': '<span class="source-badge source-badge--ph">PH</span>',
            'hackernews': '<span class="source-badge source-badge--hn">HN</span>',
            'hn': '<span class="source-badge source-badge--hn">HN</span>',
            'news': '<span class="source-badge source-badge--news">News</span>',
        };
        const sourceLower = (source || '').toLowerCase();
        return badges[sourceLower] || '';
    },

    /**
     * Safe JSON parse
     */
    safeJsonParse(str, fallback = null) {
        try {
            return JSON.parse(str);
        } catch {
            return fallback;
        }
    },

    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
} else {
    window.Utils = Utils;
}
