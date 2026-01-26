/**
 * WeeklyAI - Search Section
 * Product search functionality
 */

const Search = {
    init() {
        this.initSearchInput();
        this.initCategoryTags();
    },

    /**
     * Initialize search input
     */
    initSearchInput() {
        const input = document.getElementById('searchInput');
        const btn = document.getElementById('searchBtn');

        if (input) {
            // Enter key to search
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });

            // Debounced live search (optional - remove if too aggressive)
            // input.addEventListener('input', Utils.debounce(() => {
            //     if (input.value.length >= 2) this.performSearch();
            // }, 500));
        }

        if (btn) {
            btn.addEventListener('click', () => this.performSearch());
        }
    },

    /**
     * Initialize category filter tags
     */
    initCategoryTags() {
        const container = document.getElementById('categoryTags');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const tag = e.target.closest('.category-tag');
            if (!tag) return;

            tag.classList.toggle('active');

            if (tag.classList.contains('active')) {
                AppState.ui.selectedCategories.add(tag.dataset.category);
            } else {
                AppState.ui.selectedCategories.delete(tag.dataset.category);
            }

            // Re-search if we have a query
            const input = document.getElementById('searchInput');
            if (input?.value) {
                this.performSearch();
            }
        });
    },

    /**
     * Perform search
     */
    async performSearch() {
        const input = document.getElementById('searchInput');
        const keyword = input?.value?.trim() || '';

        if (!keyword) return;

        // Switch to search section
        Navigation.switchSection('search');

        const resultsContainer = document.getElementById('searchResults');
        const infoContainer = document.getElementById('searchResultInfo');

        if (resultsContainer) {
            Animations.showSkeleton(resultsContainer, 4);
        }

        try {
            const categories = Array.from(AppState.ui.selectedCategories).join(',');

            const response = await API.search(keyword, {
                categories,
                type: 'all',
                sort: 'trending',
                page: 1,
                limit: 30
            });

            if (response.success) {
                this.renderResults(response.data.products || response.data, response.data.total || response.data.length, keyword);
            } else {
                this.showError(resultsContainer, keyword);
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.showError(resultsContainer, keyword);
        }
    },

    /**
     * Render search results
     */
    renderResults(products, total, keyword) {
        const container = document.getElementById('searchResults');
        const info = document.getElementById('searchResultInfo');

        if (info) {
            info.innerHTML = `
                <span class="search-keyword">"${Utils.escapeHtml(keyword)}"</span>
                <span class="search-count">找到 ${total} 个结果</span>
            `;
        }

        if (!container) return;

        container.innerHTML = '';

        if (products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>😕 没有找到 "${Utils.escapeHtml(keyword)}" 相关的产品</p>
                    <p class="hint">试试其他关键词或减少筛选条件</p>
                </div>
            `;
            return;
        }

        products.forEach(product => {
            const card = Cards.createProductCardWithFavorite(product);
            container.appendChild(card);
        });

        Animations.animateCards(container);
    },

    /**
     * Show error state
     */
    showError(container, keyword) {
        if (!container) return;

        container.innerHTML = `
            <div class="error-state">
                <p>😕 搜索失败</p>
                <button class="btn btn--secondary" onclick="Search.performSearch()">重试</button>
            </div>
        `;
    },

    /**
     * Clear search
     */
    clear() {
        const input = document.getElementById('searchInput');
        if (input) input.value = '';

        AppState.ui.selectedCategories.clear();

        document.querySelectorAll('.category-tag').forEach(tag => {
            tag.classList.remove('active');
        });
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Search;
} else {
    window.Search = Search;
}
