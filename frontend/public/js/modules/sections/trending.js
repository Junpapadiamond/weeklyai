/**
 * WeeklyAI - Trending Section
 * More recommendations with filtering and pagination
 */

const Trending = {
    init() {
        this.initSortFilter();
        this.initTierTabs();
        this.initLoadMore();
        this.loadProducts();
    },

    /**
     * Initialize sort and filter controls
     */
    initSortFilter() {
        const sortSelect = document.getElementById('sortBy');
        const typeSelect = document.getElementById('typeFilter');

        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                AppState.ui.currentSort = sortSelect.value;
                AppState.ui.currentPage = 1;
                this.applyFiltersAndRender();
            });
        }

        if (typeSelect) {
            typeSelect.addEventListener('change', () => {
                AppState.ui.currentTypeFilter = typeSelect.value;
                AppState.ui.currentPage = 1;
                this.applyFiltersAndRender();
            });
        }
    },

    /**
     * Initialize tier tabs (all/darkhorse/rising)
     */
    initTierTabs() {
        const tabs = document.querySelectorAll('.tier-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                AppState.ui.currentTier = tab.dataset.tier;
                AppState.ui.currentPage = 1;
                this.applyFiltersAndRender();
            });
        });
    },

    /**
     * Initialize load more button
     */
    initLoadMore() {
        const btn = document.getElementById('loadMoreBtn');
        if (btn) {
            btn.addEventListener('click', () => {
                AppState.ui.currentPage++;
                this.applyFiltersAndRender(true);
            });
        }
    },

    /**
     * Load all products
     */
    async loadProducts() {
        const container = document.getElementById('trendingProducts');
        if (!container) return;

        Animations.showSkeleton(container, 6);

        try {
            const response = await API.getWeeklyTop(0); // Get all

            if (response.success) {
                AppState.cache.allProducts = response.data;
                this.applyFiltersAndRender();
            } else {
                this.showError(container);
            }
        } catch (error) {
            console.error('Failed to load trending products:', error);
            this.showError(container);
        }
    },

    /**
     * Apply filters and render products
     */
    applyFiltersAndRender(append = false) {
        let products = [...AppState.cache.allProducts];

        // Filter by tier
        if (AppState.ui.currentTier === 'darkhorse') {
            products = products.filter(p => (p.dark_horse_index || 0) >= 4);
        } else if (AppState.ui.currentTier === 'rising') {
            products = products.filter(p => {
                const score = p.dark_horse_index || 0;
                return score >= 2 && score <= 3;
            });
        }

        // Filter by type
        if (AppState.ui.currentTypeFilter === 'hardware') {
            products = products.filter(p => Utils.isHardware(p));
        } else if (AppState.ui.currentTypeFilter === 'software') {
            products = products.filter(p => !Utils.isHardware(p));
        }

        // Sort
        products = this.sortProducts(products, AppState.ui.currentSort);

        // Paginate
        const pageSize = AppState.PRODUCTS_PER_PAGE;
        const endIndex = AppState.ui.currentPage * pageSize;
        const paginatedProducts = products.slice(0, endIndex);

        // Render
        this.render(paginatedProducts, append);

        // Update load more button
        this.updateLoadMoreButton(products.length, endIndex);
    },

    /**
     * Sort products by criteria
     */
    sortProducts(products, sortBy) {
        const sorted = [...products];

        switch (sortBy) {
            case 'score':
                sorted.sort((a, b) => {
                    const scoreA = a.dark_horse_index || 0;
                    const scoreB = b.dark_horse_index || 0;
                    if (scoreB !== scoreA) return scoreB - scoreA;

                    const fundingA = Utils.parseFunding(a.funding_total);
                    const fundingB = Utils.parseFunding(b.funding_total);
                    return fundingB - fundingA;
                });
                break;

            case 'date':
                sorted.sort((a, b) => {
                    const dateA = a.discovered_at || a.first_seen || '';
                    const dateB = b.discovered_at || b.first_seen || '';
                    return dateB.localeCompare(dateA);
                });
                break;

            case 'funding':
                sorted.sort((a, b) => {
                    const fundingA = Utils.parseFunding(a.funding_total);
                    const fundingB = Utils.parseFunding(b.funding_total);
                    return fundingB - fundingA;
                });
                break;

            default:
                // Default: trending/hot score
                sorted.sort((a, b) => {
                    const scoreA = a.hot_score || a.final_score || a.trending_score || 0;
                    const scoreB = b.hot_score || b.final_score || b.trending_score || 0;
                    return scoreB - scoreA;
                });
        }

        return sorted;
    },

    /**
     * Render products to grid
     */
    render(products, append = false) {
        const container = document.getElementById('trendingProducts');
        if (!container) return;

        if (!append) {
            container.innerHTML = '';
        }

        if (products.length === 0 && !append) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>没有找到符合条件的产品</p>
                </div>
            `;
            return;
        }

        const startIndex = append ? container.children.length : 0;
        const newProducts = products.slice(startIndex);

        newProducts.forEach(product => {
            const card = Cards.createProductCardWithFavorite(product);
            container.appendChild(card);
        });

        Animations.animateCards(container);
    },

    /**
     * Update load more button visibility
     */
    updateLoadMoreButton(total, shown) {
        const btn = document.getElementById('loadMoreBtn');
        const container = document.getElementById('loadMoreContainer');

        if (btn && container) {
            if (shown >= total) {
                container.style.display = 'none';
            } else {
                container.style.display = 'block';
                btn.textContent = `加载更多 (${total - shown} 剩余)`;
            }
        }
    },

    /**
     * Show error state
     */
    showError(container) {
        container.innerHTML = `
            <div class="error-state">
                <p>😕 加载失败</p>
                <button class="btn btn--secondary" onclick="Trending.loadProducts()">重试</button>
            </div>
        `;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Trending;
} else {
    window.Trending = Trending;
}
