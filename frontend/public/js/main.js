/**
 * WeeklyAI - 主JavaScript文件
 * 处理页面交互和API调用
 */

// API 基础URL
const API_BASE_URL = 'http://localhost:5000/api/v1';
const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// 当前选中的分类
let selectedCategories = new Set();

// 当前显示的section
let hasDarkhorseData = true;

// Sort and filter state
let currentSort = 'score';
let currentTypeFilter = 'all';

// Favorites stored in localStorage
const FAVORITES_KEY = 'weeklyai_favorites';

// All products cache for sorting/filtering
let allProductsCache = [];

// ========== DOM 元素 ==========
const elements = {
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    categoryTags: document.getElementById('categoryTags'),
    discoverSection: document.getElementById('discoverSection'),
    swipeStack: document.getElementById('swipeStack'),
    swipeLike: document.getElementById('swipeLike'),
    swipeNope: document.getElementById('swipeNope'),
    swipeStatus: document.getElementById('swipeStatus'),
    darkhorseSection: document.getElementById('darkhorseSection'),
    darkhorseProducts: document.getElementById('darkhorseProducts'),
    trendingSection: document.getElementById('trendingSection'),
    weeklySection: document.getElementById('weeklySection'),
    blogsSection: document.getElementById('blogsSection'),
    blogsList: document.getElementById('blogsList'),
    blogFilters: document.getElementById('blogFilters'),
    searchSection: document.getElementById('searchSection'),
    productSection: document.getElementById('productSection'),
    productDetail: document.getElementById('productDetail'),
    productDetailSubtitle: document.getElementById('productDetailSubtitle'),
    dataFreshness: document.getElementById('dataFreshness'),
    trendingProducts: document.getElementById('trendingProducts'),
    weeklyProducts: document.getElementById('weeklyProducts'),
    searchResults: document.getElementById('searchResults'),
    searchResultInfo: document.getElementById('searchResultInfo'),
    navLinks: document.querySelectorAll('.nav-link'),
    // Sort/Filter controls
    sortBy: document.getElementById('sortBy'),
    typeFilter: document.getElementById('typeFilter'),
    showFavoritesBtn: document.getElementById('showFavoritesBtn'),
    favoritesCount: document.getElementById('favoritesCount'),
    // Modal
    productModal: document.getElementById('productModal'),
    modalClose: document.getElementById('modalClose'),
    modalContent: document.getElementById('modalContent'),
    // Favorites panel
    favoritesPanel: document.getElementById('favoritesPanel'),
    favoritesClose: document.getElementById('favoritesClose'),
    favoritesList: document.getElementById('favoritesList')
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initNavScroll();
    initSearch();
    initCategoryTags();
    initHeroGlow();
    initDiscovery();
    initBlogFilters();
    initSortFilter();
    initFavorites();
    initModal();
    loadDataFreshness();
    loadDarkHorseProducts();
    loadTrendingProducts();
    handleInitialRoute();
    updateFavoritesCount();
});

// ========== 导航功能 ==========
function initNavigation() {
    elements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            switchSection(section);
        });
    });
}

function initNavScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const updateNavbar = () => {
        navbar.classList.toggle('navbar--scrolled', window.scrollY > 12);
    };

    updateNavbar();
    window.addEventListener('scroll', updateNavbar, { passive: true });
}

function switchSection(section) {
    // 更新导航状态
    elements.navLinks.forEach(link => {
        link.classList.toggle('active', link.dataset.section === section);
    });

    // 切换显示的区域
    const showTrending = section === 'trending';
    elements.trendingSection.style.display = showTrending ? 'block' : 'none';
    if (elements.discoverSection) {
        elements.discoverSection.style.display = showTrending ? 'block' : 'none';
    }
    if (elements.darkhorseSection) {
        elements.darkhorseSection.style.display = showTrending && hasDarkhorseData ? 'block' : 'none';
    }
    elements.weeklySection.style.display = section === 'weekly' ? 'block' : 'none';
    if (elements.blogsSection) {
        elements.blogsSection.style.display = section === 'blogs' ? 'block' : 'none';
    }
    elements.searchSection.style.display = section === 'search' ? 'block' : 'none';
    if (elements.productSection) {
        elements.productSection.style.display = section === 'product' ? 'block' : 'none';
    }

    // 加载对应数据
    if (section === 'trending') {
        loadTrendingProducts();
    } else if (section === 'weekly') {
        loadWeeklyProducts();
    } else if (section === 'blogs') {
        loadBlogs();
    } else if (section === 'product') {
        // product detail is loaded by route handler
    }
}

function handleInitialRoute() {
    const rawPath = window.location.pathname || '/';
    const path = rawPath.endsWith('/') && rawPath !== '/' ? rawPath.slice(0, -1) : rawPath;
    if (path === '/blog') {
        switchSection('blogs');
        return;
    }
    if (path === '/search') {
        switchSection('search');
        return;
    }
    const productMatch = path.match(/^\/product\/(.+)$/);
    if (productMatch) {
        const productId = decodeURIComponent(productMatch[1]);
        loadProductDetail(productId);
    }
}

async function loadDataFreshness() {
    if (!elements.dataFreshness) return;

    try {
        const res = await fetch(`${API_BASE_URL}/products/last-updated`);
        const data = await res.json();
        if (!data || !data.last_updated) {
            elements.dataFreshness.textContent = '📡 数据更新时间未知';
            return;
        }

        const hours = Number(data.hours_ago);
        if (Number.isFinite(hours)) {
            if (hours < 1) {
                elements.dataFreshness.textContent = '📡 数据更新于 1 小时内';
            } else {
                elements.dataFreshness.textContent = `📡 数据更新于 ${hours.toFixed(1)} 小时前`;
            }
        } else {
            elements.dataFreshness.textContent = '📡 数据更新时间未知';
        }
    } catch (error) {
        console.error('加载数据更新时间失败:', error);
        elements.dataFreshness.textContent = '📡 数据更新时间未知';
    }
}

// ========== 搜索功能 ==========
function initSearch() {
    // 搜索按钮点击
    elements.searchBtn.addEventListener('click', performSearch);
    
    // 回车搜索
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// ========== Discovery Swipe ==========
const discoveryState = {
    pool: [],
    stack: [],
    liked: 0,
    skipped: 0,
    leftStreak: 0,
    categoryWeights: {}
};

function initDiscovery() {
    if (!elements.swipeStack || !elements.swipeLike || !elements.swipeNope) return;

    elements.swipeLike.addEventListener('click', () => handleSwipe('right'));
    elements.swipeNope.addEventListener('click', () => handleSwipe('left'));
    loadDiscoveryProducts();
}

async function loadDiscoveryProducts() {
    elements.swipeStack.innerHTML = '<div class="skeleton-card"></div>';

    try {
        const [trendingRes, weeklyRes] = await Promise.all([
            fetch(`${API_BASE_URL}/products/trending`),
            fetch(`${API_BASE_URL}/products/weekly-top`)
        ]);
        const trendingData = await trendingRes.json();
        const weeklyData = await weeklyRes.json();

        const products = mergeUniqueProducts([
            ...(trendingData.success ? trendingData.data : []),
            ...(weeklyData.success ? weeklyData.data : [])
        ]);

        buildDiscoveryDeck(products.length ? products : getMockWeeklyProducts());
    } catch (error) {
        console.error('加载发现产品失败:', error);
        buildDiscoveryDeck(getMockWeeklyProducts());
    }
}

function mergeUniqueProducts(products) {
    const seen = new Set();
    return products.filter(product => {
        const key = `${product.website || ''}-${product.name || ''}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

function buildDiscoveryDeck(products) {
    discoveryState.pool = [...products];
    discoveryState.stack = [];
    discoveryState.liked = 0;
    discoveryState.skipped = 0;
    discoveryState.leftStreak = 0;
    discoveryState.categoryWeights = {};

    refillDiscoveryStack();
    renderDiscoveryStack();
    updateDiscoveryStatus();
}

function refillDiscoveryStack() {
    while (discoveryState.stack.length < 3 && discoveryState.pool.length > 0) {
        const next = pickNextDiscoveryProduct();
        if (!next) break;
        discoveryState.stack.push(next);
    }
}

function pickNextDiscoveryProduct() {
    if (discoveryState.pool.length === 0) return null;

    const scored = discoveryState.pool.map(product => ({
        product,
        score: scoreDiscoveryProduct(product)
    }));

    scored.sort((a, b) => b.score - a.score);
    const pickWindow = Math.min(6, scored.length);
    const pickIndex = Math.floor(Math.random() * pickWindow);
    const chosen = scored[pickIndex].product;

    discoveryState.pool = discoveryState.pool.filter(item => item !== chosen);
    return chosen;
}

function scoreDiscoveryProduct(product) {
    let score = product.final_score || product.trending_score || 0;
    const categories = product.categories || [];
    categories.forEach(category => {
        score += discoveryState.categoryWeights[category] || 0;
    });
    return score + Math.random() * 0.3;
}

function renderDiscoveryStack() {
    if (!elements.swipeStack) return;

    if (discoveryState.stack.length === 0) {
        elements.swipeStack.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✨</div>
                <p class="empty-state-text">已经看完这一轮，稍后再来看看新产品吧。</p>
            </div>
        `;
        return;
    }

    const renderOrder = [...discoveryState.stack].reverse();
    elements.swipeStack.innerHTML = renderOrder.map((product, index) => {
        const pos = discoveryState.stack.length - 1 - index;
        return createSwipeCard(product, pos);
    }).join('');

    const activeCard = elements.swipeStack.querySelector('.swipe-card.is-active');
    if (activeCard) {
        attachSwipeHandlers(activeCard);
    }
}

function createSwipeCard(product, position) {
    const name = product.name || '未命名';
    const categories = (product.categories || []).slice(0, 2).map(getCategoryName).join(' · ');
    const website = product.website || '';

    // Clean and truncate description - remove technical noise
    let description = product.description || '暂无描述';
    description = cleanDescription(description);

    // Show source badge for new/trending items
    const source = product.source || '';
    const isNew = isRecentProduct(product);
    const sourceBadge = getSourceBadge(source, isNew);

    const logoMarkup = buildLogoMarkup(product);

    const videoPreview = getVideoPreview(product);

    return `
        <div class="swipe-card ${position === 0 ? 'is-active' : ''}" data-pos="${position}" data-website="${website}">
            <div class="swipe-card-header">
                <div class="swipe-card-logo">${logoMarkup}</div>
                <div class="swipe-card-title">
                    <h3>${name}</h3>
                    <p>${categories || '精选 AI 工具'}</p>
                </div>
                ${sourceBadge}
            </div>
            <p class="swipe-card-desc">${description}</p>
            ${videoPreview}
            <div class="swipe-card-meta">
                ${website ? `<a class="swipe-link" href="${website}" target="_blank" rel="noopener noreferrer">了解更多 →</a>` : ''}
            </div>
        </div>
    `;
}

function cleanDescription(desc) {
    if (!desc) return '暂无描述';
    // Remove technical noise patterns
    return desc
        .replace(/Hugging Face (模型|Space): [^|]+[|]/g, '')
        .replace(/[|] ⭐ [\d.]+K?\+? Stars/g, '')
        .replace(/[|] 技术: .+$/g, '')
        .replace(/[|] 下载量: .+$/g, '')
        .replace(/^\s*[|·]\s*/g, '')
        .trim() || '暂无描述';
}

function isRecentProduct(product) {
    if (!product.first_seen && !product.published_at) return false;
    const dateStr = product.published_at || product.first_seen;
    const productDate = new Date(dateStr);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return productDate > weekAgo;
}

function getSourceBadge(source, isNew) {
    if (isNew) {
        return '<span class="swipe-badge swipe-badge--new">🆕 新上线</span>';
    }
    const badges = {
        'producthunt': '<span class="swipe-badge">🚀 PH</span>',
        'hackernews': '<span class="swipe-badge">🔶 HN</span>',
        'tech_news': '<span class="swipe-badge">📰 News</span>'
    };
    return badges[source] || '';
}

function getVideoPreview(product) {
    const extra = product.extra || {};
    const videoUrl = extra.video_url;
    const videoThumbnail = extra.video_thumbnail;

    if (!videoUrl || !videoThumbnail) {
        return '';
    }

    return `
        <a class="video-preview" href="${videoUrl}" target="_blank" rel="noopener noreferrer">
            <img src="${videoThumbnail}" alt="Video preview" loading="lazy">
            <span class="video-play-icon">▶</span>
        </a>
    `;
}

function attachSwipeHandlers(card) {
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;

    const onPointerMove = (event) => {
        if (!isDragging) return;
        currentX = event.clientX - startX;
        currentY = event.clientY - startY;
        const rotate = currentX / 18;
        card.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${rotate}deg)`;
    };

    const onPointerUp = (event) => {
        if (!isDragging) return;
        isDragging = false;
        card.releasePointerCapture?.(event.pointerId);

        const threshold = 110;
        if (currentX > threshold) {
            handleSwipe('right');
        } else if (currentX < -threshold) {
            handleSwipe('left');
        } else {
            card.style.transition = 'transform 0.25s ease';
            card.style.transform = '';
        }
    };

    card.addEventListener('pointerdown', (event) => {
        if (event.button !== 0) return;
        isDragging = true;
        startX = event.clientX;
        startY = event.clientY;
        card.setPointerCapture(event.pointerId);
        card.style.transition = 'none';
    });

    card.addEventListener('pointermove', onPointerMove);
    card.addEventListener('pointerup', onPointerUp);
    card.addEventListener('pointercancel', onPointerUp);
}

function handleSwipe(direction) {
    const activeCard = elements.swipeStack.querySelector('.swipe-card.is-active');
    const activeProduct = discoveryState.stack[0];
    if (!activeCard || !activeProduct) return;

    activeCard.style.transform = '';
    activeCard.style.transition = '';

    if (direction === 'right') {
        activeCard.classList.add('is-exit-like');
    } else {
        activeCard.classList.add('is-exit-nope');
    }

    updateDiscoveryPreferences(activeProduct, direction);
    updateDiscoveryStatus();

    setTimeout(() => {
        discoveryState.stack.shift();
        refillDiscoveryStack();
        renderDiscoveryStack();
    }, 260);
}

function updateDiscoveryPreferences(product, direction) {
    const categories = product.categories || [];
    if (direction === 'right') {
        discoveryState.liked += 1;
        discoveryState.leftStreak = 0;
        categories.forEach(category => {
            discoveryState.categoryWeights[category] = (discoveryState.categoryWeights[category] || 0) + 2;
        });
    } else {
        discoveryState.skipped += 1;
        discoveryState.leftStreak += 1;
        if (discoveryState.leftStreak >= 4) {
            categories.forEach(category => {
                discoveryState.categoryWeights[category] = (discoveryState.categoryWeights[category] || 0) - 0.5;
            });
        }
    }
}

function updateDiscoveryStatus() {
    if (!elements.swipeStatus) return;
    elements.swipeStatus.textContent = `已收藏 ${discoveryState.liked} · 已跳过 ${discoveryState.skipped}`;
}

// ========== Hero 互动光效 ==========
function initHeroGlow() {
    const hero = document.querySelector('.hero');
    if (!hero) return;

    hero.addEventListener('pointermove', (event) => {
        const rect = hero.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        hero.style.setProperty('--glow-x', `${x}%`);
        hero.style.setProperty('--glow-y', `${y}%`);
    });

    hero.addEventListener('pointerleave', () => {
        hero.style.removeProperty('--glow-x');
        hero.style.removeProperty('--glow-y');
    });
}

async function performSearch() {
    const keyword = elements.searchInput.value.trim();
    const categories = Array.from(selectedCategories).join(',');
    
    // 切换到搜索结果区
    switchSection('search');
    
    // 显示加载状态
    elements.searchResults.innerHTML = `
        <div class="loading-skeleton">
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
        </div>
    `;
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/search/?q=${encodeURIComponent(keyword)}&categories=${categories}`
        );
        const data = await response.json();
        
        if (data.success) {
            renderSearchResults(data.data, data.pagination.total, keyword);
        } else {
            showEmptyState(elements.searchResults, '搜索失败，请稍后重试');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        // 使用模拟数据
        const mockResults = getMockSearchResults(keyword, Array.from(selectedCategories));
        renderSearchResults(mockResults.products, mockResults.total, keyword);
    }
}

function renderSearchResults(products, total, keyword) {
    const searchInfo = keyword 
        ? `搜索 "${keyword}" 找到 ${total} 个相关产品`
        : `找到 ${total} 个相关产品`;
    elements.searchResultInfo.textContent = searchInfo;
    
    if (products.length === 0) {
        showEmptyState(elements.searchResults, '没有找到匹配的产品，换个关键词试试？');
        return;
    }
    
    elements.searchResults.innerHTML = products.map(product => 
        createProductCard(product)
    ).join('');
    
    // 添加动画
    animateCards(elements.searchResults);
}

// ========== 分类标签 ==========
function initCategoryTags() {
    const tagButtons = elements.categoryTags.querySelectorAll('.tag-btn');
    
    tagButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.dataset.category;
            
            if (selectedCategories.has(category)) {
                selectedCategories.delete(category);
                btn.classList.remove('active');
            } else {
                selectedCategories.add(category);
                btn.classList.add('active');
            }
            
            // 如果有选中分类，自动触发搜索
            if (selectedCategories.size > 0) {
                performSearch();
            }
        });
    });
}

// ========== 加载热门产品 ==========
async function loadTrendingProducts() {
    try {
        // Load weekly-top for the full product cache (for sorting/filtering)
        const weeklyResponse = await fetch(`${API_BASE_URL}/products/weekly-top`);
        const weeklyData = await weeklyResponse.json();
        if (weeklyData.success && weeklyData.data) {
            allProductsCache = weeklyData.data;
        }

        const response = await fetch(`${API_BASE_URL}/products/trending`);
        const data = await response.json();

        if (data.success) {
            renderTrendingProducts(data.data);
        }
    } catch (error) {
        console.error('加载热门产品失败:', error);
        // 使用模拟数据
        renderTrendingProducts(getMockTrendingProducts());
    }
}

function renderTrendingProducts(products) {
    // Cache all products for sorting/filtering
    if (products.length > 0 && allProductsCache.length === 0) {
        allProductsCache = [...products];
    }

    elements.trendingProducts.innerHTML = products.map(product =>
        createProductCardWithFavorite(product, true)
    ).join('');

    animateCards(elements.trendingProducts);
}

// ========== 加载黑马产品 ==========
async function loadDarkHorseProducts() {
    if (!elements.darkhorseProducts) return;

    try {
        const response = await fetch(`${API_BASE_URL}/products/dark-horses?limit=6`);
        const data = await response.json();

        hasDarkhorseData = Boolean(data.success && data.data.length > 0);
        if (hasDarkhorseData) {
            renderDarkHorseProducts(data.data);
        } else {
            // 如果没有数据，隐藏整个黑马区域
            if (elements.darkhorseSection) {
                elements.darkhorseSection.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('加载黑马产品失败:', error);
        hasDarkhorseData = false;
        if (elements.darkhorseSection) {
            elements.darkhorseSection.style.display = 'none';
        }
    }
}

function renderDarkHorseProducts(products) {
    elements.darkhorseProducts.innerHTML = products.map(product =>
        createDarkHorseCard(product)
    ).join('');

    animateDarkHorseCards(elements.darkhorseProducts);
}

function createDarkHorseCard(product) {
    const name = product.name || '未命名';
    const darkHorseIndex = product.dark_horse_index || 0;
    const stars = '★'.repeat(darkHorseIndex) + '☆'.repeat(5 - darkHorseIndex);
    const foundedDate = product.founded_date || '';
    const fundingTotal = product.funding_total || '';
    const valuation = product.valuation || '';
    const whyMatters = product.why_matters || '';
    const latestNews = product.latest_news || '';
    const isHardware = product.is_hardware || false;
    const website = product.website || '';

    const logoMarkup = buildLogoMarkup(product);

    // Build metadata tags
    let metaTags = '';
    if (foundedDate) {
        metaTags += `<span class="darkhorse-meta-tag"><span class="meta-icon">📅</span> ${foundedDate}</span>`;
    }
    if (fundingTotal) {
        metaTags += `<span class="darkhorse-meta-tag darkhorse-meta-tag--funding"><span class="meta-icon">💰</span> ${fundingTotal}</span>`;
    }
    if (isHardware) {
        metaTags += `<span class="darkhorse-meta-tag darkhorse-meta-tag--hardware"><span class="meta-icon">🤖</span> 硬件</span>`;
    }

    return `
        <div class="darkhorse-card" onclick="openProduct('${website}')">
            <div class="darkhorse-card-header">
                <div class="darkhorse-logo">${logoMarkup}</div>
                <div class="darkhorse-title-block">
                    <h3 class="darkhorse-name">${name}</h3>
                    <div class="darkhorse-rating" title="黑马指数 ${darkHorseIndex}/5">
                        <span class="darkhorse-stars">${stars}</span>
                    </div>
                </div>
            </div>
            ${whyMatters ? `<p class="darkhorse-why">${whyMatters}</p>` : ''}
            <div class="darkhorse-meta">
                ${metaTags}
            </div>
            ${valuation ? `<div class="darkhorse-valuation">估值: ${valuation}</div>` : ''}
            ${latestNews ? `<div class="darkhorse-news"><span class="news-icon">📰</span> ${latestNews}</div>` : ''}
            <div class="darkhorse-cta">
                <span class="darkhorse-link">了解更多 →</span>
            </div>
        </div>
    `;
}

function animateDarkHorseCards(container) {
    const cards = container.querySelectorAll('.darkhorse-card');
    if (prefersReducedMotion) {
        cards.forEach((card) => {
            card.style.opacity = '1';
            card.style.transform = 'none';
        });
        return;
    }
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(24px) scale(0.96)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0) scale(1)';
        }, index * 100);
    });
}

// ========== 加载本周榜单 ==========
async function loadWeeklyProducts() {
    try {
        const response = await fetch(`${API_BASE_URL}/products/weekly-top`);
        const data = await response.json();
        
        if (data.success) {
            renderWeeklyProducts(data.data);
        }
    } catch (error) {
        console.error('加载本周榜单失败:', error);
        // 使用模拟数据
        renderWeeklyProducts(getMockWeeklyProducts());
    }
}

function renderWeeklyProducts(products) {
    elements.weeklyProducts.innerHTML = products.map((product, index) =>
        createProductListItem(product, index + 1)
    ).join('');

    animateListItems(elements.weeklyProducts);
}

// ========== 产品详情 ==========
async function loadProductDetail(productId) {
    if (!elements.productSection || !elements.productDetail) return;
    switchSection('product');
    elements.productDetail.innerHTML = `
        <div class="loading-skeleton">
            <div class="skeleton-card"></div>
        </div>
    `;

    if (elements.productDetailSubtitle) {
        elements.productDetailSubtitle.textContent = '产品详情加载中...';
    }

    try {
        const response = await fetch(`${API_BASE_URL}/products/${encodeURIComponent(productId)}`);
        const data = await response.json();

        if (data.success && data.data) {
            renderProductDetail(data.data);
        } else {
            showProductDetailError('未找到对应产品');
        }
    } catch (error) {
        console.error('加载产品详情失败:', error);
        showProductDetailError('产品详情加载失败');
    }
}

function renderProductDetail(product) {
    const name = product.name || '未命名';
    const description = product.description || '暂无描述';
    const website = product.website || '';
    const categories = (product.categories || []).map(getCategoryName).join(' · ');
    const rating = product.rating ? product.rating.toFixed(1) : '';
    const users = product.weekly_users ? formatNumber(product.weekly_users) : '';
    const foundedDate = product.founded_date || '';
    const fundingTotal = product.funding_total || '';
    const whyMatters = product.why_matters || '';
    const logoMarkup = buildLogoMarkup(product);

    const metaItems = [];
    if (categories) metaItems.push(`🏷️ ${categories}`);
    if (rating) metaItems.push(`⭐ ${rating}`);
    if (users) metaItems.push(`👥 ${users}`);
    if (foundedDate) metaItems.push(`📅 ${foundedDate}`);
    if (fundingTotal) metaItems.push(`💰 ${fundingTotal}`);

    if (elements.productDetailSubtitle) {
        elements.productDetailSubtitle.textContent = categories ? `类别 · ${categories}` : '来自本周精选';
    }

    elements.productDetail.innerHTML = `
        <div class="product-detail-card">
            <div class="product-detail-logo">${logoMarkup}</div>
            <div class="product-detail-title">
                <a class="product-detail-link" href="/" data-action="back">← 返回首页</a>
                <h3>${name}</h3>
                <p class="product-detail-description">${description}</p>
                ${website ? `<a class="product-detail-link" href="${website}" target="_blank" rel="noopener noreferrer">${website}</a>` : ''}
                ${metaItems.length ? `<div class="product-detail-meta">${metaItems.map(item => `<span>${item}</span>`).join('')}</div>` : ''}
                ${whyMatters ? `<div class="product-detail-why">💡 ${whyMatters}</div>` : ''}
            </div>
        </div>
    `;

    const backLink = elements.productDetail.querySelector('[data-action="back"]');
    if (backLink) {
        backLink.addEventListener('click', (event) => {
            event.preventDefault();
            window.history.pushState({}, '', '/');
            switchSection('trending');
        });
    }
}

function showProductDetailError(message) {
    if (elements.productDetailSubtitle) {
        elements.productDetailSubtitle.textContent = '产品详情';
    }
    elements.productDetail.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <p class="empty-state-text">${message}</p>
        </div>
    `;
}

// ========== 博客动态功能 ==========
let currentBlogSource = '';

function initBlogFilters() {
    if (!elements.blogFilters) return;

    const filterBtns = elements.blogFilters.querySelectorAll('.blog-filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentBlogSource = btn.dataset.source || '';
            loadBlogs(currentBlogSource);
        });
    });
}

async function loadBlogs(source = '') {
    if (!elements.blogsList) return;

    elements.blogsList.innerHTML = `
        <div class="loading-skeleton">
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
        </div>
    `;

    try {
        const url = source
            ? `${API_BASE_URL}/products/blogs?source=${source}&limit=30`
            : `${API_BASE_URL}/products/blogs?limit=30`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            renderBlogs(data.data);
        } else {
            showEmptyState(elements.blogsList, '暂无博客动态');
        }
    } catch (error) {
        console.error('加载博客失败:', error);
        showEmptyState(elements.blogsList, '加载失败，请稍后重试');
    }
}

function renderBlogs(blogs) {
    elements.blogsList.innerHTML = blogs.map(blog => createBlogItem(blog)).join('');
    animateListItems(elements.blogsList);
}

function createBlogItem(blog) {
    const source = blog.source || 'unknown';
    const sourceLabel = getSourceLabel(source);
    const description = cleanDescription(blog.description || '');
    const website = blog.website || '';
    const extra = blog.extra || {};
    const points = extra.points || extra.votes || 0;
    const comments = extra.comments || 0;

    // Format date
    const dateStr = blog.published_at || blog.first_seen || '';
    const dateLabel = dateStr ? formatDate(dateStr) : '';

    return `
        <div class="blog-item" onclick="openProduct('${website}')">
            <div class="blog-source ${source}">${sourceLabel}</div>
            <div class="blog-content">
                <h3 class="blog-title">${blog.name}</h3>
                <p class="blog-desc">${description}</p>
                <div class="blog-meta">
                    ${points ? `<span class="blog-stat">👍 ${points}</span>` : ''}
                    ${comments ? `<span class="blog-stat">💬 ${comments}</span>` : ''}
                    ${dateLabel ? `<span class="blog-date">${dateLabel}</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

function getSourceLabel(source) {
    const labels = {
        'hackernews': '🔶 HN',
        'tech_news': '📰 News',
        'reddit': '🔴 Reddit'
    };
    return labels[source] || '📄 Blog';
}

function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return '今天';
        if (diffDays === 1) return '昨天';
        if (diffDays < 7) return `${diffDays}天前`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`;
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    } catch {
        return '';
    }
}

function getInitial(name) {
    if (!name) return '?';
    const trimmed = name.trim();
    return trimmed ? trimmed.charAt(0).toUpperCase() : '?';
}

function getLogoSource(product) {
    return product.logo_url || product.logo || product.logoUrl || '';
}

function getFaviconUrl(website) {
    if (!website) return '';
    try {
        const normalized = website.startsWith('http') ? website : `https://${website}`;
        const host = new URL(normalized).hostname;
        if (!host) return '';
        return `https://www.google.com/s2/favicons?domain=${host}&sz=128`;
    } catch {
        return '';
    }
}

function buildLogoMarkup(product) {
    const name = product.name || 'AI';
    const initial = getInitial(name);
    const logoSrc = getLogoSource(product);
    const fallbackSrc = getFaviconUrl(product.website || '');

    if (logoSrc) {
        return `<img src="${logoSrc}" alt="${name}" data-fallback="${fallbackSrc}" data-initial="${initial}" onerror="handleLogoError(this)">`;
    }
    if (fallbackSrc) {
        return `<img src="${fallbackSrc}" alt="${name}" data-initial="${initial}" onerror="handleLogoError(this)">`;
    }
    return `<div class="product-logo-placeholder">${initial}</div>`;
}

/* exported handleLogoError, openProduct */
function handleLogoError(img) {
    if (!img) return;
    const fallbackSrc = img.dataset.fallback || '';
    const initial = img.dataset.initial || '?';

    if (!img.dataset.fallbackTried && fallbackSrc && img.src !== fallbackSrc) {
        img.dataset.fallbackTried = 'true';
        img.src = fallbackSrc;
        return;
    }

    const placeholder = document.createElement('div');
    placeholder.className = 'product-logo-placeholder';
    placeholder.textContent = initial;
    img.replaceWith(placeholder);
}

// ========== 创建产品卡片 ==========
function createProductCard(product, showBadge = false) {
    const categories = product.categories || [];
    const categoryTags = categories.slice(0, 2).map(cat => 
        `<span class="product-tag">${getCategoryName(cat)}</span>`
    ).join('');
    
    const name = product.name || '未命名';
    const fundingTotal = product.funding_total || '';
    const whyMatters = product.why_matters || '';
    const description = product.description || '暂无描述';
    const rating = product.rating ? product.rating.toFixed(1) : 'N/A';
    const users = formatNumber(product.weekly_users);
    const cardClass = showBadge ? 'product-card product-card--hot' : 'product-card';
    const logoMarkup = buildLogoMarkup(product);
    
    return `
        <div class="${cardClass}" onclick="openProduct('${product.website}')">
            <div class="product-logo">
                ${logoMarkup}
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${name}</h3>
                    ${showBadge ? `<span class="product-badge">🔥 热门</span>` : ''}
                </div>
                <p class="product-description">${description}</p>
                ${(whyMatters || fundingTotal) ? `
                <div class="product-insights">
                    ${whyMatters ? `<div class="product-insight">💡 ${whyMatters}</div>` : ''}
                    ${fundingTotal ? `<div class="product-insight product-insight--funding">💰 ${fundingTotal}</div>` : ''}
                </div>` : ''}
                <div class="product-meta">
                    <span class="product-meta-item">⭐ ${rating}</span>
                    <span class="product-meta-item">👥 ${users}</span>
                </div>
                <div class="product-tags">
                    ${categoryTags}
                </div>
            </div>
        </div>
    `;
}

// ========== 创建产品列表项 ==========
function createProductListItem(product, rank) {
    const name = product.name || '未命名';
    const description = product.description || '暂无描述';
    const users = formatNumber(product.weekly_users);
    const fundingTotal = product.funding_total || '';
    const whyMatters = product.why_matters || '';
    const logoMarkup = buildLogoMarkup(product);
    
    return `
        <div class="product-list-item" onclick="openProduct('${product.website}')">
            <div class="product-rank ${rank <= 3 ? 'top-3' : ''}">${rank}</div>
            <div class="product-list-logo">
                ${logoMarkup}
            </div>
            <div class="product-list-info">
                <h3 class="product-list-name">${name}</h3>
                <p class="product-list-desc">${description}</p>
                ${(whyMatters || fundingTotal) ? `
                <div class="product-list-extra">
                    ${whyMatters ? `<span>💡 ${whyMatters}</span>` : ''}
                    ${fundingTotal ? `<span class="product-list-funding">💰 ${fundingTotal}</span>` : ''}
                </div>` : ''}
            </div>
            <div class="product-list-stats">
                <div class="stat-value">${users}</div>
                <div class="stat-label">周活跃用户</div>
            </div>
        </div>
    `;
}

// ========== 辅助函数 ==========
function getCategoryName(categoryId) {
    const categoryNames = {
        'coding': '编程开发',
        'voice': '语音识别',
        'finance': '金融科技',
        'image': '图像处理',
        'video': '视频生成',
        'writing': '写作助手',
        'healthcare': '医疗健康',
        'education': '教育学习',
        'hardware': '硬件设备',
        'other': '其他'
    };
    return categoryNames[categoryId] || categoryId;
}

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
}

function showEmptyState(container, message) {
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <p class="empty-state-text">${message}</p>
        </div>
    `;
}

function openProduct(url) {
    if (url) {
        const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
        if (newWindow) {
            newWindow.opener = null;
        }
    }
}

// ========== 动画效果 ==========
function animateCards(container) {
    const cards = container.querySelectorAll('.product-card');
    if (prefersReducedMotion) {
        cards.forEach((card) => {
            card.style.opacity = '1';
            card.style.transform = 'none';
        });
        return;
    }
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 80);
    });
}

function animateListItems(container) {
    const items = container.querySelectorAll('.product-list-item');
    if (prefersReducedMotion) {
        items.forEach((item) => {
            item.style.opacity = '1';
            item.style.transform = 'none';
        });
        return;
    }
    items.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            item.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, index * 60);
    });
}

// ========== 模拟数据 (当API不可用时使用) - 只包含黑马产品 ==========
function getMockTrendingProducts() {
    return [
        {
            _id: '1',
            name: 'Lovable',
            description: '欧洲最快增长的 AI 产品，8 个月从 0 到独角兽。非开发者也能快速构建全栈应用。',
            logo_url: 'https://lovable.dev/favicon.ico',
            website: 'https://lovable.dev',
            categories: ['coding'],
            rating: 4.8,
            weekly_users: 120000,
            trending_score: 92,
            why_matters: '证明了 AI 原生产品可以极速获客，对想做 AI 创业的 PM 有重要参考价值。'
        },
        {
            _id: '2',
            name: 'Devin',
            description: '全自主 AI 软件工程师，能够端到端处理需求拆解、代码实现与交付。',
            logo_url: 'https://cognition.ai/favicon.ico',
            website: 'https://cognition.ai',
            categories: ['coding'],
            rating: 4.7,
            weekly_users: 160000,
            trending_score: 93,
            why_matters: '重新定义了「AI 工程师」边界，PM 需要思考如何与 AI 协作而非仅仅使用 AI。'
        },
        {
            _id: '3',
            name: 'Kiro',
            description: 'AWS 背景团队打造的规范驱动 AI 开发平台，强调稳定的工程化交付。',
            logo_url: 'https://kiro.dev/favicon.ico',
            website: 'https://kiro.dev',
            categories: ['coding'],
            rating: 4.7,
            weekly_users: 85000,
            trending_score: 90,
            why_matters: '大厂背景创业，专注企业级可靠性，是 AI 编程工具的差异化方向。'
        },
        {
            _id: '4',
            name: 'Bolt.new',
            description: 'StackBlitz 推出的浏览器内全栈 AI 开发环境，无需配置即可开始编码。',
            logo_url: 'https://bolt.new/favicon.ico',
            website: 'https://bolt.new',
            categories: ['coding'],
            rating: 4.8,
            weekly_users: 200000,
            trending_score: 91,
            why_matters: '零配置 + 浏览器内运行，大幅降低 AI 开发入门门槛。'
        },
        {
            _id: '5',
            name: 'NEO (1X Technologies)',
            description: '挪威初创公司研发的人形机器人，定位家庭助手和轻工业场景。',
            logo_url: 'https://1x.tech/favicon.ico',
            website: 'https://1x.tech',
            categories: ['hardware'],
            rating: 4.5,
            weekly_users: 15000,
            trending_score: 85,
            why_matters: '人形机器人赛道的黑马，融资后估值飙升，值得关注具身智能趋势。'
        }
    ];
}

function getMockWeeklyProducts() {
    return [
        { _id: '1', name: 'Lovable', description: '欧洲最快增长的 AI 产品，8 个月从 0 到独角兽。非开发者也能快速构建全栈应用。', logo_url: 'https://lovable.dev/favicon.ico', website: 'https://lovable.dev', categories: ['coding'], rating: 4.8, weekly_users: 120000, why_matters: '证明了 AI 原生产品可以极速获客' },
        { _id: '2', name: 'Devin', description: '全自主 AI 软件工程师，能够端到端处理需求拆解、代码实现与交付。', logo_url: 'https://cognition.ai/favicon.ico', website: 'https://cognition.ai', categories: ['coding'], rating: 4.7, weekly_users: 160000, why_matters: '重新定义了 AI 工程师边界' },
        { _id: '3', name: 'Kiro', description: 'AWS 背景团队打造的规范驱动 AI 开发平台，强调稳定交付。', logo_url: 'https://kiro.dev/favicon.ico', website: 'https://kiro.dev', categories: ['coding'], rating: 4.7, weekly_users: 85000, why_matters: '大厂背景创业，专注企业级可靠性' },
        { _id: '4', name: 'Emergent', description: '非开发者也能用 AI 代理构建全栈应用的建站产品。', logo_url: 'https://emergent.sh/favicon.ico', website: 'https://emergent.sh', categories: ['coding'], rating: 4.6, weekly_users: 45000, why_matters: '面向非技术用户的 AI 开发工具' },
        { _id: '5', name: 'Bolt.new', description: 'StackBlitz 推出的浏览器内全栈 AI 开发环境。', logo_url: 'https://bolt.new/favicon.ico', website: 'https://bolt.new', categories: ['coding'], rating: 4.8, weekly_users: 200000, why_matters: '零配置浏览器内 AI 开发' },
        { _id: '6', name: 'Windsurf', description: 'Codeium 推出的 Agentic IDE，AI 代理主动参与开发流程。', logo_url: 'https://codeium.com/favicon.ico', website: 'https://codeium.com/windsurf', categories: ['coding'], rating: 4.6, weekly_users: 95000, why_matters: 'Agentic IDE 概念先行者' },
        { _id: '7', name: 'NEO (1X)', description: '挪威初创公司研发的人形机器人，定位家庭助手。', logo_url: 'https://1x.tech/favicon.ico', website: 'https://1x.tech', categories: ['hardware'], rating: 4.5, weekly_users: 15000, why_matters: '人形机器人赛道黑马' },
        { _id: '8', name: 'Rokid AR Studio', description: '中国 AR 眼镜厂商的 AI 开发平台。', logo_url: 'https://www.rokid.com/favicon.ico', website: 'https://www.rokid.com', categories: ['hardware'], rating: 4.4, weekly_users: 25000, why_matters: '国产 AR + AI 空间计算' },
        { _id: '9', name: 'DeepSeek', description: '中国 AI 研究公司，以高效开源模型著称。', logo_url: 'https://www.deepseek.com/favicon.ico', website: 'https://www.deepseek.com', categories: ['coding', 'writing'], rating: 4.6, weekly_users: 180000, why_matters: '开源大模型性价比之王' },
        { _id: '10', name: 'Replit Agent', description: 'Replit 的 AI 代理，自主完成从需求到部署。', logo_url: 'https://replit.com/favicon.ico', website: 'https://replit.com', categories: ['coding'], rating: 4.5, weekly_users: 150000, why_matters: '全流程 AI 开发代理' },
        { _id: '11', name: 'v0.dev', description: 'Vercel 推出的 AI UI 生成器，对话生成 React 组件。', logo_url: 'https://v0.dev/favicon.ico', website: 'https://v0.dev', categories: ['coding', 'image'], rating: 4.7, weekly_users: 175000, why_matters: '前端 AI 生成标杆产品' },
        { _id: '12', name: 'Kling AI', description: '快手推出的 AI 视频生成工具。', logo_url: 'https://klingai.com/favicon.ico', website: 'https://klingai.com', categories: ['video'], rating: 4.4, weekly_users: 320000, why_matters: '国产视频生成 AI 代表' },
        { _id: '13', name: 'Poe', description: 'Quora 的多模型 AI 聊天平台，一站式访问多种模型。', logo_url: 'https://poe.com/favicon.ico', website: 'https://poe.com', categories: ['other'], rating: 4.5, weekly_users: 280000, why_matters: 'AI 模型聚合平台' },
        { _id: '14', name: 'Glif', description: '可视化 AI 工作流构建平台，无需代码串联多个模型。', logo_url: 'https://glif.app/favicon.ico', website: 'https://glif.app', categories: ['image', 'other'], rating: 4.5, weekly_users: 45000, why_matters: 'AI 工作流乐高积木' },
        { _id: '15', name: 'Thinking Machines Lab', description: '菲律宾 AI 研究初创，专注东南亚本地化大模型。', logo_url: 'https://thinkingmachines.ph/favicon.ico', website: 'https://thinkingmachines.ph', categories: ['other'], rating: 4.3, weekly_users: 12000, why_matters: '东南亚本土 AI 研究力量' }
    ];
}

function getMockSearchResults(keyword, categories) {
    let allProducts = getMockWeeklyProducts();

    // 关键词筛选
    if (keyword) {
        const keywordLower = keyword.toLowerCase();
        allProducts = allProducts.filter(p =>
            p.name.toLowerCase().includes(keywordLower) ||
            p.description.toLowerCase().includes(keywordLower)
        );
    }

    // 分类筛选
    if (categories.length > 0) {
        allProducts = allProducts.filter(p =>
            p.categories.some(cat => categories.includes(cat))
        );
    }

    return {
        products: allProducts,
        total: allProducts.length
    };
}

// ========== Sort/Filter Controls ==========
function initSortFilter() {
    if (elements.sortBy) {
        elements.sortBy.addEventListener('change', (e) => {
            currentSort = e.target.value;
            applyFiltersAndSort();
        });
    }

    if (elements.typeFilter) {
        elements.typeFilter.addEventListener('change', (e) => {
            currentTypeFilter = e.target.value;
            applyFiltersAndSort();
        });
    }
}

function applyFiltersAndSort() {
    let products = [...allProductsCache];

    // Apply type filter
    if (currentTypeFilter === 'software') {
        products = products.filter(p => !p.is_hardware);
    } else if (currentTypeFilter === 'hardware') {
        products = products.filter(p => p.is_hardware);
    }

    // Apply sort
    products.sort((a, b) => {
        switch (currentSort) {
            case 'users':
                return (b.weekly_users || 0) - (a.weekly_users || 0);
            case 'date':
                const dateA = new Date(a.first_seen || a.published_at || 0);
                const dateB = new Date(b.first_seen || b.published_at || 0);
                return dateB - dateA;
            case 'rating':
                return (b.rating || 0) - (a.rating || 0);
            case 'score':
            default:
                return (b.hot_score || b.final_score || b.trending_score || 0) -
                       (a.hot_score || a.final_score || a.trending_score || 0);
        }
    });

    renderTrendingProducts(products.slice(0, 5));
}

// ========== Favorites ==========
function initFavorites() {
    if (elements.showFavoritesBtn) {
        elements.showFavoritesBtn.addEventListener('click', toggleFavoritesPanel);
    }

    if (elements.favoritesClose) {
        elements.favoritesClose.addEventListener('click', closeFavoritesPanel);
    }

    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
        if (elements.favoritesPanel?.classList.contains('is-open')) {
            if (!elements.favoritesPanel.contains(e.target) &&
                !elements.showFavoritesBtn?.contains(e.target)) {
                closeFavoritesPanel();
            }
        }
    });
}

function getFavorites() {
    try {
        const stored = localStorage.getItem(FAVORITES_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

function saveFavorites(favorites) {
    try {
        localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
    } catch (e) {
        console.error('Failed to save favorites:', e);
    }
}

function isFavorited(productKey) {
    const favorites = getFavorites();
    return favorites.some(f => f.key === productKey);
}

function toggleFavorite(product, event) {
    if (event) {
        event.stopPropagation();
    }

    const productKey = getProductKey(product);
    let favorites = getFavorites();

    if (isFavorited(productKey)) {
        favorites = favorites.filter(f => f.key !== productKey);
    } else {
        favorites.push({
            key: productKey,
            name: product.name,
            logo_url: product.logo_url,
            website: product.website,
            categories: product.categories,
            addedAt: new Date().toISOString()
        });
    }

    saveFavorites(favorites);
    updateFavoritesCount();
    updateFavoriteButtons(productKey);
    renderFavoritesList();
}

function getProductKey(product) {
    return product.website || product.name || '';
}

function updateFavoritesCount() {
    const count = getFavorites().length;
    if (elements.favoritesCount) {
        elements.favoritesCount.textContent = count;
    }
}

function updateFavoriteButtons(productKey) {
    const isFav = isFavorited(productKey);
    document.querySelectorAll(`[data-product-key="${productKey}"]`).forEach(btn => {
        btn.classList.toggle('is-favorited', isFav);
        btn.innerHTML = isFav ? '❤️' : '🤍';
    });
}

function toggleFavoritesPanel() {
    const panel = elements.favoritesPanel;
    if (!panel) return;

    const isOpen = panel.classList.contains('is-open');
    if (isOpen) {
        closeFavoritesPanel();
    } else {
        openFavoritesPanel();
    }
}

function openFavoritesPanel() {
    if (!elements.favoritesPanel) return;
    elements.favoritesPanel.classList.add('is-open');
    renderFavoritesList();
}

function closeFavoritesPanel() {
    if (!elements.favoritesPanel) return;
    elements.favoritesPanel.classList.remove('is-open');
}

function renderFavoritesList() {
    if (!elements.favoritesList) return;

    const favorites = getFavorites();
    const panel = elements.favoritesPanel;

    if (favorites.length === 0) {
        panel?.classList.add('is-empty');
        elements.favoritesList.innerHTML = '';
        return;
    }

    panel?.classList.remove('is-empty');

    elements.favoritesList.innerHTML = favorites.map(fav => {
        const categories = (fav.categories || []).slice(0, 2).map(getCategoryName).join(' · ');
        const logoMarkup = fav.logo_url
            ? `<img src="${fav.logo_url}" alt="${fav.name}" onerror="this.style.display='none'">`
            : `<div class="product-logo-placeholder">${getInitial(fav.name)}</div>`;

        return `
            <div class="favorite-item" onclick="openProduct('${fav.website}')">
                <div class="favorite-item-logo">${logoMarkup}</div>
                <div class="favorite-item-info">
                    <div class="favorite-item-name">${fav.name}</div>
                    <div class="favorite-item-category">${categories || '精选 AI 工具'}</div>
                </div>
                <button class="favorite-item-remove" onclick="removeFavoriteFromPanel('${fav.key}', event)" title="移除收藏">×</button>
            </div>
        `;
    }).join('');
}

/* exported removeFavoriteFromPanel */
function removeFavoriteFromPanel(productKey, event) {
    if (event) {
        event.stopPropagation();
    }

    let favorites = getFavorites();
    favorites = favorites.filter(f => f.key !== productKey);
    saveFavorites(favorites);
    updateFavoritesCount();
    updateFavoriteButtons(productKey);
    renderFavoritesList();
}

// ========== Product Modal ==========
function initModal() {
    if (elements.modalClose) {
        elements.modalClose.addEventListener('click', closeModal);
    }

    if (elements.productModal) {
        elements.productModal.addEventListener('click', (e) => {
            if (e.target === elements.productModal) {
                closeModal();
            }
        });
    }

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.productModal?.classList.contains('is-open')) {
            closeModal();
        }
    });
}

function openModal(product) {
    if (!elements.productModal || !elements.modalContent) return;

    const name = product.name || '未命名';
    const description = product.description || '暂无描述';
    const website = product.website || '';
    const categories = (product.categories || []).map(getCategoryName);
    const rating = product.rating ? product.rating.toFixed(1) : 'N/A';
    const users = formatNumber(product.weekly_users);
    const whyMatters = product.why_matters || '';
    const fundingTotal = product.funding_total || '';
    const valuation = product.valuation || '';
    const foundedDate = product.founded_date || '';
    const pricing = product.pricing || '';
    const productKey = getProductKey(product);
    const isFav = isFavorited(productKey);

    const logoMarkup = buildLogoMarkup(product);

    const categoriesHtml = categories.map(cat =>
        `<span class="modal-category">${cat}</span>`
    ).join('');

    let statsHtml = '';
    if (rating !== 'N/A' || users !== '0') {
        statsHtml = `
            <div class="modal-stats">
                ${rating !== 'N/A' ? `<div class="modal-stat"><div class="modal-stat-value">⭐ ${rating}</div><div class="modal-stat-label">评分</div></div>` : ''}
                ${users !== '0' ? `<div class="modal-stat"><div class="modal-stat-value">👥 ${users}</div><div class="modal-stat-label">周活跃</div></div>` : ''}
                ${fundingTotal ? `<div class="modal-stat"><div class="modal-stat-value">💰 ${fundingTotal}</div><div class="modal-stat-label">融资</div></div>` : ''}
            </div>
        `;
    }

    let detailsHtml = '';
    const details = [];
    if (foundedDate) details.push({ label: '成立时间', value: foundedDate });
    if (valuation) details.push({ label: '估值', value: valuation });
    if (pricing) details.push({ label: '定价', value: pricing });

    if (details.length > 0) {
        detailsHtml = `
            <div class="modal-details">
                ${details.map(d => `
                    <div class="modal-detail-row">
                        <span class="modal-detail-label">${d.label}</span>
                        <span class="modal-detail-value">${d.value}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    elements.modalContent.innerHTML = `
        <div class="modal-header">
            <div class="modal-logo">${logoMarkup}</div>
            <div class="modal-title-block">
                <h2 class="modal-title" id="modalTitle">${name}</h2>
                <div class="modal-categories">${categoriesHtml}</div>
            </div>
            <button class="modal-favorite-btn ${isFav ? 'is-favorited' : ''}"
                    data-product-key="${productKey}"
                    onclick="toggleFavoriteFromModal(event)">
                ${isFav ? '❤️ 已收藏' : '🤍 收藏'}
            </button>
        </div>

        <p class="modal-description">${description}</p>

        ${whyMatters ? `
            <div class="modal-why-matters">
                <div class="modal-why-matters-title">💡 为什么值得关注</div>
                <div class="modal-why-matters-text">${whyMatters}</div>
            </div>
        ` : ''}

        ${statsHtml}
        ${detailsHtml}

        <div class="modal-actions">
            ${website ? `<a class="modal-action-btn modal-action-btn--primary" href="${website}" target="_blank" rel="noopener noreferrer">访问官网 →</a>` : ''}
            <button class="modal-action-btn modal-action-btn--secondary" onclick="closeModal()">关闭</button>
        </div>
    `;

    // Store current product for favorite toggle
    elements.modalContent._currentProduct = product;

    elements.productModal.classList.add('is-open');
    elements.productModal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    if (!elements.productModal) return;
    elements.productModal.classList.remove('is-open');
    elements.productModal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
}

/* exported toggleFavoriteFromModal */
function toggleFavoriteFromModal(event) {
    event.stopPropagation();
    const product = elements.modalContent?._currentProduct;
    if (product) {
        toggleFavorite(product, event);
        // Update modal button
        const btn = event.target.closest('.modal-favorite-btn');
        if (btn) {
            const isFav = isFavorited(getProductKey(product));
            btn.classList.toggle('is-favorited', isFav);
            btn.innerHTML = isFav ? '❤️ 已收藏' : '🤍 收藏';
        }
    }
}

// ========== Updated Product Card with Favorite Button ==========
function createProductCardWithFavorite(product, showBadge = false) {
    const categories = product.categories || [];
    const categoryTags = categories.slice(0, 2).map(cat =>
        `<span class="product-tag">${getCategoryName(cat)}</span>`
    ).join('');

    const name = product.name || '未命名';
    const fundingTotal = product.funding_total || '';
    const whyMatters = product.why_matters || '';
    const description = product.description || '暂无描述';
    const rating = product.rating ? product.rating.toFixed(1) : 'N/A';
    const users = formatNumber(product.weekly_users);
    const cardClass = showBadge ? 'product-card product-card--hot' : 'product-card';
    const logoMarkup = buildLogoMarkup(product);
    const productKey = getProductKey(product);
    const isFav = isFavorited(productKey);

    return `
        <div class="${cardClass}" onclick="handleProductClick(event, '${encodeURIComponent(JSON.stringify(product).replace(/'/g, "\\'"))}')">
            <button class="product-favorite-btn ${isFav ? 'is-favorited' : ''}"
                    data-product-key="${productKey}"
                    onclick="handleFavoriteClick(event, '${encodeURIComponent(JSON.stringify(product).replace(/'/g, "\\'"))}')">
                ${isFav ? '❤️' : '🤍'}
            </button>
            <div class="product-logo">
                ${logoMarkup}
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${name}</h3>
                    ${showBadge ? `<span class="product-badge">🔥 热门</span>` : ''}
                </div>
                <p class="product-description">${description}</p>
                ${(whyMatters || fundingTotal) ? `
                <div class="product-insights">
                    ${whyMatters ? `<div class="product-insight">💡 ${whyMatters}</div>` : ''}
                    ${fundingTotal ? `<div class="product-insight product-insight--funding">💰 ${fundingTotal}</div>` : ''}
                </div>` : ''}
                <div class="product-meta">
                    <span class="product-meta-item">⭐ ${rating}</span>
                    <span class="product-meta-item">👥 ${users}</span>
                </div>
                <div class="product-tags">
                    ${categoryTags}
                </div>
            </div>
        </div>
    `;
}

/* exported handleProductClick, handleFavoriteClick */
function handleProductClick(event, encodedProduct) {
    // Don't open modal if clicking on favorite button
    if (event.target.closest('.product-favorite-btn')) {
        return;
    }

    try {
        const product = JSON.parse(decodeURIComponent(encodedProduct));
        openModal(product);
    } catch (e) {
        console.error('Failed to parse product data:', e);
    }
}

function handleFavoriteClick(event, encodedProduct) {
    event.stopPropagation();
    try {
        const product = JSON.parse(decodeURIComponent(encodedProduct));
        toggleFavorite(product, event);
    } catch (e) {
        console.error('Failed to parse product data:', e);
    }
}
