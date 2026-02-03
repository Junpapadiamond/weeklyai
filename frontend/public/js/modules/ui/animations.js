/**
 * WeeklyAI - Animations
 * Card animations and visual effects
 */

const Animations = {
    // Debounced icon refresh to prevent multiple calls
    _iconRefreshTimeout: null,

    /**
     * Refresh Lucide icons (debounced)
     */
    refreshIcons() {
        if (this._iconRefreshTimeout) {
            clearTimeout(this._iconRefreshTimeout);
        }
        this._iconRefreshTimeout = setTimeout(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }, 50);
    },

    /**
     * Animate cards with staggered fade-in
     */
    animateCards(container, selector = '.product-card') {
        if (AppState.prefersReducedMotion) {
            this.refreshIcons();
            return;
        }

        const cards = container.querySelectorAll(selector);
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 80);
        });

        this.refreshIcons();
    },

    /**
     * Animate dark horse cards
     */
    animateDarkHorseCards(container) {
        this.animateCards(container, '.darkhorse-card');
    },

    /**
     * Animate list items with slide-in
     */
    animateListItems(container, selector = '.blog-card') {
        if (AppState.prefersReducedMotion) {
            this.refreshIcons();
            return;
        }

        const items = container.querySelectorAll(selector);
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';

            setTimeout(() => {
                item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, index * 60);
        });

        this.refreshIcons();
    },

    /**
     * Animate leader cards
     */
    animateLeaderCards(container) {
        this.animateCards(container, '.leader-card');
    },

    /**
     * Fade in element
     */
    fadeIn(element, duration = 300) {
        if (AppState.prefersReducedMotion) {
            element.style.opacity = '1';
            return;
        }

        element.style.opacity = '0';
        element.style.transition = `opacity ${duration}ms ease`;

        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
    },

    /**
     * Fade out element
     */
    fadeOut(element, duration = 300) {
        return new Promise(resolve => {
            if (AppState.prefersReducedMotion) {
                element.style.opacity = '0';
                resolve();
                return;
            }

            element.style.transition = `opacity ${duration}ms ease`;
            element.style.opacity = '0';

            setTimeout(resolve, duration);
        });
    },

    /**
     * Slide element
     */
    slide(element, direction, distance = 100) {
        if (AppState.prefersReducedMotion) return;

        const axis = direction === 'left' || direction === 'right' ? 'X' : 'Y';
        const sign = direction === 'left' || direction === 'up' ? -1 : 1;

        element.style.transform = `translate${axis}(${sign * distance}px)`;
        element.style.transition = 'transform 0.3s ease';

        requestAnimationFrame(() => {
            element.style.transform = `translate${axis}(0)`;
        });
    },

    /**
     * Shake element (for errors/invalid actions)
     */
    shake(element) {
        if (AppState.prefersReducedMotion) return;

        element.style.animation = 'shake 0.5s ease';
        element.addEventListener('animationend', () => {
            element.style.animation = '';
        }, { once: true });
    },

    /**
     * Pulse element (for success/attention)
     */
    pulse(element) {
        if (AppState.prefersReducedMotion) return;

        element.style.animation = 'pulse 0.3s ease';
        element.addEventListener('animationend', () => {
            element.style.animation = '';
        }, { once: true });
    },

    /**
     * Initialize hero glow effect
     */
    initHeroGlow() {
        const hero = document.querySelector('.hero');
        if (!hero || AppState.prefersReducedMotion) return;

        hero.addEventListener('mousemove', Utils.throttle((e) => {
            const rect = hero.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            hero.style.setProperty('--mouse-x', `${x}%`);
            hero.style.setProperty('--mouse-y', `${y}%`);
        }, 50));
    },

    /**
     * Loading skeleton show/hide
     */
    showSkeleton(container, count = 3) {
        container.innerHTML = Array(count).fill(`
            <div class="loading-skeleton">
                <div class="skeleton-logo"></div>
                <div class="skeleton-content">
                    <div class="skeleton-title"></div>
                    <div class="skeleton-text"></div>
                    <div class="skeleton-text short"></div>
                </div>
            </div>
        `).join('');
    },

    hideSkeleton(container) {
        const skeletons = container.querySelectorAll('.loading-skeleton');
        skeletons.forEach(s => s.remove());
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Animations;
} else {
    window.Animations = Animations;
}
