/**
 * WeeklyAI - Discovery Section
 * Swipe cards for product discovery
 */

const Discovery = {
    deck: [],
    currentIndex: 0,
    isAnimating: false,

    init() {
        this.initButtons();
        this.initFilters();
        this.loadProducts();
    },

    /**
     * Initialize swipe buttons
     */
    initButtons() {
        const likeBtn = document.getElementById('swipeLike');
        const nopeBtn = document.getElementById('swipeNope');

        if (likeBtn) {
            likeBtn.addEventListener('click', () => this.handleSwipe('right'));
        }
        if (nopeBtn) {
            nopeBtn.addEventListener('click', () => this.handleSwipe('left'));
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (Navigation.getActiveSection() !== 'discover') return;
            if (e.key === 'ArrowLeft') this.handleSwipe('left');
            if (e.key === 'ArrowRight') this.handleSwipe('right');
        });
    },

    /**
     * Initialize category filters
     */
    initFilters() {
        const filterBtns = document.querySelectorAll('.discover-filters .filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                AppState.ui.discoverFilter = btn.dataset.category || 'all';
                this.loadCards();
            });
        });
    },

    /**
     * Load products for discovery
     */
    async loadProducts() {
        try {
            // Load from multiple sources
            const [weeklyRes, darkHorseRes] = await Promise.all([
                API.getWeeklyTop(50),
                API.getDarkHorses(20, 4)
            ]);

            let products = [];

            if (weeklyRes.success) {
                products = [...weeklyRes.data];
            }

            if (darkHorseRes.success) {
                // Merge dark horses, avoiding duplicates
                const existingKeys = new Set(products.map(p => Utils.getProductKey(p)));
                darkHorseRes.data.forEach(p => {
                    if (!existingKeys.has(Utils.getProductKey(p))) {
                        products.push(p);
                    }
                });
            }

            AppState.cache.discoveryProducts = products;
            this.loadCards();

        } catch (error) {
            console.error('Failed to load discovery products:', error);
            this.showError();
        }
    },

    /**
     * Load cards into the deck
     */
    loadCards() {
        const products = this.filterProducts(AppState.cache.discoveryProducts);
        this.deck = Utils.shuffleArray(products).filter(p => !this.isProductSwiped(p));
        this.currentIndex = 0;
        this.renderStack();
        this.updateStatus();
    },

    /**
     * Filter products by category
     */
    filterProducts(products) {
        const filter = AppState.ui.discoverFilter;
        if (filter === 'all') return products;

        return products.filter(p => {
            const categories = p.categories || [];
            if (filter === 'hardware') return Utils.isHardware(p);
            if (filter === 'software') return !Utils.isHardware(p);
            return categories.includes(filter);
        });
    },

    /**
     * Render the card stack (show top 3 cards)
     */
    renderStack() {
        const stack = document.getElementById('swipeStack');
        if (!stack) return;

        stack.innerHTML = '';

        const cardsToShow = this.deck.slice(this.currentIndex, this.currentIndex + 3);

        if (cardsToShow.length === 0) {
            stack.innerHTML = `
                <div class="swipe-empty">
                    <p>🎉 你已经看完了所有产品！</p>
                    <button class="btn btn--secondary" onclick="Discovery.reset()">重新开始</button>
                </div>
            `;
            return;
        }

        cardsToShow.forEach((product, i) => {
            const card = Cards.createSwipeCard(product, i);
            if (i === 0) {
                this.attachSwipeHandlers(card);
            }
            stack.appendChild(card);
        });

        Animations.refreshIcons();
    },

    /**
     * Attach swipe gesture handlers to card
     */
    attachSwipeHandlers(card) {
        let startX = 0;
        let startY = 0;
        let currentX = 0;
        let isDragging = false;

        const onStart = (e) => {
            if (this.isAnimating) return;
            isDragging = true;
            startX = e.clientX || e.touches?.[0]?.clientX || 0;
            startY = e.clientY || e.touches?.[0]?.clientY || 0;
            card.style.transition = 'none';
        };

        const onMove = (e) => {
            if (!isDragging) return;
            currentX = (e.clientX || e.touches?.[0]?.clientX || 0) - startX;
            const rotation = currentX / 20;

            card.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;

            // Show like/nope indicator
            if (currentX > 50) {
                card.classList.add('swiping-right');
                card.classList.remove('swiping-left');
            } else if (currentX < -50) {
                card.classList.add('swiping-left');
                card.classList.remove('swiping-right');
            } else {
                card.classList.remove('swiping-left', 'swiping-right');
            }
        };

        const onEnd = () => {
            if (!isDragging) return;
            isDragging = false;

            card.style.transition = 'transform 0.3s ease';
            card.classList.remove('swiping-left', 'swiping-right');

            const threshold = 100;

            if (currentX > threshold) {
                this.handleSwipe('right');
            } else if (currentX < -threshold) {
                this.handleSwipe('left');
            } else {
                card.style.transform = '';
            }
        };

        // Mouse events
        card.addEventListener('mousedown', onStart);
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onEnd);

        // Touch events
        card.addEventListener('touchstart', onStart, { passive: true });
        card.addEventListener('touchmove', onMove, { passive: true });
        card.addEventListener('touchend', onEnd);
    },

    /**
     * Handle swipe action
     */
    handleSwipe(direction) {
        if (this.isAnimating || this.currentIndex >= this.deck.length) return;

        const stack = document.getElementById('swipeStack');
        const card = stack?.querySelector('.swipe-card.active');
        if (!card) return;

        this.isAnimating = true;
        const product = this.deck[this.currentIndex];

        // Animate card off screen
        const translateX = direction === 'right' ? 500 : -500;
        const rotation = direction === 'right' ? 30 : -30;

        card.style.transition = 'transform 0.4s ease';
        card.style.transform = `translateX(${translateX}px) rotate(${rotation}deg)`;

        // If right swipe, add to favorites
        if (direction === 'right' && product) {
            Favorites.add(product);
        }

        // Mark as swiped
        if (product) {
            this.markProductSwiped(product);
        }

        // After animation, move to next card
        setTimeout(() => {
            this.currentIndex++;
            this.renderStack();
            this.updateStatus();
            this.isAnimating = false;
        }, 400);
    },

    /**
     * Update status indicator
     */
    updateStatus() {
        const status = document.getElementById('swipeStatus');
        if (!status) return;

        const remaining = this.deck.length - this.currentIndex;
        const total = this.deck.length;
        const viewed = this.currentIndex;

        status.innerHTML = `
            <span class="status-viewed">${viewed} 已看</span>
            <span class="status-remaining">${remaining} 剩余</span>
        `;
    },

    /**
     * Check if product has been swiped
     */
    isProductSwiped(product) {
        const key = Utils.getProductKey(product);
        const swiped = this.getSwipedProducts();
        return swiped.hasOwnProperty(key);
    },

    /**
     * Mark product as swiped
     */
    markProductSwiped(product) {
        const key = Utils.getProductKey(product);
        const swiped = this.getSwipedProducts();
        swiped[key] = Date.now();
        this.saveSwipedProducts(swiped);
    },

    /**
     * Get swiped products from localStorage
     */
    getSwipedProducts() {
        const data = localStorage.getItem(AppState.SWIPED_KEY);
        const swiped = Utils.safeJsonParse(data, {});

        // Clean expired entries
        const now = Date.now();
        const expiryMs = AppState.SWIPED_EXPIRY_DAYS * 24 * 60 * 60 * 1000;
        let cleaned = false;

        Object.keys(swiped).forEach(key => {
            if (now - swiped[key] > expiryMs) {
                delete swiped[key];
                cleaned = true;
            }
        });

        if (cleaned) {
            this.saveSwipedProducts(swiped);
        }

        return swiped;
    },

    // Debounce save
    _swipeSaveTimeout: null,
    _pendingSwipeData: null,

    /**
     * Save swiped products (debounced)
     */
    saveSwipedProducts(data) {
        this._pendingSwipeData = data;

        if (this._swipeSaveTimeout) {
            clearTimeout(this._swipeSaveTimeout);
        }

        this._swipeSaveTimeout = setTimeout(() => {
            try {
                localStorage.setItem(AppState.SWIPED_KEY, JSON.stringify(this._pendingSwipeData));
            } catch (e) {
                console.error('Failed to save swiped products:', e);
            }
        }, 500);
    },

    /**
     * Reset discovery (clear swiped history)
     */
    reset() {
        localStorage.removeItem(AppState.SWIPED_KEY);
        this.loadCards();
    },

    /**
     * Show error state
     */
    showError() {
        const stack = document.getElementById('swipeStack');
        if (!stack) return;

        stack.innerHTML = `
            <div class="swipe-error">
                <p>😕 加载失败</p>
                <button class="btn btn--secondary" onclick="Discovery.loadProducts()">重试</button>
            </div>
        `;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Discovery;
} else {
    window.Discovery = Discovery;
}
