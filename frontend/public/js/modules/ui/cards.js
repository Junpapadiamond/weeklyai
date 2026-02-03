/**
 * WeeklyAI - Product Cards
 * Card rendering for different contexts
 */

const Cards = {
    /**
     * Build logo markup with fallback
     */
    buildLogoMarkup(product) {
        const name = Utils.escapeHtml(product.name || 'Product');
        const logoUrl = product.logo_url || product.logo;
        const faviconUrl = Utils.getFaviconUrl(product.website);
        const initial = name.charAt(0).toUpperCase();

        if (logoUrl) {
            return `<img src="${logoUrl}" alt="${name}"
                onerror="this.onerror=null; this.src='${faviconUrl || ''}'; if(!this.src) this.outerHTML='<div class=\\'product-logo-placeholder\\'>${initial}</div>'"
                loading="lazy" width="48" height="48">`;
        } else if (faviconUrl) {
            return `<img src="${faviconUrl}" alt="${name}"
                onerror="this.onerror=null; this.outerHTML='<div class=\\'product-logo-placeholder\\'>${initial}</div>'"
                loading="lazy" width="48" height="48">`;
        }
        return `<div class="product-logo-placeholder">${initial}</div>`;
    },

    /**
     * Create standard product card
     */
    createProductCard(product) {
        const name = Utils.escapeHtml(product.name || 'Unknown');
        const description = Utils.escapeHtml(Utils.truncate(product.description, 100) || '');
        const website = product.website || '#';
        const categories = product.categories || [];
        const score = product.dark_horse_index || 0;

        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <div class="product-logo">
                ${this.buildLogoMarkup(product)}
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${name}</h3>
                    ${Utils.getScoreBadge(score)}
                </div>
                <p class="product-description">${description}</p>
                <div class="product-tags">
                    ${categories.slice(0, 3).map(cat =>
                        `<span class="product-tag">${Utils.escapeHtml(cat)}</span>`
                    ).join('')}
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            window.open(website, '_blank');
        });

        return card;
    },

    /**
     * Create dark horse card (featured products)
     */
    createDarkHorseCard(product) {
        const name = Utils.escapeHtml(product.name || 'Unknown');
        const description = Utils.escapeHtml(Utils.truncate(product.description, 120) || '');
        const website = product.website || '#';
        const score = product.dark_horse_index || 0;
        const funding = product.funding_total;
        const region = product.region || '';
        const whyMatters = product.why_matters;
        const latestNews = product.latest_news;
        const isHardware = Utils.isHardware(product);

        // Star rating display
        const stars = '★'.repeat(score) + '☆'.repeat(5 - score);

        const card = document.createElement('div');
        card.className = 'darkhorse-card';
        card.innerHTML = `
            <div class="darkhorse-header">
                <div class="darkhorse-logo">
                    ${this.buildLogoMarkup(product)}
                </div>
                <div class="darkhorse-title">
                    <h3>${name}</h3>
                    <div class="darkhorse-rating">${stars}</div>
                </div>
            </div>
            <p class="darkhorse-desc">${description}</p>
            ${whyMatters ? `<p class="darkhorse-why">${Utils.escapeHtml(whyMatters)}</p>` : ''}
            <div class="darkhorse-meta">
                ${funding ? `<span class="meta-funding">💰 ${Utils.escapeHtml(funding)}</span>` : ''}
                ${isHardware ? '<span class="meta-hardware">🔧 硬件</span>' : ''}
                ${region ? `<span class="meta-region">${region}</span>` : ''}
            </div>
            ${latestNews ? `<p class="darkhorse-news">📰 ${Utils.escapeHtml(latestNews)}</p>` : ''}
        `;

        card.addEventListener('click', () => {
            window.open(website, '_blank');
        });

        return card;
    },

    /**
     * Create product card with favorite button
     */
    createProductCardWithFavorite(product) {
        const name = Utils.escapeHtml(product.name || 'Unknown');
        const description = Utils.escapeHtml(Utils.truncate(product.description, 100) || '');
        const website = product.website || '#';
        const score = product.dark_horse_index || 0;
        const funding = product.funding_total;
        const whyMatters = product.why_matters;
        const isHardware = Utils.isHardware(product);
        const productKey = Utils.getProductKey(product);
        const isFavorite = Favorites.isFavorite(productKey);

        const card = document.createElement('div');
        card.className = 'product-card product-card--with-favorite';
        card.innerHTML = `
            <div class="product-card-header">
                <div class="product-logo">
                    ${this.buildLogoMarkup(product)}
                </div>
                <button class="favorite-btn ${isFavorite ? 'is-favorite' : ''}"
                    data-product-key="${productKey}"
                    aria-label="${isFavorite ? '从收藏移除' : '添加到收藏'}">
                    ${isFavorite ? '❤️' : '🤍'}
                </button>
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${name}</h3>
                    ${Utils.getScoreBadge(score)}
                </div>
                <p class="product-description">${description}</p>
                ${whyMatters ? `<p class="product-why">${Utils.escapeHtml(Utils.truncate(whyMatters, 80))}</p>` : ''}
                <div class="product-meta">
                    ${funding ? `<span class="meta-funding">💰 ${Utils.escapeHtml(funding)}</span>` : ''}
                    ${isHardware ? '<span class="meta-tag">🔧 硬件</span>' : '<span class="meta-tag">💻 软件</span>'}
                </div>
            </div>
        `;

        // Favorite button click
        const favBtn = card.querySelector('.favorite-btn');
        favBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            Favorites.toggle(product);
            const isNowFavorite = Favorites.isFavorite(productKey);
            favBtn.classList.toggle('is-favorite', isNowFavorite);
            favBtn.innerHTML = isNowFavorite ? '❤️' : '🤍';
            favBtn.setAttribute('aria-label', isNowFavorite ? '从收藏移除' : '添加到收藏');
        });

        // Card click opens website
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.favorite-btn')) {
                window.open(website, '_blank');
            }
        });

        return card;
    },

    /**
     * Create swipe card for discovery
     */
    createSwipeCard(product, position) {
        const name = Utils.escapeHtml(product.name || 'Unknown');
        const description = Utils.cleanDescription(product.description || '');
        const truncatedDesc = Utils.truncate(description, 150);
        const website = product.website || '#';
        const source = product.source;
        const isNew = Utils.isRecentProduct(product);
        const whyMatters = product.why_matters;
        const funding = product.funding_total;
        const latestNews = product.latest_news;

        const card = document.createElement('div');
        card.className = `swipe-card ${position === 0 ? 'active' : ''}`;
        card.style.zIndex = 10 - position;
        card.dataset.productKey = Utils.getProductKey(product);

        // Check for video content
        const videoPreview = this.getVideoPreview(product);

        card.innerHTML = `
            <div class="swipe-card-content">
                <div class="swipe-card-header">
                    <div class="swipe-card-logo">
                        ${this.buildLogoMarkup(product)}
                    </div>
                    <div class="swipe-card-title">
                        <h3>${name}</h3>
                        ${Utils.getSourceBadge(source, isNew)}
                    </div>
                </div>
                <p class="swipe-card-desc">${Utils.escapeHtml(truncatedDesc)}</p>
                ${videoPreview}
                <div class="swipe-card-highlights">
                    ${whyMatters ? `<p class="highlight-why">💡 ${Utils.escapeHtml(Utils.truncate(whyMatters, 100))}</p>` : ''}
                    ${funding ? `<p class="highlight-funding">💰 ${Utils.escapeHtml(funding)}</p>` : ''}
                    ${latestNews ? `<p class="highlight-news">📰 ${Utils.escapeHtml(Utils.truncate(latestNews, 80))}</p>` : ''}
                </div>
                <a href="${website}" target="_blank" class="swipe-card-link" onclick="event.stopPropagation()">
                    了解更多 →
                </a>
            </div>
        `;

        return card;
    },

    /**
     * Get video preview if available
     */
    getVideoPreview(product) {
        const videoUrl = product.video_url || product.demo_video;
        if (!videoUrl) return '';

        // Extract YouTube thumbnail if YouTube URL
        const ytMatch = videoUrl.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&]+)/);
        if (ytMatch) {
            const videoId = ytMatch[1];
            return `
                <div class="swipe-card-video">
                    <img src="https://img.youtube.com/vi/${videoId}/mqdefault.jpg"
                        alt="Video preview" loading="lazy" width="280" height="158">
                    <span class="video-play-icon">▶</span>
                </div>
            `;
        }
        return '';
    },

    /**
     * Create leader card (industry leaders section)
     */
    createLeaderCard(product) {
        const name = Utils.escapeHtml(product.name || 'Unknown');
        const description = Utils.escapeHtml(Utils.truncate(product.description, 80) || '');
        const website = product.website || '#';

        const card = document.createElement('div');
        card.className = 'leader-card';
        card.innerHTML = `
            <div class="leader-logo">
                ${this.buildLogoMarkup(product)}
            </div>
            <div class="leader-info">
                <h4 class="leader-name">${name}</h4>
                <p class="leader-desc">${description}</p>
            </div>
        `;

        card.addEventListener('click', () => {
            window.open(website, '_blank');
        });

        return card;
    },

    /**
     * Create blog/news card
     */
    createBlogCard(blog) {
        const title = Utils.escapeHtml(blog.title || blog.name || 'Untitled');
        const description = Utils.escapeHtml(Utils.truncate(blog.description, 120) || '');
        const url = blog.url || blog.website || '#';
        const source = blog.source || '';
        const date = blog.published_at || blog.first_seen || '';

        const card = document.createElement('div');
        card.className = 'blog-card';
        card.innerHTML = `
            <div class="blog-content">
                <h4 class="blog-title">${title}</h4>
                <p class="blog-desc">${description}</p>
                <div class="blog-meta">
                    ${source ? `<span class="blog-source">${Utils.escapeHtml(source)}</span>` : ''}
                    ${date ? `<span class="blog-date">${date.slice(0, 10)}</span>` : ''}
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            window.open(url, '_blank');
        });

        return card;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Cards;
} else {
    window.Cards = Cards;
}
