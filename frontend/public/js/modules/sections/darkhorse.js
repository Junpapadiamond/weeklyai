/**
 * WeeklyAI - Dark Horse Section
 * Weekly black horse products (4-5 score)
 */

const DarkHorse = {
    init() {
        this.initFilters();
        this.loadProducts();
    },

    /**
     * Initialize hardware/software filters
     */
    initFilters() {
        const filterBtns = document.querySelectorAll('.darkhorse-filters .filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                AppState.ui.darkHorseFilter = btn.dataset.type || 'all';
                this.render();
            });
        });
    },

    /**
     * Load dark horse products
     */
    async loadProducts() {
        const container = document.getElementById('darkhorseProducts');
        const section = document.getElementById('darkhorseSection');

        if (!container) return;

        Animations.showSkeleton(container, 3);

        try {
            const response = await API.getDarkHorses(10, 4);

            if (response.success && response.data.length > 0) {
                AppState.cache.darkHorses = response.data;
                AppState.ui.hasDarkhorseData = true;
                this.render();
            } else {
                AppState.ui.hasDarkhorseData = false;
                if (section) section.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to load dark horse products:', error);
            AppState.ui.hasDarkhorseData = false;
            if (section) section.style.display = 'none';
        }
    },

    /**
     * Filter products by type
     */
    filterByType(products, type) {
        if (type === 'all') return products;

        return products.filter(p => {
            const isHardware = Utils.isHardware(p);
            return type === 'hardware' ? isHardware : !isHardware;
        });
    },

    /**
     * Render dark horse products
     */
    render() {
        const container = document.getElementById('darkhorseProducts');
        if (!container) return;

        const filtered = this.filterByType(
            AppState.cache.darkHorses,
            AppState.ui.darkHorseFilter
        );

        container.innerHTML = '';

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>暂无符合条件的黑马产品</p>
                </div>
            `;
            return;
        }

        filtered.forEach(product => {
            const card = Cards.createDarkHorseCard(product);
            container.appendChild(card);
        });

        Animations.animateDarkHorseCards(container);
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DarkHorse;
} else {
    window.DarkHorse = DarkHorse;
}
