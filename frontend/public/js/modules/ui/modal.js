/**
 * WeeklyAI - Product Modal
 * Modal dialog for product details
 */

const Modal = {
    isOpen: false,
    previousFocus: null,

    init() {
        const modal = document.getElementById('productModal');
        const closeBtn = document.getElementById('modalClose');

        if (!modal) return;

        // Close button
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('modal-overlay')) {
                this.close();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    },

    open(product) {
        const modal = document.getElementById('productModal');
        const content = document.getElementById('modalContent');

        if (!modal || !content) return;

        // Save current focus for restoration
        this.previousFocus = document.activeElement;

        // Build modal content
        const name = Utils.escapeHtml(product.name || 'Unknown');
        const description = Utils.escapeHtml(product.description || '');
        const website = product.website || '#';
        const score = product.dark_horse_index || 0;
        const funding = product.funding_total;
        const whyMatters = product.why_matters;
        const latestNews = product.latest_news;
        const region = product.region || '';
        const categories = product.categories || [];
        const isHardware = Utils.isHardware(product);

        content.innerHTML = `
            <div class="modal-header">
                <div class="modal-logo">
                    ${Cards.buildLogoMarkup(product)}
                </div>
                <div class="modal-title-section">
                    <h2 class="modal-title">${name}</h2>
                    <div class="modal-badges">
                        ${Utils.getScoreBadge(score)}
                        ${isHardware ? '<span class="badge badge--hardware">🔧 硬件</span>' : ''}
                        ${region ? `<span class="badge badge--region">${region}</span>` : ''}
                    </div>
                </div>
            </div>

            <div class="modal-body">
                <p class="modal-description">${description}</p>

                ${whyMatters ? `
                    <div class="modal-section">
                        <h4>💡 为什么重要</h4>
                        <p>${Utils.escapeHtml(whyMatters)}</p>
                    </div>
                ` : ''}

                ${funding ? `
                    <div class="modal-section">
                        <h4>💰 融资信息</h4>
                        <p>${Utils.escapeHtml(funding)}</p>
                    </div>
                ` : ''}

                ${latestNews ? `
                    <div class="modal-section">
                        <h4>📰 最新动态</h4>
                        <p>${Utils.escapeHtml(latestNews)}</p>
                    </div>
                ` : ''}

                ${categories.length > 0 ? `
                    <div class="modal-tags">
                        ${categories.map(cat =>
                            `<span class="modal-tag">${Utils.escapeHtml(cat)}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>

            <div class="modal-footer">
                <a href="${website}" target="_blank" class="modal-btn modal-btn--primary">
                    访问官网 →
                </a>
                <button class="modal-btn modal-btn--secondary favorite-modal-btn"
                    data-product-key="${Utils.getProductKey(product)}">
                    ${Favorites.isFavorite(Utils.getProductKey(product)) ? '❤️ 已收藏' : '🤍 收藏'}
                </button>
            </div>
        `;

        // Favorite button in modal
        const favBtn = content.querySelector('.favorite-modal-btn');
        if (favBtn) {
            favBtn.addEventListener('click', () => {
                Favorites.toggle(product);
                const isFav = Favorites.isFavorite(Utils.getProductKey(product));
                favBtn.innerHTML = isFav ? '❤️ 已收藏' : '🤍 收藏';
            });
        }

        // Show modal
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        this.isOpen = true;

        // Focus trap - focus first focusable element
        const firstFocusable = content.querySelector('a, button, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    },

    close() {
        const modal = document.getElementById('productModal');
        if (!modal) return;

        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        this.isOpen = false;

        // Restore body scroll
        document.body.style.overflow = '';

        // Restore focus
        if (this.previousFocus) {
            this.previousFocus.focus();
        }
    },

    toggle(product) {
        if (this.isOpen) {
            this.close();
        } else {
            this.open(product);
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Modal;
} else {
    window.Modal = Modal;
}
