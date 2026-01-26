/**
 * WeeklyAI - Favorites
 * Favorite products management with localStorage
 */

const Favorites = {
    _saveTimeout: null,
    _pendingData: null,

    init() {
        this.updateCount();
        this.initPanel();
        this.initToggleButton();
    },

    /**
     * Get all favorites from localStorage
     */
    getAll() {
        const data = localStorage.getItem(AppState.FAVORITES_KEY);
        return Utils.safeJsonParse(data, []);
    },

    /**
     * Save favorites to localStorage (debounced)
     */
    save(favorites) {
        this._pendingData = favorites;

        if (this._saveTimeout) {
            clearTimeout(this._saveTimeout);
        }

        this._saveTimeout = setTimeout(() => {
            try {
                localStorage.setItem(AppState.FAVORITES_KEY, JSON.stringify(this._pendingData));
            } catch (e) {
                console.error('Failed to save favorites:', e);
            }
        }, 500);
    },

    /**
     * Check if product is favorited
     */
    isFavorite(productKey) {
        const favorites = this.getAll();
        return favorites.some(f => f.key === productKey);
    },

    /**
     * Add product to favorites
     */
    add(product) {
        const favorites = this.getAll();
        const key = Utils.getProductKey(product);

        if (this.isFavorite(key)) return;

        favorites.push({
            key,
            name: product.name,
            logo_url: product.logo_url || product.logo,
            website: product.website,
            categories: product.categories || [],
            addedAt: new Date().toISOString()
        });

        this.save(favorites);
        this.updateCount();
    },

    /**
     * Remove product from favorites
     */
    remove(productKey) {
        let favorites = this.getAll();
        favorites = favorites.filter(f => f.key !== productKey);
        this.save(favorites);
        this.updateCount();
    },

    /**
     * Toggle favorite status
     */
    toggle(product) {
        const key = Utils.getProductKey(product);
        if (this.isFavorite(key)) {
            this.remove(key);
            return false;
        } else {
            this.add(product);
            return true;
        }
    },

    /**
     * Update favorites count badge
     */
    updateCount() {
        const count = this.getAll().length;
        const badge = document.getElementById('favoritesCount');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    },

    /**
     * Initialize favorites panel
     */
    initPanel() {
        const closeBtn = document.getElementById('favoritesClose');
        const panel = document.getElementById('favoritesPanel');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel?.classList.contains('is-open')) {
                this.closePanel();
            }
        });

        // Close on click outside
        if (panel) {
            panel.addEventListener('click', (e) => {
                if (e.target === panel) {
                    this.closePanel();
                }
            });
        }
    },

    /**
     * Initialize toggle button
     */
    initToggleButton() {
        const btn = document.getElementById('showFavoritesBtn');
        if (btn) {
            btn.addEventListener('click', () => this.togglePanel());
        }
    },

    /**
     * Open favorites panel
     */
    openPanel() {
        const panel = document.getElementById('favoritesPanel');
        if (!panel) return;

        this.renderList();
        panel.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    },

    /**
     * Close favorites panel
     */
    closePanel() {
        const panel = document.getElementById('favoritesPanel');
        if (!panel) return;

        panel.classList.remove('is-open');
        document.body.style.overflow = '';
    },

    /**
     * Toggle favorites panel
     */
    togglePanel() {
        const panel = document.getElementById('favoritesPanel');
        if (panel?.classList.contains('is-open')) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    },

    /**
     * Render favorites list
     */
    renderList() {
        const list = document.getElementById('favoritesList');
        if (!list) return;

        const favorites = this.getAll();

        if (favorites.length === 0) {
            list.innerHTML = `
                <div class="favorites-empty">
                    <p>还没有收藏任何产品</p>
                    <p class="favorites-empty-hint">在发现页面右滑或点击 ❤️ 收藏喜欢的产品</p>
                </div>
            `;
            return;
        }

        list.innerHTML = favorites.map(fav => `
            <div class="favorite-item" data-key="${fav.key}">
                <div class="favorite-logo">
                    <img src="${fav.logo_url || Utils.getFaviconUrl(fav.website) || ''}"
                        alt="${Utils.escapeHtml(fav.name)}"
                        onerror="this.outerHTML='<div class=\\'favorite-logo-placeholder\\'>${(fav.name || 'P').charAt(0)}</div>'"
                        loading="lazy" width="40" height="40">
                </div>
                <div class="favorite-info">
                    <h4 class="favorite-name">${Utils.escapeHtml(fav.name)}</h4>
                    <div class="favorite-tags">
                        ${(fav.categories || []).slice(0, 2).map(cat =>
                            `<span class="favorite-tag">${Utils.escapeHtml(cat)}</span>`
                        ).join('')}
                    </div>
                </div>
                <div class="favorite-actions">
                    <a href="${fav.website}" target="_blank" class="favorite-link" title="访问">🔗</a>
                    <button class="favorite-remove" data-key="${fav.key}" title="移除">✕</button>
                </div>
            </div>
        `).join('');

        // Remove button handlers
        list.querySelectorAll('.favorite-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const key = btn.dataset.key;
                this.remove(key);
                this.renderList();
                this.updateAllFavoriteButtons();
            });
        });

        // Click to open website
        list.querySelectorAll('.favorite-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.favorite-actions')) {
                    const fav = favorites.find(f => f.key === item.dataset.key);
                    if (fav?.website) {
                        window.open(fav.website, '_blank');
                    }
                }
            });
        });
    },

    /**
     * Update all favorite buttons on the page
     */
    updateAllFavoriteButtons() {
        document.querySelectorAll('.favorite-btn').forEach(btn => {
            const key = btn.dataset.productKey;
            const isFav = this.isFavorite(key);
            btn.classList.toggle('is-favorite', isFav);
            btn.innerHTML = isFav ? '❤️' : '🤍';
        });
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Favorites;
} else {
    window.Favorites = Favorites;
}
