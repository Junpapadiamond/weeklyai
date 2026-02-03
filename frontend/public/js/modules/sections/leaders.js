/**
 * WeeklyAI - Industry Leaders Section
 * Well-known AI products reference list
 */

const Leaders = {
    init() {
        this.initFilters();
        this.loadLeaders();
    },

    /**
     * Initialize category filters
     */
    initFilters() {
        const container = document.getElementById('leadersFilters');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const btn = e.target.closest('.filter-btn');
            if (!btn) return;

            container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            AppState.ui.leadersActiveFilter = btn.dataset.category || 'all';
            this.render();
        });
    },

    /**
     * Load industry leaders data
     */
    async loadLeaders() {
        const container = document.getElementById('leadersGrid');
        if (!container) return;

        Animations.showSkeleton(container, 6);

        try {
            const response = await API.getIndustryLeaders();

            if (response.success && response.data) {
                AppState.cache.leaderCategories = response.data.categories || response.data;
                this.buildFilters();
                this.render();
            } else {
                this.showError(container);
            }
        } catch (error) {
            console.error('Failed to load industry leaders:', error);
            this.showError(container);
        }
    },

    /**
     * Build filter buttons from categories
     */
    buildFilters() {
        const container = document.getElementById('leadersFilters');
        if (!container || !AppState.cache.leaderCategories) return;

        const categories = Object.keys(AppState.cache.leaderCategories);

        // Sort by predefined order
        categories.sort((a, b) => {
            const indexA = AppState.LEADERS_CATEGORY_ORDER.indexOf(a);
            const indexB = AppState.LEADERS_CATEGORY_ORDER.indexOf(b);
            if (indexA === -1 && indexB === -1) return a.localeCompare(b);
            if (indexA === -1) return 1;
            if (indexB === -1) return -1;
            return indexA - indexB;
        });

        container.innerHTML = `
            <button class="filter-btn active" data-category="all">全部</button>
            ${categories.map(cat =>
                `<button class="filter-btn" data-category="${Utils.escapeHtml(cat)}">${Utils.escapeHtml(cat)}</button>`
            ).join('')}
        `;
    },

    /**
     * Render leaders grid
     */
    render() {
        const container = document.getElementById('leadersGrid');
        if (!container || !AppState.cache.leaderCategories) return;

        container.innerHTML = '';

        const filter = AppState.ui.leadersActiveFilter;
        const categories = AppState.cache.leaderCategories;

        if (filter === 'all') {
            // Show all categories
            const sortedCategories = Object.keys(categories).sort((a, b) => {
                const indexA = AppState.LEADERS_CATEGORY_ORDER.indexOf(a);
                const indexB = AppState.LEADERS_CATEGORY_ORDER.indexOf(b);
                if (indexA === -1 && indexB === -1) return a.localeCompare(b);
                if (indexA === -1) return 1;
                if (indexB === -1) return -1;
                return indexA - indexB;
            });

            sortedCategories.forEach(categoryName => {
                const products = categories[categoryName];
                if (!products || products.length === 0) return;

                const section = document.createElement('div');
                section.className = 'leaders-category';
                section.innerHTML = `
                    <h3 class="leaders-category-title">${Utils.escapeHtml(categoryName)}</h3>
                    <div class="leaders-category-grid"></div>
                `;

                const grid = section.querySelector('.leaders-category-grid');
                products.forEach(product => {
                    const card = Cards.createLeaderCard(product);
                    grid.appendChild(card);
                });

                container.appendChild(section);
            });
        } else {
            // Show single category
            const products = categories[filter];
            if (!products || products.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <p>该分类暂无产品</p>
                    </div>
                `;
                return;
            }

            const grid = document.createElement('div');
            grid.className = 'leaders-single-grid';

            products.forEach(product => {
                const card = Cards.createLeaderCard(product);
                grid.appendChild(card);
            });

            container.appendChild(grid);
        }

        Animations.animateLeaderCards(container);
    },

    /**
     * Show error state
     */
    showError(container) {
        container.innerHTML = `
            <div class="error-state">
                <p>😕 加载失败</p>
                <button class="btn btn--secondary" onclick="Leaders.loadLeaders()">重试</button>
            </div>
        `;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Leaders;
} else {
    window.Leaders = Leaders;
}
