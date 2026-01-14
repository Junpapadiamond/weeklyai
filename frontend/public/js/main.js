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
let currentSection = 'trending';

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
    trendingSection: document.getElementById('trendingSection'),
    weeklySection: document.getElementById('weeklySection'),
    blogsSection: document.getElementById('blogsSection'),
    blogsList: document.getElementById('blogsList'),
    blogFilters: document.getElementById('blogFilters'),
    searchSection: document.getElementById('searchSection'),
    trendingProducts: document.getElementById('trendingProducts'),
    weeklyProducts: document.getElementById('weeklyProducts'),
    searchResults: document.getElementById('searchResults'),
    searchResultInfo: document.getElementById('searchResultInfo'),
    navLinks: document.querySelectorAll('.nav-link')
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
    loadTrendingProducts();
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
    elements.trendingSection.style.display = section === 'trending' ? 'block' : 'none';
    if (elements.discoverSection) {
        elements.discoverSection.style.display = section === 'trending' ? 'block' : 'none';
    }
    elements.weeklySection.style.display = section === 'weekly' ? 'block' : 'none';
    if (elements.blogsSection) {
        elements.blogsSection.style.display = section === 'blogs' ? 'block' : 'none';
    }
    elements.searchSection.style.display = section === 'search' ? 'block' : 'none';

    currentSection = section;

    // 加载对应数据
    if (section === 'trending') {
        loadTrendingProducts();
    } else if (section === 'weekly') {
        loadWeeklyProducts();
    } else if (section === 'blogs') {
        loadBlogs();
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
    const categories = (product.categories || []).slice(0, 2).map(getCategoryName).join(' · ');
    const website = product.website || '';

    // Clean and truncate description - remove technical noise
    let description = product.description || '暂无描述';
    description = cleanDescription(description);

    // Show source badge for new/trending items
    const source = product.source || '';
    const isNew = isRecentProduct(product);
    const sourceBadge = getSourceBadge(source, isNew);

    const logoMarkup = product.logo_url
        ? `<img src="${product.logo_url}" alt="${product.name}" onerror="this.parentElement.innerHTML='<div class=\\'product-logo-placeholder\\'>${product.name.charAt(0)}</div>'">`
        : `<div class="product-logo-placeholder">${product.name.charAt(0)}</div>`;

    const videoPreview = getVideoPreview(product);

    return `
        <div class="swipe-card ${position === 0 ? 'is-active' : ''}" data-pos="${position}" data-website="${website}">
            <div class="swipe-card-header">
                <div class="swipe-card-logo">${logoMarkup}</div>
                <div class="swipe-card-title">
                    <h3>${product.name}</h3>
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
        .replace(/Hugging Face (模型|Space): [^\|]+\|/g, '')
        .replace(/\| ⭐ [\d.]+K?\+? Stars/g, '')
        .replace(/\| 技术: .+$/g, '')
        .replace(/\| 下载量: .+$/g, '')
        .replace(/^\s*[\|·]\s*/g, '')
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
        'github': '<span class="swipe-badge">⭐ GitHub</span>',
        'huggingface': '<span class="swipe-badge">🤗 HF</span>',
        'huggingface_spaces': '<span class="swipe-badge">🤗 Space</span>',
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
    elements.trendingProducts.innerHTML = products.map(product => 
        createProductCard(product, true)
    ).join('');
    
    animateCards(elements.trendingProducts);
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
        'reddit': '🔴 Reddit',
        'github': '⭐ GitHub'
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

// ========== 创建产品卡片 ==========
function createProductCard(product, showBadge = false) {
    const categories = product.categories || [];
    const categoryTags = categories.slice(0, 2).map(cat => 
        `<span class="product-tag">${getCategoryName(cat)}</span>`
    ).join('');
    
    const rating = product.rating ? product.rating.toFixed(1) : 'N/A';
    const users = formatNumber(product.weekly_users);
    const cardClass = showBadge ? 'product-card product-card--hot' : 'product-card';
    
    return `
        <div class="${cardClass}" onclick="openProduct('${product.website}')">
            <div class="product-logo">
                ${product.logo_url 
                    ? `<img src="${product.logo_url}" alt="${product.name}" onerror="this.parentElement.innerHTML='<div class=\\'product-logo-placeholder\\'>${product.name.charAt(0)}</div>'">`
                    : `<div class="product-logo-placeholder">${product.name.charAt(0)}</div>`
                }
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${product.name}</h3>
                    ${showBadge ? `<span class="product-badge">🔥 热门</span>` : ''}
                </div>
                <p class="product-description">${product.description}</p>
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
    const users = formatNumber(product.weekly_users);
    
    return `
        <div class="product-list-item" onclick="openProduct('${product.website}')">
            <div class="product-rank ${rank <= 3 ? 'top-3' : ''}">${rank}</div>
            <div class="product-list-logo">
                ${product.logo_url 
                    ? `<img src="${product.logo_url}" alt="${product.name}" onerror="this.parentElement.innerHTML='<div class=\\'product-logo-placeholder\\'>${product.name.charAt(0)}</div>'">`
                    : `<div class="product-logo-placeholder">${product.name.charAt(0)}</div>`
                }
            </div>
            <div class="product-list-info">
                <h3 class="product-list-name">${product.name}</h3>
                <p class="product-list-desc">${product.description}</p>
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

// ========== 模拟数据 (当API不可用时使用) ==========
function getMockTrendingProducts() {
    return [
        {
            _id: '1',
            name: 'ChatGPT',
            description: 'OpenAI开发的大型语言模型，能够进行自然对话、写作、编程辅助等多种任务。',
            logo_url: 'https://cdn.openai.com/common/images/favicon.ico',
            website: 'https://chat.openai.com',
            categories: ['coding', 'writing'],
            rating: 4.8,
            weekly_users: 1500000,
            trending_score: 98
        },
        {
            _id: '3',
            name: 'Midjourney',
            description: '强大的AI图像生成工具，通过文本描述生成高质量艺术图像。',
            logo_url: 'https://www.midjourney.com/apple-touch-icon.png',
            website: 'https://midjourney.com',
            categories: ['image'],
            rating: 4.9,
            weekly_users: 1200000,
            trending_score: 96
        },
        {
            _id: '2',
            name: 'Claude',
            description: 'Anthropic开发的AI助手，以安全、有帮助和诚实为核心设计理念。',
            logo_url: 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
            website: 'https://claude.ai',
            categories: ['coding', 'writing'],
            rating: 4.7,
            weekly_users: 800000,
            trending_score: 95
        },
        {
            _id: '16',
            name: 'Cursor',
            description: 'AI增强的代码编辑器，内置智能代码补全和对话式编程功能。',
            logo_url: 'https://cursor.sh/favicon.ico',
            website: 'https://cursor.sh',
            categories: ['coding'],
            rating: 4.8,
            weekly_users: 420000,
            trending_score: 94
        },
        {
            _id: '6',
            name: 'NVIDIA H100',
            description: 'NVIDIA最新一代AI加速器，专为大规模AI训练和推理设计。',
            logo_url: 'https://www.nvidia.com/favicon.ico',
            website: 'https://www.nvidia.com/en-us/data-center/h100/',
            categories: ['hardware'],
            rating: 4.9,
            weekly_users: 50000,
            trending_score: 94
        }
    ];
}

function getMockWeeklyProducts() {
    return [
        { _id: '1', name: 'ChatGPT', description: 'OpenAI开发的大型语言模型，能够进行自然对话、写作、编程辅助等多种任务。', logo_url: 'https://cdn.openai.com/common/images/favicon.ico', website: 'https://chat.openai.com', categories: ['coding', 'writing'], rating: 4.8, weekly_users: 1500000 },
        { _id: '3', name: 'Midjourney', description: '强大的AI图像生成工具，通过文本描述生成高质量艺术图像。', logo_url: 'https://www.midjourney.com/apple-touch-icon.png', website: 'https://midjourney.com', categories: ['image'], rating: 4.9, weekly_users: 1200000 },
        { _id: '13', name: 'Google Gemini', description: 'Google最新的多模态AI模型，整合文本、图像、音频理解能力。', logo_url: 'https://www.google.com/favicon.ico', website: 'https://gemini.google.com', categories: ['coding', 'writing', 'image'], rating: 4.5, weekly_users: 1100000 },
        { _id: '4', name: 'GitHub Copilot', description: 'GitHub与OpenAI合作开发的AI编程助手，提供智能代码补全和建议。', logo_url: 'https://github.githubassets.com/favicons/favicon.png', website: 'https://github.com/features/copilot', categories: ['coding'], rating: 4.6, weekly_users: 950000 },
        { _id: '12', name: 'Stable Diffusion', description: '开源的AI图像生成模型，支持本地部署和自定义训练。', logo_url: 'https://stability.ai/favicon.ico', website: 'https://stability.ai', categories: ['image'], rating: 4.6, weekly_users: 890000 },
        { _id: '2', name: 'Claude', description: 'Anthropic开发的AI助手，以安全、有帮助和诚实为核心设计理念。', logo_url: 'https://www.anthropic.com/images/icons/apple-touch-icon.png', website: 'https://claude.ai', categories: ['coding', 'writing'], rating: 4.7, weekly_users: 800000 },
        { _id: '14', name: 'Hugging Face', description: '开源AI社区平台，提供模型托管、数据集和机器学习工具。', logo_url: 'https://huggingface.co/favicon.ico', website: 'https://huggingface.co', categories: ['coding', 'other'], rating: 4.8, weekly_users: 750000 },
        { _id: '7', name: 'Perplexity AI', description: 'AI驱动的搜索引擎，提供带引用来源的答案。', logo_url: 'https://www.perplexity.ai/favicon.ico', website: 'https://perplexity.ai', categories: ['other'], rating: 4.5, weekly_users: 700000 },
        { _id: '19', name: 'Duolingo Max', description: '使用GPT-4增强的语言学习平台，提供AI对话练习功能。', logo_url: 'https://www.duolingo.com/favicon.ico', website: 'https://www.duolingo.com/max', categories: ['education'], rating: 4.6, weekly_users: 650000 },
        { _id: '5', name: 'Eleven Labs', description: '领先的AI语音合成平台，提供逼真的文字转语音和语音克隆功能。', logo_url: 'https://elevenlabs.io/favicon.ico', website: 'https://elevenlabs.io', categories: ['voice'], rating: 4.7, weekly_users: 600000 },
        { _id: '10', name: 'Whisper', description: 'OpenAI开源的语音识别模型，支持多语言转录和翻译。', logo_url: 'https://openai.com/favicon.ico', website: 'https://openai.com/research/whisper', categories: ['voice'], rating: 4.7, weekly_users: 520000 },
        { _id: '8', name: 'Runway ML', description: '创意AI工具套件，提供视频生成、编辑和特效功能。', logo_url: 'https://runwayml.com/favicon.ico', website: 'https://runwayml.com', categories: ['video', 'image'], rating: 4.6, weekly_users: 450000 },
        { _id: '16', name: 'Cursor', description: 'AI增强的代码编辑器，内置智能代码补全和对话式编程功能。', logo_url: 'https://cursor.sh/favicon.ico', website: 'https://cursor.sh', categories: ['coding'], rating: 4.8, weekly_users: 420000 },
        { _id: '9', name: 'Jasper AI', description: '企业级AI写作助手，帮助创建营销内容和商业文案。', logo_url: 'https://jasper.ai/favicon.ico', website: 'https://jasper.ai', categories: ['writing'], rating: 4.4, weekly_users: 380000 },
        { _id: '20', name: 'Sora', description: 'OpenAI的文本到视频生成模型，能创建高质量的视频内容。', logo_url: 'https://openai.com/favicon.ico', website: 'https://openai.com/sora', categories: ['video'], rating: 4.8, weekly_users: 300000 }
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


