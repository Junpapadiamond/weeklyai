/**
 * WeeklyAI - 主JavaScript文件
 * 处理页面交互和API调用
 */

// API 基础URL
const API_BASE_URL = window.__API_BASE_URL__ || (
    window.location.hostname === 'localhost'
        ? 'http://localhost:5000/api/v1'
        : '/api/v1'
);
const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// 当前选中的分类
let selectedCategories = new Set();

// 当前显示的section
let hasDarkhorseData = true;

// Sort and filter state
let currentSort = 'score';
let currentTypeFilter = 'all';
let currentDirectionFilter = 'all';

// Favorites stored in localStorage
const FAVORITES_KEY = 'weeklyai_favorites';

// Swiped products tracking (to avoid duplicates)
const SWIPED_KEY = 'weeklyai_swiped';
const SWIPED_EXPIRY_DAYS = 7; // Reset swiped history after 7 days

const INVALID_WEBSITE_VALUES = new Set(['unknown', 'n/a', 'na', 'none', 'null', 'undefined', '']);
const PLACEHOLDER_VALUES = new Set(['unknown', 'n/a', 'na', 'none', 'tbd', '暂无', '未公开', '待定', 'unknown.', 'n/a.']);

// All products cache for sorting/filtering
let allProductsCache = [];
let discoveryAllProducts = [];

// Dark horse products cache
let darkHorseCache = [];
let darkHorseFilter = 'all'; // all, hardware, software

// Discover filter
let discoverFilter = 'all';

// Tier filter for trending section
let currentTier = 'all'; // all, darkhorse, rising

// Pagination
let currentPage = 1;
const PRODUCTS_PER_PAGE = 12;

// Favorites panel filters
let favoritesTypeFilter = 'all'; // all / product / blog
let favoritesSubFilter = 'all';

// Industry leaders
const LEADERS_CATEGORY_ORDER = [
    '通用大模型',
    '中国大模型',
    '搜索引擎',
    '写作助手',
    '图像生成',
    '视频生成',
    '语音合成',
    '代码开发',
    '开发者工具',
    'AI角色/伴侣'
];
let leadersCategoriesData = null;
let leadersActiveFilter = 'all';

const CATEGORY_ALIASES = {
    'ai coding': 'coding',
    'ai 基础设施': 'other',
    'ai 硬件': 'hardware',
    'ai 客服': 'agent',
    'enterprise': 'other',
    'world model': 'vision'
};

const DIRECTION_META = {
    voice: { label: '🎤 语音', tag: '语音' },
    vision: { label: '👁️ 视觉', tag: '视觉' },
    driving: { label: '🚗 驾驶', tag: '驾驶' },
    robotics: { label: '🤖 机器人', tag: '机器人' },
    chip: { label: '🧠 芯片/算力', tag: '芯片/算力' },
    agent: { label: '🧩 Agent', tag: 'Agent' },
    coding: { label: '💻 编程开发', tag: '编程' },
    writing: { label: '✍️ 写作内容', tag: '写作' },
    finance: { label: '💰 金融科技', tag: '金融' },
    healthcare: { label: '🏥 医疗健康', tag: '医疗' },
    education: { label: '📚 教育学习', tag: '教育' }
};

const DIRECTION_ORDER = [
    'voice',
    'vision',
    'driving',
    'robotics',
    'chip',
    'agent',
    'coding',
    'writing',
    'finance',
    'healthcare',
    'education'
];

const DIRECTION_CORE_KEYS = ['voice', 'vision', 'driving'];

function normalizeWebsite(url) {
    if (!url) return '';
    const trimmed = String(url).trim();
    if (!trimmed) return '';
    const lower = trimmed.toLowerCase();
    if (INVALID_WEBSITE_VALUES.has(lower)) return '';
    if (!/^https?:\/\//i.test(trimmed) && trimmed.includes('.')) {
        return `https://${trimmed}`;
    }
    return trimmed;
}

function isValidWebsite(url) {
    const normalized = normalizeWebsite(url);
    if (!normalized) return false;
    if (!/^https?:\/\//i.test(normalized)) return false;
    return true;
}

function isPlaceholderValue(value) {
    if (!value) return true;
    const normalized = String(value).trim().toLowerCase();
    if (!normalized) return true;
    return PLACEHOLDER_VALUES.has(normalized);
}

function normalizeCategoryId(value) {
    if (!value) return '';
    const normalized = String(value).trim().toLowerCase();
    if (!normalized) return '';
    return CATEGORY_ALIASES[normalized] || normalized;
}

function getNormalizedProductCategories(product) {
    const rawCategories = Array.isArray(product.categories) ? product.categories : [];
    const categorySet = new Set();

    rawCategories.forEach((cat) => {
        const normalized = normalizeCategoryId(cat);
        if (normalized) categorySet.add(normalized);
    });

    const primary = normalizeCategoryId(product.category);
    if (primary) categorySet.add(primary);

    return categorySet;
}

function getProductCorpusText(product) {
    const rawCategories = Array.isArray(product.categories) ? product.categories : [];
    return [
        product.name,
        product.description,
        product.why_matters,
        product.latest_news,
        product.search_keyword,
        product.hardware_category,
        product.use_case,
        product.form_factor,
        ...rawCategories,
        product.category
    ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
}

function isHardwareProduct(product) {
    if (!product) return false;

    const categories = getNormalizedProductCategories(product);
    if (product.is_hardware || categories.has('hardware')) return true;

    if (product.hardware_category) return true;

    const text = getProductCorpusText(product);
    return /(chip|semiconductor|robot|robotics|humanoid|drone|wearable|hardware|硬件|芯片|机器人|眼镜|吊坠|ring|glasses)/i.test(text);
}

function inferProductDirections(product) {
    const categories = getNormalizedProductCategories(product);
    const text = getProductCorpusText(product);
    const hardwareCategory = String(product.hardware_category || '').toLowerCase();
    const useCase = String(product.use_case || '').toLowerCase();
    const directions = [];

    if (
        categories.has('voice') ||
        /voice|audio|speech|asr|tts|podcast|call|phone|语音|音频|语音识别|语音合成/.test(text)
    ) {
        directions.push('voice');
    }

    if (
        categories.has('image') ||
        categories.has('video') ||
        categories.has('vision') ||
        /\bvision\b|\bvisual\b|\bimage\b|\bvideo\b|\bcamera\b|\bocr\b|\bmultimodal\b|\bar\b|\bvr\b|\bglasses\b|图像|视觉|视频|相机|识别|多模态|眼镜/.test(text)
    ) {
        directions.push('vision');
    }

    if (
        /\bdrive\b|\bdriving\b|autonomous|self-driving|adas|vehicle|车载|自动驾驶|无人驾驶|智驾/.test(text)
    ) {
        directions.push('driving');
    }

    if (
        hardwareCategory === 'robotics' ||
        /robot|robotics|humanoid|embodied|具身|机器人/.test(text)
    ) {
        directions.push('robotics');
    }

    if (
        hardwareCategory === 'ai_chip' ||
        hardwareCategory === 'edge_ai' ||
        /chip|semiconductor|gpu|npu|edge ai|芯片|半导体|算力/.test(text)
    ) {
        directions.push('chip');
    }

    if (
        categories.has('agent') ||
        /agent|workflow|automation|assistant|copilot|智能体|自动化|代理/.test(text)
    ) {
        directions.push('agent');
    }

    if (
        categories.has('coding') ||
        /\bcode\b|\bcoding\b|\bdeveloper\b|devtool|\bide\b|programming|编程|开发|代码|开发者/.test(text)
    ) {
        directions.push('coding');
    }

    if (
        categories.has('writing') ||
        /writing|copywriting|content|blog|文案|写作|内容创作/.test(text)
    ) {
        directions.push('writing');
    }

    if (
        categories.has('finance') ||
        /finance|fintech|trading|bank|payment|金融|理财|投顾/.test(text)
    ) {
        directions.push('finance');
    }

    if (
        categories.has('healthcare') ||
        useCase === 'health_monitoring' ||
        /health|medical|clinic|hospital|医疗|健康|诊疗/.test(text)
    ) {
        directions.push('healthcare');
    }

    if (
        categories.has('education') ||
        /education|learning|tutor|classroom|课程|教育|学习|教学/.test(text)
    ) {
        directions.push('education');
    }

    return Array.from(new Set(directions));
}

function getDirectionLabel(directionKey) {
    return DIRECTION_META[directionKey]?.label || directionKey;
}

function getDirectionTagName(directionKey) {
    return DIRECTION_META[directionKey]?.tag || directionKey;
}

function syncDirectionFilterOptions(products) {
    if (!elements.directionFilter) return;

    const directionCounts = {};
    products.forEach((product) => {
        inferProductDirections(product).forEach((direction) => {
            directionCounts[direction] = (directionCounts[direction] || 0) + 1;
        });
    });

    const availableDirections = DIRECTION_ORDER.filter((direction) => {
        return DIRECTION_CORE_KEYS.includes(direction) || (directionCounts[direction] || 0) > 0;
    });

    const optionsHtml = [
        '<option value="all">全部方向</option>',
        ...availableDirections.map((direction) => {
            const count = directionCounts[direction] || 0;
            const suffix = count > 0 ? ` (${count})` : '';
            return `<option value="${direction}">${getDirectionLabel(direction)}${suffix}</option>`;
        })
    ].join('');

    elements.directionFilter.innerHTML = optionsHtml;

    if (currentDirectionFilter !== 'all' && !availableDirections.includes(currentDirectionFilter)) {
        currentDirectionFilter = 'all';
    }
    elements.directionFilter.value = currentDirectionFilter;
}

function applyTierFilter(products) {
    if (currentTier === 'darkhorse') {
        return products.filter((p) => (p.dark_horse_index || 0) >= 4);
    }
    if (currentTier === 'rising') {
        return products.filter((p) => {
            const score = p.dark_horse_index || 0;
            return score >= 2 && score <= 3;
        });
    }
    return products;
}

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
    directionFilter: document.getElementById('directionFilter'),
    showFavoritesBtn: document.getElementById('showFavoritesBtn'),
    favoritesCount: document.getElementById('favoritesCount'),
    // Modal
    productModal: document.getElementById('productModal'),
    modalClose: document.getElementById('modalClose'),
    modalContent: document.getElementById('modalContent'),
    // Favorites panel
    favoritesPanel: document.getElementById('favoritesPanel'),
    favoritesClose: document.getElementById('favoritesClose'),
    favoritesControls: document.getElementById('favoritesControls'),
    favoritesTypeTabs: document.getElementById('favoritesTypeTabs'),
    favoritesSubfilters: document.getElementById('favoritesSubfilters'),
    favoritesList: document.getElementById('favoritesList'),
    // Industry leaders
    leadersSection: document.getElementById('leadersSection'),
    leadersFilters: document.getElementById('leadersFilters'),
    leadersCategories: document.getElementById('leadersCategories')
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    initLucide();
    initThemeToggle();
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
    initDarkhorseFilters();
    initDiscoverFilters();
    initTierTabs();
    initLoadMore();
    loadDataFreshness();
    loadDarkHorseProducts();
    loadTrendingProducts();
    loadIndustryLeaders();
    handleInitialRoute();
    updateFavoritesCount();
});

// ========== Lucide Icons ==========
// Debounced icon refresh to avoid multiple rapid createIcons calls
let lucideRefreshTimer = null;
let lucideInitialized = false;

function initLucide() {
    if (typeof lucide !== 'undefined' && !lucideInitialized) {
        lucide.createIcons();
        lucideInitialized = true;
    }
}

/**
 * Debounced function to refresh Lucide icons after DOM updates.
 * Call this after dynamically adding content with Lucide icons.
 * Uses a 50ms debounce to batch rapid updates.
 */
function refreshIcons() {
    if (typeof lucide === 'undefined') return;

    if (lucideRefreshTimer) {
        clearTimeout(lucideRefreshTimer);
    }

    lucideRefreshTimer = setTimeout(() => {
        lucide.createIcons();
        lucideRefreshTimer = null;
    }, 50);
}

// ========== Theme Toggle ==========
const THEME_KEY = 'weeklyai_theme';

function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;

    // Load saved theme or respect system preference
    const savedTheme = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    setTheme(initialTheme);

    toggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        localStorage.setItem(THEME_KEY, newTheme);
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    const lightIcon = document.querySelector('.theme-icon-light');
    const darkIcon = document.querySelector('.theme-icon-dark');

    if (lightIcon && darkIcon) {
        if (theme === 'dark') {
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'block';
        } else {
            lightIcon.style.display = 'block';
            darkIcon.style.display = 'none';
        }
    }
}

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
    if (elements.leadersSection) {
        elements.leadersSection.style.display = section === 'leaders' ? 'block' : 'none';
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
    } else if (section === 'leaders') {
        loadIndustryLeaders();
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
    skipped: 0
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
        const response = await fetch(`${API_BASE_URL}/products/weekly-top?limit=0`);
        const data = await response.json();

        const products = mergeUniqueProducts([
            ...(data.success ? data.data : [])
        ]);

        discoveryAllProducts = products.length ? products : getMockWeeklyProducts();
        loadDiscoveryCards();
    } catch (error) {
        console.error('加载发现产品失败:', error);
        discoveryAllProducts = getMockWeeklyProducts();
        loadDiscoveryCards();
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

function filterDiscoveryProducts(products) {
    if (discoverFilter === 'all') return products;
    return products.filter(product => {
        const categories = product.categories || [];
        const category = product.category;
        if (discoverFilter === 'hardware') {
            return categories.includes('hardware') || category === 'hardware' || product.is_hardware;
        }
        return categories.includes(discoverFilter) || category === discoverFilter;
    });
}

function loadDiscoveryCards() {
    const filtered = filterDiscoveryProducts(discoveryAllProducts);
    if (discoveryAllProducts.length === 0) {
        buildDiscoveryDeck(getMockWeeklyProducts());
        return;
    }
    buildDiscoveryDeck(filtered);
}

function shuffleArray(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

// ========== Swiped Products Tracking ==========
function getSwipedProducts() {
    try {
        const stored = localStorage.getItem(SWIPED_KEY);
        if (!stored) return { keys: [], timestamp: Date.now() };
        const data = JSON.parse(stored);
        // Check if expired (older than SWIPED_EXPIRY_DAYS)
        const expiryMs = SWIPED_EXPIRY_DAYS * 24 * 60 * 60 * 1000;
        if (Date.now() - data.timestamp > expiryMs) {
            clearSwipedProducts();
            return { keys: [], timestamp: Date.now() };
        }
        return data;
    } catch {
        return { keys: [], timestamp: Date.now() };
    }
}

function addSwipedProduct(productKey) {
    if (!productKey) return;
    const data = getSwipedProducts();
    if (!data.keys.includes(productKey)) {
        data.keys.push(productKey);
        saveSwipedProducts(data);
    }
}

// Debounced localStorage writes to batch rapid updates
let swipedSaveTimer = null;
let pendingSwipedData = null;

function saveSwipedProducts(data) {
    pendingSwipedData = data;

    if (swipedSaveTimer) {
        clearTimeout(swipedSaveTimer);
    }

    swipedSaveTimer = setTimeout(() => {
        try {
            if (pendingSwipedData) {
                localStorage.setItem(SWIPED_KEY, JSON.stringify(pendingSwipedData));
                pendingSwipedData = null;
            }
        } catch (e) {
            console.error('Failed to save swiped products:', e);
        }
        swipedSaveTimer = null;
    }, 500);
}

function clearSwipedProducts() {
    try {
        localStorage.removeItem(SWIPED_KEY);
    } catch (e) {
        console.error('Failed to clear swiped products:', e);
    }
}

function isProductSwiped(productKey) {
    const data = getSwipedProducts();
    return data.keys.includes(productKey);
}

function buildDiscoveryDeck(products) {
    // Filter out already-swiped products
    let availableProducts = products.filter(p => {
        const key = getProductKey(p);
        return key && !isProductSwiped(key);
    });

    // If all products have been swiped, reset and start fresh
    if (availableProducts.length === 0) {
        clearSwipedProducts();
        availableProducts = [...products];
    }

    discoveryState.pool = shuffleArray([...availableProducts]);
    discoveryState.stack = [];
    discoveryState.liked = 0;
    discoveryState.skipped = 0;

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
    // Simply take the first product (pool is already shuffled in buildDiscoveryDeck)
    return discoveryState.pool.shift();
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
    refreshIcons();

    const activeCard = elements.swipeStack.querySelector('.swipe-card.is-active');
    if (activeCard) {
        attachSwipeHandlers(activeCard);
    }
}

function createSwipeCard(product, position) {
    const name = product.name || '未命名';
    const categories = (product.categories || []).slice(0, 2).map(getCategoryName).join(' · ');
    const website = normalizeWebsite(product.website || '');
    const hasWebsite = isValidWebsite(website);
    const productKey = getProductKey(product);
    const isFav = isFavorited(productKey);
    const encodedProduct = encodeURIComponent(JSON.stringify(product).replace(/'/g, "\\'"));

    // Clean and truncate description - remove technical noise
    let description = product.description || '暂无描述';
    description = cleanDescription(description);

    // Show source badge for new/trending items
    const source = product.source || '';
    const isNew = isRecentProduct(product);
    const sourceBadge = getSourceBadge(source, isNew);

    const logoMarkup = buildLogoMarkup(product);
    const screenshotMarkup = buildWebsiteScreenshotMarkup(product, { className: 'swipe-media', width: 920 });

    const videoPreview = getVideoPreview(product);

    const highlights = [];
    if (product.why_matters) {
        highlights.push(`💡 ${product.why_matters}`);
    }
    if (product.funding_total && !isPlaceholderValue(product.funding_total)) {
        highlights.push(`💰 ${product.funding_total}`);
    }
    if (product.latest_news && !isPlaceholderValue(product.latest_news)) {
        highlights.push(`📰 ${product.latest_news}`);
    }
    const highlightsMarkup = highlights.length
        ? `<div class="swipe-card-highlights">${highlights.slice(0, 2).map(item => `<div class="swipe-card-highlight">${item}</div>`).join('')}</div>`
        : '';

    const pendingBadge = hasWebsite ? '' : '<span class="swipe-link swipe-link--pending">官网待验证</span>';

    return `
        <div class="swipe-card ${position === 0 ? 'is-active' : ''} ${hasWebsite ? '' : 'swipe-card--no-link'}" data-pos="${position}" data-website="${website}">
            <div class="swipe-card-header">
                <div class="swipe-card-logo">${logoMarkup}</div>
                <div class="swipe-card-title">
                    <h3>${name}</h3>
                    <p>${categories || '精选 AI 工具'}</p>
                </div>
                ${sourceBadge}
                <button class="card-favorite-btn swipe-favorite-btn ${isFav ? 'is-favorited' : ''}"
                        data-product-key="${productKey}"
                        onclick="handleSwipeFavoriteClick(event, '${encodedProduct}')"
                        title="收藏">
                    ${isFav ? '❤️' : '🤍'}
                </button>
            </div>
            ${screenshotMarkup}
            <p class="swipe-card-desc">${description}</p>
            ${highlightsMarkup}
            ${videoPreview}
            <div class="swipe-card-meta">
                ${hasWebsite ? `<a class="swipe-link" href="${website}" target="_blank" rel="noopener noreferrer">了解更多 →</a>` : pendingBadge}
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
            <img src="${videoThumbnail}" alt="Video preview" width="280" height="158" loading="lazy">
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

    const openWebsite = (event) => {
        if (event?.target?.closest && event.target.closest('a, button')) return;
        const website = card.dataset.website || '';
        if (isValidWebsite(website)) {
            window.open(website, '_blank', 'noopener,noreferrer');
        }
    };

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
        const clickThreshold = 8;
        if (currentX > threshold) {
            handleSwipe('right');
        } else if (currentX < -threshold) {
            handleSwipe('left');
        } else {
            card.style.transition = 'transform 0.25s ease';
            card.style.transform = '';
            if (Math.abs(currentX) < clickThreshold && Math.abs(currentY) < clickThreshold) {
                openWebsite(event);
            }
        }
    };

    card.addEventListener('pointerdown', (event) => {
        if (event.button !== 0) return;
        if (event.target?.closest && event.target.closest('a, button')) return;
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
    const productKey = getProductKey(product);

    // Track as swiped (both left and right) to avoid showing again
    addSwipedProduct(productKey);

    if (direction === 'right') {
        discoveryState.liked += 1;
        // 右滑即收藏，立即写入避免用户切页时丢失
        addFavoriteEntry(createProductFavoriteEntry(product), { immediate: true });
    } else {
        discoveryState.skipped += 1;
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
    if (!elements.categoryTags) return; // 已移除该区域

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
        const response = await fetch(`${API_BASE_URL}/products/weekly-top?limit=0`);
        const data = await response.json();

        allProductsCache = data.success ? data.data : getMockTrendingProducts();
        currentPage = 1;
        applyFiltersAndRender();

    } catch (error) {
        console.error('加载产品失败:', error);
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

// ========== 加载黑马产品 (4-5分) ==========
async function loadDarkHorseProducts() {
    if (!elements.darkhorseProducts) return;

    try {
        // 加载 4-5 分的黑马产品
        const response = await fetch(`${API_BASE_URL}/products/dark-horses?limit=10&min_index=4`);
        const data = await response.json();

        hasDarkhorseData = Boolean(data.success && data.data.length > 0);
        if (hasDarkhorseData) {
            darkHorseCache = data.data;
            renderDarkHorseProducts(filterDarkHorseByType(darkHorseCache, darkHorseFilter));
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

function filterDarkHorseByType(products, type) {
    if (type === 'all') return products;
    return products.filter(p => {
        const isHardware = isHardwareProduct(p);
        return type === 'hardware' ? isHardware : !isHardware;
    });
}

function renderDarkHorseProducts(products) {
    if (products.length === 0) {
        elements.darkhorseProducts.innerHTML = `
            <div class="empty-state">
                <p>暂无符合条件的黑马产品</p>
            </div>
        `;
        return;
    }

    elements.darkhorseProducts.innerHTML = products.map(product =>
        createDarkHorseCard(product)
    ).join('');

    animateDarkHorseCards(elements.darkhorseProducts);
}

// ========== 黑马筛选初始化 ==========
function initDarkhorseFilters() {
    const filterBtns = document.querySelectorAll('.darkhorse-filters .filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            darkHorseFilter = btn.dataset.type;
            renderDarkHorseProducts(filterDarkHorseByType(darkHorseCache, darkHorseFilter));
        });
    });
}

// ========== 快速发现筛选初始化 ==========
function initDiscoverFilters() {
    const filterBtns = document.querySelectorAll('.discover-filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            discoverFilter = btn.dataset.category;
            // 重新加载发现卡片
            loadDiscoveryCards();
        });
    });
}

// ========== Tier Tabs 初始化 ==========
function initTierTabs() {
    const tierTabs = document.querySelectorAll('.tier-tab');
    tierTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tierTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentTier = tab.dataset.tier;
            currentPage = 1;
            applyFiltersAndRender();
        });
    });
}

// ========== 加载更多 ==========
function initLoadMore() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            currentPage++;
            applyFiltersAndRender(true); // append mode
        });
    }
}

function applyFiltersAndRender(append = false) {
    let products = applyTierFilter([...allProductsCache]);

    // 一级分类筛选（软件/硬件）
    if (currentTypeFilter !== 'all') {
        products = products.filter((p) => {
            const isHardware = isHardwareProduct(p);
            return currentTypeFilter === 'hardware' ? isHardware : !isHardware;
        });
    }

    // 二级方向筛选（语音/视觉/驾驶等）
    syncDirectionFilterOptions(products);
    if (currentDirectionFilter !== 'all') {
        products = products.filter((p) => inferProductDirections(p).includes(currentDirectionFilter));
    }

    // 排序
    products = sortProducts(products, currentSort);

    // 分页
    const start = 0;
    const end = currentPage * PRODUCTS_PER_PAGE;
    const paginatedProducts = products.slice(start, end);

    // 渲染
    if (append) {
        const newCards = paginatedProducts.slice((currentPage - 1) * PRODUCTS_PER_PAGE);
        const container = elements.trendingProducts;
        newCards.forEach(product => {
            container.insertAdjacentHTML('beforeend', createProductCardWithFavorite(product, true));
        });
        animateCards(container);
    } else {
        renderTrendingProducts(paginatedProducts);
    }

    // 更新加载更多按钮状态
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.style.display = end >= products.length ? 'none' : 'block';
    }
}

function sortProducts(products, sortBy) {
    return products.sort((a, b) => {
        switch (sortBy) {
            case 'date':
                return new Date(b.discovered_at || 0) - new Date(a.discovered_at || 0);
            case 'funding':
                return parseFunding(b.funding_total) - parseFunding(a.funding_total);
            case 'score':
            default:
                // 排序规则: 评分 > 融资金额 > 用户数/估值

                // 1. 首先按评分排序 (5分 > 4分 > 3分...)
                const scoreA = a.dark_horse_index || 0;
                const scoreB = b.dark_horse_index || 0;
                if (scoreB !== scoreA) {
                    return scoreB - scoreA;
                }

                // 2. 同分时按融资金额排序
                const fundingA = parseFunding(a.funding_total);
                const fundingB = parseFunding(b.funding_total);
                if (fundingB !== fundingA) {
                    return fundingB - fundingA;
                }

                // 3. 融资相同时按用户数/估值排序
                const valuationA = parseValuation(a);
                const valuationB = parseValuation(b);
                return valuationB - valuationA;
        }
    });
}

function parseFunding(funding) {
    if (!funding || isPlaceholderValue(funding)) return 0;
    const match = funding.match(/\$?([\d.]+)\s*(M|B|K)?/i);
    if (!match) return 0;
    let value = parseFloat(match[1]);
    const unit = (match[2] || '').toUpperCase();
    if (unit === 'B') value *= 1000;
    if (unit === 'K') value /= 1000;
    return value;
}

function parseValuation(product) {
    // 优先使用估值
    const valuation = product.valuation || product.market_cap || '';
    if (valuation) {
        const match = valuation.toString().match(/\$?([\d.]+)\s*(M|B|K)?/i);
        if (match) {
            let value = parseFloat(match[1]);
            const unit = (match[2] || '').toUpperCase();
            if (unit === 'B') value *= 1000;
            if (unit === 'K') value /= 1000;
            return value * 10; // 估值权重更高
        }
    }

    // 其次使用用户数
    const users = product.weekly_users || product.users || product.monthly_users || 0;
    if (users > 0) {
        return users / 10000; // 转换为万用户
    }

    // 最后使用热度分数
    return product.hot_score || product.trending_score || product.final_score || 0;
}

function createDarkHorseCard(product) {
    const name = product.name || '未命名';
    const darkHorseIndex = product.dark_horse_index || 0;
    const stars = '★'.repeat(darkHorseIndex) + '☆'.repeat(5 - darkHorseIndex);
    const description = product.description || '暂无描述';
    const website = normalizeWebsite(product.website || '');
    const hasWebsite = isValidWebsite(website);
    const categories = product.categories || [];
    const whyMatters = product.why_matters || '';
    const funding = product.funding_total || '';
    const latestNews = product.latest_news || '';
    const region = product.region || '';
    const ratingLabel = darkHorseIndex > 0 ? `${darkHorseIndex} 分黑马` : '黑马推荐';
    const cardTierClass = darkHorseIndex >= 5 ? 'darkhorse-card--elite' : 'darkhorse-card--strong';

    // 判断是否为硬件产品
    const isHardware = isHardwareProduct(product);

    const categoryTags = categories.slice(0, 2).map(cat =>
        `<span class="darkhorse-tag">${getCategoryName(cat)}</span>`
    ).join('');

    const logoMarkup = buildLogoMarkup(product);
    const screenshotMarkup = buildWebsiteScreenshotMarkup(product, { className: 'darkhorse-media', width: 1100 });

    // 构建 meta 标签
    let metaTags = '';
    if (funding && !isPlaceholderValue(funding)) {
        metaTags += `<span class="darkhorse-meta-tag darkhorse-meta-tag--funding">
            <span class="meta-icon">💰</span>${funding}
        </span>`;
    }
    if (isHardware) {
        metaTags += `<span class="darkhorse-meta-tag darkhorse-meta-tag--hardware">
            <span class="meta-icon">🔧</span>硬件
        </span>`;
    }
    if (region) {
        metaTags += `<span class="darkhorse-meta-tag">
            <span class="meta-icon">${region}</span>
        </span>`;
    }
    if (!hasWebsite) {
        metaTags += `<span class="darkhorse-meta-tag darkhorse-meta-tag--verify">
            <span class="meta-icon">🔎</span>官网待验证
        </span>`;
    }

    const clickAttr = hasWebsite ? `onclick="openProduct('${website}')"` : '';

    return `
        <div class="darkhorse-card ${cardTierClass} ${hasWebsite ? '' : 'darkhorse-card--no-link'}" ${clickAttr}>
            ${screenshotMarkup}
            <div class="darkhorse-card-header">
                <div class="darkhorse-logo">${logoMarkup}</div>
                <div class="darkhorse-title-block">
                    <h3 class="darkhorse-name">${name}</h3>
                    <div class="darkhorse-rating" title="黑马指数 ${darkHorseIndex}/5">
                        <span class="darkhorse-score">${ratingLabel}</span>
                        <span class="darkhorse-stars">${stars}</span>
                    </div>
                </div>
            </div>
            <p class="darkhorse-description">${description}</p>
            ${categoryTags ? `<div class="darkhorse-tags">${categoryTags}</div>` : ''}
            ${whyMatters ? `<div class="darkhorse-why">${whyMatters}</div>` : ''}
            <div class="darkhorse-meta">
                ${metaTags}
            </div>
            ${latestNews ? `<div class="darkhorse-news">
                <span class="news-icon">📰</span>
                <span>${latestNews}</span>
            </div>` : ''}
            <div class="darkhorse-cta">
                <span class="darkhorse-link ${hasWebsite ? '' : 'darkhorse-link--pending'}">
                    ${hasWebsite ? '了解更多 →' : '官网待验证'}
                </span>
            </div>
        </div>
    `;
}

function animateDarkHorseCards(container) {
    // Reinitialize Lucide icons for dynamically added content
    refreshIcons();

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
        const response = await fetch(`${API_BASE_URL}/products/weekly-top?limit=15`);
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
    const website = normalizeWebsite(product.website || '');
    const hasWebsite = isValidWebsite(website);
    const categories = (product.categories || []).map(getCategoryName).join(' · ');
    const rating = product.rating ? product.rating.toFixed(1) : '';
    const users = product.weekly_users ? formatNumber(product.weekly_users) : '';
    const foundedDate = product.founded_date || '';
    const fundingTotal = product.funding_total || '';
    const whyMatters = product.why_matters || '';
    const latestNews = product.latest_news || '';
    const extra = product.extra || {};
    const signalsRaw = Array.isArray(extra.signals) ? extra.signals : [];
    const logoMarkup = buildLogoMarkup(product);

    const metaItems = [];
    if (categories) metaItems.push(`🏷️ ${categories}`);
    if (rating) metaItems.push(`⭐ ${rating}`);
    if (users) metaItems.push(`👥 ${users}`);
    if (foundedDate) metaItems.push(`📅 ${foundedDate}`);
    if (fundingTotal && !isPlaceholderValue(fundingTotal)) metaItems.push(`💰 ${fundingTotal}`);

    const signals = signalsRaw
        .filter(s => s && (s.url || s.title))
        .slice()
        .sort((a, b) => {
            const aDate = new Date(a.published_at || a.discovered_at || 0);
            const bDate = new Date(b.published_at || b.discovered_at || 0);
            return bDate - aDate;
        })
        .slice(0, 3);

    const evidenceMarkup = signals.length ? `
        <div class="product-detail-evidence">
            <h4 class="product-detail-evidence-title">证据链</h4>
            <div class="product-detail-evidence-list">
                ${signals.map(s => {
                    const platform = (s.platform || '').toLowerCase();
                    const icon = platform === 'youtube' ? '📺' : (platform === 'x' ? '𝕏' : '🔗');
                    const url = s.url || '#';
                    const title = s.title || url;
                    const author = s.author || '';
                    const dateStr = s.published_at || '';
                    const dateLabel = dateStr ? formatDate(dateStr) : '';
                    const meta = [author, dateLabel].filter(Boolean).join(' · ');
                    const snippet = s.snippet ? cleanDescription(s.snippet) : '';
                    return `
                        <div class="evidence-item">
                            <div class="evidence-item-header">
                                <span class="evidence-icon">${icon}</span>
                                <a class="evidence-link" href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
                            </div>
                            ${meta ? `<div class="evidence-meta">${meta}</div>` : ''}
                            ${snippet ? `<div class="evidence-snippet">${snippet}</div>` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    ` : '';

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
                ${hasWebsite ? `<a class="product-detail-link" href="${website}" target="_blank" rel="noopener noreferrer">${website}</a>` : '<span class="product-detail-link product-detail-link--pending">官网待验证</span>'}
                ${metaItems.length ? `<div class="product-detail-meta">${metaItems.map(item => `<span>${item}</span>`).join('')}</div>` : ''}
                ${whyMatters ? `<div class="product-detail-why">💡 ${whyMatters}</div>` : ''}
                ${latestNews ? `<div class="product-detail-latest">📰 ${latestNews}</div>` : ''}
                ${evidenceMarkup}
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
    const website = normalizeWebsite(blog.website || '');
    const hasWebsite = isValidWebsite(website);
    const extra = blog.extra || {};
    const points = extra.points || extra.votes || 0;
    const comments = extra.comments || 0;
    const blogKey = getBlogFavoriteKey(blog);
    const isFav = isFavorited(blogKey);
    const encodedBlog = encodeURIComponent(JSON.stringify(blog).replace(/'/g, "\\'"));

    // Format date
    const dateStr = blog.published_at || blog.first_seen || '';
    const dateLabel = dateStr ? formatDate(dateStr) : '';

    return `
        <div class="blog-item ${hasWebsite ? '' : 'blog-item--no-link'}" ${hasWebsite ? `onclick="openProduct('${website}')"` : ''}>
            <button class="card-favorite-btn blog-favorite-btn ${isFav ? 'is-favorited' : ''}"
                    data-product-key="${blogKey}"
                    onclick="toggleBlogFavorite(event, '${encodedBlog}')"
                    title="收藏">
                ${isFav ? '❤️' : '🤍'}
            </button>
            <div class="blog-source ${source}">${sourceLabel}</div>
            <div class="blog-content">
                <h3 class="blog-title">${blog.name}</h3>
                <p class="blog-desc">${description}</p>
                <div class="blog-meta">
                    ${points ? `<span class="blog-stat">👍 ${points}</span>` : ''}
                    ${comments ? `<span class="blog-stat">💬 ${comments}</span>` : ''}
                    ${dateLabel ? `<span class="blog-date">${dateLabel}</span>` : ''}
                    ${!hasWebsite ? '<span class="blog-date">官网待验证</span>' : ''}
                </div>
            </div>
        </div>
    `;
}

function getSourceLabel(source) {
    const labels = {
        'hackernews': '🔶 HN',
        'tech_news': '📰 News',
        'youtube': '📺 YouTube',
        'x': '𝕏 X',
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
    if (!isValidWebsite(website)) return '';
    try {
        const normalized = normalizeWebsite(website);
        const host = new URL(normalized).hostname;
        if (!host) return '';
        return `https://www.google.com/s2/favicons?domain=${host}&sz=128`;
    } catch {
        return '';
    }
}

function getLogoFallbacks(website) {
    const primary = normalizeWebsite(website);
    const candidate = isValidWebsite(primary) ? primary : '';
    if (!candidate) return [];
    try {
        const host = new URL(candidate).hostname;
        if (!host) return [];
        return [
            `https://logo.clearbit.com/${host}`,
            `https://www.google.com/s2/favicons?domain=${host}&sz=128`,
            `https://favicon.bing.com/favicon.ico?url=${host}&size=128`,
            `https://icons.duckduckgo.com/ip3/${host}.ico`,
            `https://icon.horse/icon/${host}`
        ];
    } catch {
        return [];
    }
}

function buildLogoMarkup(product, options = {}) {
    const name = product.name || 'AI';
    const initial = getInitial(name);
    const logoSrc = getLogoSource(product);
    const { width = 48, height = 48 } = options;
    const fallbacks = getLogoFallbacks(product.website || '');
    const filtered = fallbacks.filter(url => url && url !== logoSrc);
    const fallbackAttr = filtered.join('|');

    if (logoSrc) {
        return `<img src="${logoSrc}" alt="${name}" width="${width}" height="${height}" loading="lazy" data-fallbacks="${fallbackAttr}" data-initial="${initial}" onerror="handleLogoError(this)">`;
    }
    if (fallbackAttr) {
        const first = filtered[0];
        const rest = filtered.slice(1).join('|');
        return `<img src="${first}" alt="${name}" width="${width}" height="${height}" loading="lazy" data-fallbacks="${rest}" data-initial="${initial}" onerror="handleLogoError(this)">`;
    }
    return `<div class="product-logo-placeholder">${initial}</div>`;
}

function getProductVisualMeta(product) {
    const isHardware = isHardwareProduct(product);
    if (isHardware) {
        return { icon: 'cpu', label: '硬件产品', tone: 'card-shot--hardware' };
    }

    const primaryCategory = normalizeCategoryId((product.categories && product.categories[0]) || product.category || 'other');
    const visualMap = {
        coding: { icon: 'code', label: '编程工具', tone: 'card-shot--coding' },
        agent: { icon: 'bot', label: '智能体', tone: 'card-shot--agent' },
        image: { icon: 'image', label: '图像产品', tone: 'card-shot--image' },
        video: { icon: 'film', label: '视频产品', tone: 'card-shot--video' },
        voice: { icon: 'mic', label: '语音产品', tone: 'card-shot--voice' },
        writing: { icon: 'pen-tool', label: '写作产品', tone: 'card-shot--writing' },
        finance: { icon: 'bar-chart-3', label: '金融产品', tone: 'card-shot--finance' },
        education: { icon: 'graduation-cap', label: '教育产品', tone: 'card-shot--education' },
        healthcare: { icon: 'heart', label: '医疗产品', tone: 'card-shot--healthcare' }
    };

    return visualMap[primaryCategory] || { icon: 'sparkles', label: 'AI 产品', tone: 'card-shot--default' };
}

function buildWebsiteScreenshotMarkup(product, options = {}) {
    const website = normalizeWebsite(product.website || '');
    const hasWebsite = isValidWebsite(website);
    const className = options.className || 'card-media-shot';
    const width = Number(options.width) || 960;
    const visualMeta = getProductVisualMeta(product);
    const screenshotUrl = hasWebsite
        ? `https://image.thum.io/get/width/${width}/crop/960/noanimate/${encodeURI(website)}`
        : '';

    return `
        <div class="${className} card-shot ${visualMeta.tone}${hasWebsite ? '' : ' is-fallback'}">
            ${hasWebsite ? `<img src="${screenshotUrl}" alt="${product.name || 'AI 产品'} 截图" loading="lazy" referrerpolicy="no-referrer" onerror="handleScreenshotError(this)">` : ''}
            <div class="card-shot-fallback">
                <span class="card-shot-fallback-icon"><i data-lucide="${visualMeta.icon}"></i></span>
                <span class="card-shot-fallback-label">${visualMeta.label}</span>
            </div>
        </div>
    `;
}

/* exported handleLogoError, handleScreenshotError, openProduct */
function handleLogoError(img) {
    if (!img) return;
    const fallbackAttr = img.dataset.fallbacks || '';
    const initial = img.dataset.initial || '?';
    const fallbacks = fallbackAttr ? fallbackAttr.split('|').filter(Boolean) : [];
    const nextIndex = parseInt(img.dataset.fallbackIndex || '0', 10);

    if (fallbacks.length > 0 && nextIndex < fallbacks.length) {
        img.dataset.fallbackIndex = String(nextIndex + 1);
        img.src = fallbacks[nextIndex];
        return;
    }

    const placeholder = document.createElement('div');
    placeholder.className = 'product-logo-placeholder';
    placeholder.textContent = initial;
    img.replaceWith(placeholder);
}

function handleScreenshotError(img) {
    if (!img) return;
    const wrapper = img.closest('.card-shot');
    if (wrapper) {
        wrapper.classList.add('is-fallback');
    }
    img.remove();
}

// ========== 创建产品卡片 ==========
function createProductCard(product, showBadge = false) {
    const categories = product.categories || [];
    const categoryTags = categories.slice(0, 2).map(cat =>
        `<span class="product-tag">${getCategoryName(cat)}</span>`
    ).join('');

    const name = product.name || '未命名';
    const description = product.description || '暂无描述';
    const website = normalizeWebsite(product.website || '');
    const hasWebsite = isValidWebsite(website);
    const cardClass = `${showBadge ? 'product-card product-card--hot' : 'product-card'}${hasWebsite ? '' : ' product-card--no-link'}`;
    const logoMarkup = buildLogoMarkup(product);
    const screenshotMarkup = buildWebsiteScreenshotMarkup(product, { className: 'product-media-shot', width: 880 });
    const pendingTag = hasWebsite ? '' : '<span class="product-tag product-tag--pending">待验证</span>';
    const clickAttr = hasWebsite ? `onclick="openProduct('${website}')"` : '';

    return `
        <div class="${cardClass}" ${clickAttr}>
            <div class="product-card-media">
                ${screenshotMarkup}
                <div class="product-logo">
                    ${logoMarkup}
                </div>
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${name}</h3>
                </div>
                <p class="product-description">${description}</p>
                <div class="product-tags">
                    ${categoryTags}
                    ${pendingTag}
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
    const website = normalizeWebsite(product.website || '');
    const hasWebsite = isValidWebsite(website);
    const clickAttr = hasWebsite ? `onclick="openProduct('${website}')"` : '';
    const pendingTag = hasWebsite ? '' : '<span class="product-list-pending">🔎 官网待验证</span>';

    return `
        <div class="product-list-item ${hasWebsite ? '' : 'product-list-item--no-link'}" ${clickAttr}>
            <div class="product-rank ${rank <= 3 ? 'top-3' : ''}">${rank}</div>
            <div class="product-list-logo">
                ${logoMarkup}
            </div>
            <div class="product-list-info">
                <h3 class="product-list-name">${name}</h3>
                <p class="product-list-desc">${description}</p>
                ${(whyMatters || (fundingTotal && !isPlaceholderValue(fundingTotal))) ? `
                <div class="product-list-extra">
                    ${whyMatters ? `<span>💡 ${whyMatters}</span>` : ''}
                    ${fundingTotal && !isPlaceholderValue(fundingTotal) ? `<span class="product-list-funding">💰 ${fundingTotal}</span>` : ''}
                </div>` : ''}
                ${pendingTag}
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
    const normalized = normalizeCategoryId(categoryId);
    const categoryNames = {
        'software': '软件应用',
        'coding': '编程开发',
        'agent': '智能体',
        'voice': '语音识别',
        'finance': '金融科技',
        'image': '图像处理',
        'video': '视频生成',
        'writing': '写作助手',
        'healthcare': '医疗健康',
        'education': '教育学习',
        'hardware': '硬件设备',
        'enterprise': '企业服务',
        'vision': '视觉理解',
        'other': '其他'
    };
    return categoryNames[normalized] || categoryId;
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
    const normalized = normalizeWebsite(url);
    if (isValidWebsite(normalized)) {
        const newWindow = window.open(normalized, '_blank', 'noopener,noreferrer');
        if (newWindow) {
            newWindow.opener = null;
        }
    }
}

// ========== 动画效果 ==========
function animateCards(container) {
    // Reinitialize Lucide icons for dynamically added content
    refreshIcons();

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
    // Reinitialize Lucide icons for dynamically added content
    refreshIcons();

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
            currentPage = 1;
            applyFiltersAndRender();
        });
    }

    if (elements.typeFilter) {
        elements.typeFilter.addEventListener('change', (e) => {
            currentTypeFilter = e.target.value;
            currentDirectionFilter = 'all';
            currentPage = 1;
            applyFiltersAndRender();
        });
    }

    if (elements.directionFilter) {
        elements.directionFilter.addEventListener('change', (e) => {
            currentDirectionFilter = e.target.value;
            currentPage = 1;
            applyFiltersAndRender();
        });
    }
}

// Legacy function for backward compatibility
function applyFiltersAndSort() {
    applyFiltersAndRender();
}

// ========== Favorites ==========
function initFavorites() {
    if (elements.showFavoritesBtn) {
        elements.showFavoritesBtn.addEventListener('click', toggleFavoritesPanel);
    }

    if (elements.favoritesClose) {
        elements.favoritesClose.addEventListener('click', closeFavoritesPanel);
    }

    if (elements.favoritesTypeTabs) {
        elements.favoritesTypeTabs.addEventListener('click', (e) => {
            const btn = e.target.closest('.favorites-type-tab');
            if (!btn) return;
            favoritesTypeFilter = btn.dataset.type || 'all';
            favoritesSubFilter = 'all';
            renderFavoritesList();
        });
    }

    if (elements.favoritesSubfilters) {
        elements.favoritesSubfilters.addEventListener('click', (e) => {
            const btn = e.target.closest('.favorites-subfilter-btn');
            if (!btn) return;
            favoritesSubFilter = btn.dataset.value || 'all';
            renderFavoritesList();
        });
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
        if (pendingFavoritesData) return pendingFavoritesData;
        const stored = localStorage.getItem(FAVORITES_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

// Debounced favorites localStorage write
let favoritesSaveTimer = null;
let pendingFavoritesData = null;

function saveFavorites(favorites, options = {}) {
    const { immediate = false } = options;
    pendingFavoritesData = favorites;

    if (favoritesSaveTimer) {
        clearTimeout(favoritesSaveTimer);
    }

    if (immediate) {
        try {
            localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
            pendingFavoritesData = null;
        } catch (e) {
            console.error('Failed to save favorites:', e);
        }
        favoritesSaveTimer = null;
        return;
    }

    favoritesSaveTimer = setTimeout(() => {
        try {
            if (pendingFavoritesData) {
                localStorage.setItem(FAVORITES_KEY, JSON.stringify(pendingFavoritesData));
                pendingFavoritesData = null;
            }
        } catch (e) {
            console.error('Failed to save favorites:', e);
        }
        favoritesSaveTimer = null;
    }, 500);
}

function flushPendingFavorites() {
    if (!pendingFavoritesData) return;
    try {
        localStorage.setItem(FAVORITES_KEY, JSON.stringify(pendingFavoritesData));
        pendingFavoritesData = null;
    } catch (e) {
        console.error('Failed to flush favorites:', e);
    } finally {
        if (favoritesSaveTimer) {
            clearTimeout(favoritesSaveTimer);
            favoritesSaveTimer = null;
        }
    }
}

window.addEventListener('pagehide', flushPendingFavorites);
window.addEventListener('beforeunload', flushPendingFavorites);

function isFavorited(productKey) {
    if (!productKey) return false;
    const favorites = getFavorites();
    return favorites.some(f => f.key === productKey);
}

function getProductKey(product) {
    const website = normalizeWebsite(product.website || '');
    return website || product.name || '';
}

function getBlogFavoriteKey(blog) {
    const website = normalizeWebsite(blog.website || '');
    const source = blog.source || 'blog';
    const title = blog.name || '';
    return `blog:${source}:${website || title}`;
}

function createProductFavoriteEntry(product) {
    return {
        key: getProductKey(product),
        favorite_type: 'product',
        name: product.name,
        logo_url: product.logo_url,
        website: normalizeWebsite(product.website || ''),
        categories: product.categories,
        source: product.source || '',
        addedAt: new Date().toISOString()
    };
}

function createBlogFavoriteEntry(blog) {
    return {
        key: getBlogFavoriteKey(blog),
        favorite_type: 'blog',
        name: blog.name,
        logo_url: blog.logo_url || '',
        website: normalizeWebsite(blog.website || ''),
        categories: ['blog'],
        source: blog.source || 'unknown',
        addedAt: new Date().toISOString()
    };
}

function getFavoriteType(favorite) {
    if (!favorite) return 'product';
    if (favorite.favorite_type === 'blog') return 'blog';
    if (favorite.favorite_type === 'product') return 'product';
    return String(favorite.key || '').startsWith('blog:') ? 'blog' : 'product';
}

function getProductFavoriteSubfilters(favorites) {
    const counts = {};

    favorites
        .filter((fav) => getFavoriteType(fav) === 'product')
        .forEach((fav) => {
            const categories = Array.isArray(fav.categories) ? fav.categories : [];
            const normalized = categories.map(normalizeCategoryId).filter(Boolean);
            const keys = normalized.length > 0 ? normalized : ['other'];

            keys.forEach((key) => {
                counts[key] = (counts[key] || 0) + 1;
            });
        });

    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .map(([value, count]) => ({ value, count, label: getCategoryName(value) }));
}

function getBlogFavoriteSubfilters(favorites) {
    const counts = {};

    favorites
        .filter((fav) => getFavoriteType(fav) === 'blog')
        .forEach((fav) => {
            const source = String(fav.source || 'unknown').toLowerCase();
            counts[source] = (counts[source] || 0) + 1;
        });

    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .map(([value, count]) => ({ value, count, label: getSourceLabel(value) }));
}

function renderFavoritesControls(favorites) {
    if (!elements.favoritesTypeTabs || !elements.favoritesSubfilters || !elements.favoritesControls) return;

    const typeCounts = { product: 0, blog: 0 };
    favorites.forEach((fav) => {
        const type = getFavoriteType(fav);
        if (typeCounts[type] !== undefined) typeCounts[type] += 1;
    });

    elements.favoritesControls.style.display = favorites.length > 0 ? 'grid' : 'none';

    elements.favoritesTypeTabs.querySelectorAll('.favorites-type-tab').forEach((btn) => {
        const type = btn.dataset.type || 'all';
        const baseLabel = type === 'all'
            ? '全部'
            : (type === 'product' ? '产品' : '博客动态');
        const count = type === 'all' ? favorites.length : (typeCounts[type] || 0);
        btn.textContent = `${baseLabel} (${count})`;
        btn.classList.toggle('active', favoritesTypeFilter === type);
    });

    let subfilters = [];
    if (favoritesTypeFilter === 'product') {
        subfilters = getProductFavoriteSubfilters(favorites);
    } else if (favoritesTypeFilter === 'blog') {
        subfilters = getBlogFavoriteSubfilters(favorites);
    }

    const availableValues = subfilters.map((s) => s.value);
    if (favoritesSubFilter !== 'all' && !availableValues.includes(favoritesSubFilter)) {
        favoritesSubFilter = 'all';
    }

    if (subfilters.length === 0) {
        elements.favoritesSubfilters.innerHTML = '';
        return;
    }

    const chips = [
        `<button class="favorites-subfilter-btn ${favoritesSubFilter === 'all' ? 'active' : ''}" data-value="all">全部</button>`,
        ...subfilters.map((item) => {
            const activeClass = favoritesSubFilter === item.value ? 'active' : '';
            return `<button class="favorites-subfilter-btn ${activeClass}" data-value="${item.value}">${item.label} (${item.count})</button>`;
        })
    ];
    elements.favoritesSubfilters.innerHTML = chips.join('');
}

function filterFavoritesByPanelSelection(favorites) {
    let filtered = [...favorites];

    if (favoritesTypeFilter !== 'all') {
        filtered = filtered.filter((fav) => getFavoriteType(fav) === favoritesTypeFilter);
    }

    if (favoritesSubFilter !== 'all') {
        if (favoritesTypeFilter === 'product') {
            filtered = filtered.filter((fav) => {
                const categories = Array.isArray(fav.categories) ? fav.categories : [];
                const normalized = categories.map(normalizeCategoryId).filter(Boolean);
                const keys = normalized.length > 0 ? normalized : ['other'];
                return keys.includes(favoritesSubFilter);
            });
        } else if (favoritesTypeFilter === 'blog') {
            filtered = filtered.filter((fav) => {
                return String(fav.source || 'unknown').toLowerCase() === favoritesSubFilter;
            });
        }
    }

    return filtered;
}

function removeFavoriteByKey(productKey) {
    let favorites = getFavorites();
    const next = favorites.filter(f => f.key !== productKey);
    if (next.length === favorites.length) return false;

    saveFavorites(next);
    updateFavoritesCount();
    updateFavoriteButtons(productKey);
    renderFavoritesList();
    return true;
}

function addFavoriteEntry(entry, options = {}) {
    if (!entry?.key || isFavorited(entry.key)) return false;

    const favorites = getFavorites();
    favorites.push(entry);
    saveFavorites(favorites, options);
    updateFavoritesCount();
    updateFavoriteButtons(entry.key);
    renderFavoritesList();
    return true;
}

function toggleFavorite(product, event) {
    if (event) {
        event.stopPropagation();
    }

    const productKey = getProductKey(product);
    if (!productKey) return;

    if (isFavorited(productKey)) {
        removeFavoriteByKey(productKey);
        return;
    }

    addFavoriteEntry(createProductFavoriteEntry(product));
}

/* exported toggleBlogFavorite, handleSwipeFavoriteClick */
function toggleBlogFavorite(event, encodedBlog) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    try {
        const blog = JSON.parse(decodeURIComponent(encodedBlog));
        const key = getBlogFavoriteKey(blog);

        if (isFavorited(key)) {
            removeFavoriteByKey(key);
            return;
        }

        addFavoriteEntry(createBlogFavoriteEntry(blog));
    } catch (e) {
        console.error('Failed to toggle blog favorite:', e);
    }
}

function handleSwipeFavoriteClick(event, encodedProduct) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    try {
        const product = JSON.parse(decodeURIComponent(encodedProduct));
        toggleFavorite(product, event);
    } catch (e) {
        console.error('Failed to toggle swipe favorite:', e);
    }
}

function updateFavoritesCount() {
    const count = getFavorites().length;
    if (elements.favoritesCount) {
        elements.favoritesCount.textContent = count;
    }
}

function updateFavoriteButtons(productKey) {
    if (!productKey) return;
    const isFav = isFavorited(productKey);
    const escapedKey = (window.CSS && typeof window.CSS.escape === 'function')
        ? window.CSS.escape(productKey)
        : String(productKey).replace(/\\/g, '\\\\').replace(/"/g, '\\"');

    document.querySelectorAll(`[data-product-key="${escapedKey}"]`).forEach(btn => {
        btn.classList.toggle('is-favorited', isFav);
        if (btn.classList.contains('modal-favorite-btn')) {
            btn.innerHTML = isFav ? '❤️ 已收藏' : '🤍 收藏';
        } else {
            btn.innerHTML = isFav ? '❤️' : '🤍';
        }
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
    renderFavoritesControls(favorites);

    if (favorites.length === 0) {
        panel?.classList.add('is-empty');
        elements.favoritesList.innerHTML = '';
        return;
    }

    panel?.classList.remove('is-empty');
    const filteredFavorites = filterFavoritesByPanelSelection(favorites);

    if (filteredFavorites.length === 0) {
        elements.favoritesList.innerHTML = `
            <div class="favorites-filter-empty">
                当前筛选下暂无收藏，试试切换上方分类
            </div>
        `;
        return;
    }

    elements.favoritesList.innerHTML = filteredFavorites.map(fav => {
        const categories = (fav.categories || []).slice(0, 2).map(getCategoryName).join(' · ');
        const categoryText = getFavoriteType(fav) === 'blog'
            ? `博客动态 · ${getSourceLabel(fav.source || 'unknown')}`
            : (categories || '精选 AI 工具');
        const logoMarkup = fav.logo_url
            ? `<img src="${fav.logo_url}" alt="${fav.name}" width="40" height="40" loading="lazy" onerror="this.style.display='none'">`
            : `<div class="product-logo-placeholder">${getInitial(fav.name)}</div>`;
        const website = normalizeWebsite(fav.website || '');
        const hasWebsite = isValidWebsite(website);
        const clickAttr = hasWebsite ? `onclick="openProduct('${website}')"` : '';
        const pendingNote = hasWebsite ? '' : '<span class="favorite-item-pending">官网待验证</span>';

        return `
            <div class="favorite-item ${hasWebsite ? '' : 'favorite-item--no-link'}" ${clickAttr}>
                <div class="favorite-item-logo">${logoMarkup}</div>
                <div class="favorite-item-info">
                    <div class="favorite-item-name">${fav.name}</div>
                    <div class="favorite-item-category">${categoryText}</div>
                    ${pendingNote}
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
    removeFavoriteByKey(productKey);
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
    const directionTags = inferProductDirections(product).slice(0, 2).map(direction =>
        `<span class="product-tag product-tag--direction">${getDirectionTagName(direction)}</span>`
    ).join('');

    const name = product.name || '未命名';
    const fundingTotal = product.funding_total || '';
    const whyMatters = product.why_matters || '';
    const description = product.description || '暂无描述';
    const rating = product.rating ? product.rating.toFixed(1) : 'N/A';
    const users = formatNumber(product.weekly_users);
    const score = product.dark_horse_index || 0;
    const isFeatured = score >= 5;
    const isCompact = score >= 2 && score <= 3;
    const cardTierClass = isFeatured
        ? 'product-card--featured'
        : (isCompact ? 'product-card--compact' : 'product-card--standard');
    const cardClass = `${showBadge ? 'product-card product-card--hot' : 'product-card'} ${cardTierClass}`;
    const logoMarkup = buildLogoMarkup(product);
    const screenshotMarkup = buildWebsiteScreenshotMarkup(product, { className: 'product-media-shot', width: 960 });
    const productKey = getProductKey(product);
    const isFav = isFavorited(productKey);

    // Score badge based on dark_horse_index
    let scoreBadge = '';
    if (score >= 5) {
        scoreBadge = '<span class="score-badge score-badge--5">5分</span>';
    } else if (score >= 4) {
        scoreBadge = '<span class="score-badge score-badge--4">4分</span>';
    } else if (score >= 3) {
        scoreBadge = '<span class="score-badge score-badge--3">3分</span>';
    } else if (score >= 2) {
        scoreBadge = '<span class="score-badge score-badge--2">2分</span>';
    }

    // Category pill for hardware/software
    const isHardware = isHardwareProduct(product);
    const categoryPill = isHardware
        ? '<span class="category-pill category-pill--hardware"><i data-lucide="cpu" style="width:12px;height:12px;"></i> 硬件</span>'
        : '<span class="category-pill category-pill--software"><i data-lucide="code" style="width:12px;height:12px;"></i> 软件</span>';
    const compactLine = `
        <div class="product-compact-line">
            ${categoryPill}
            ${fundingTotal ? `<span class="product-meta-item">💰 ${fundingTotal}</span>` : ''}
            <span class="product-meta-item">⭐ ${rating}</span>
        </div>
    `;

    return `
        <div class="${cardClass}" onclick="handleProductClick(event, '${encodeURIComponent(JSON.stringify(product).replace(/'/g, "\\'"))}')">
            <button class="product-favorite-btn ${isFav ? 'is-favorited' : ''}"
                    data-product-key="${productKey}"
                    onclick="handleFavoriteClick(event, '${encodeURIComponent(JSON.stringify(product).replace(/'/g, "\\'"))}')">
                ${isFav ? '❤️' : '🤍'}
            </button>
            <div class="product-card-media">
                ${screenshotMarkup}
                <div class="product-logo">
                    ${logoMarkup}
                </div>
            </div>
            <div class="product-info">
                <div class="product-header">
                    <h3 class="product-name">${name}</h3>
                    ${scoreBadge}
                </div>
                ${isCompact ? compactLine : `<p class="product-description">${description}</p>`}
                ${!isCompact && (whyMatters || fundingTotal) ? `
                    <div class="product-insights">
                        ${whyMatters ? `<div class="product-insight">💡 ${whyMatters}</div>` : ''}
                        ${fundingTotal ? `<div class="product-insight product-insight--funding">💰 ${fundingTotal}</div>` : ''}
                    </div>` : ''}
                ${!isCompact ? `
                    <div class="product-meta">
                        ${categoryPill}
                        <span class="product-meta-item">⭐ ${rating}</span>
                        <span class="product-meta-item">👥 ${users}</span>
                    </div>
                    <div class="product-tags">
                        ${categoryTags}
                        ${directionTags}
                    </div>
                ` : ''}
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

// ========== 行业领军 ==========
async function loadIndustryLeaders() {
    if (!elements.leadersCategories) return;

    try {
        const response = await fetch(`${API_BASE_URL}/products/industry-leaders`);
        const result = await response.json();

        if (result.success && result.data && result.data.categories) {
            leadersCategoriesData = result.data.categories;
            leadersActiveFilter = 'all';
            setupLeadersFilters(leadersCategoriesData);
            renderIndustryLeaders();
        } else {
            elements.leadersCategories.innerHTML = '<p class="no-data">暂无数据</p>';
        }
    } catch (error) {
        console.error('Error loading industry leaders:', error);
        elements.leadersCategories.innerHTML = '<p class="error">加载失败</p>';
    }
}

function orderLeaderCategories(categories) {
    const ordered = [];
    const remaining = new Map(Object.entries(categories));

    LEADERS_CATEGORY_ORDER.forEach((name) => {
        if (remaining.has(name)) {
            ordered.push([name, remaining.get(name)]);
            remaining.delete(name);
        }
    });

    for (const entry of remaining.entries()) {
        ordered.push(entry);
    }

    return ordered;
}

function setupLeadersFilters(categories) {
    if (!elements.leadersFilters) return;
    const orderedNames = orderLeaderCategories(categories).map(([name]) => name);
    const filters = ['全部', ...orderedNames];

    elements.leadersFilters.innerHTML = filters.map((label) => {
        const key = label === '全部' ? 'all' : label;
        return `<button class="leaders-filter" data-filter="${key}">${label}</button>`;
    }).join('');

    elements.leadersFilters.querySelectorAll('.leaders-filter').forEach((btn) => {
        btn.addEventListener('click', () => {
            leadersActiveFilter = btn.dataset.filter || 'all';
            updateLeadersFilterSelection();
            renderIndustryLeaders();
        });
    });

    updateLeadersFilterSelection();
}

function updateLeadersFilterSelection() {
    if (!elements.leadersFilters) return;
    elements.leadersFilters.querySelectorAll('.leaders-filter').forEach((btn) => {
        const isActive = (btn.dataset.filter || 'all') === leadersActiveFilter;
        btn.classList.toggle('active', isActive);
    });
}

function renderIndustryLeaders() {
    if (!elements.leadersCategories || !leadersCategoriesData) return;

    let entries = orderLeaderCategories(leadersCategoriesData);
    if (leadersActiveFilter !== 'all') {
        entries = entries.filter(([name]) => name === leadersActiveFilter);
    }

    if (!entries.length) {
        elements.leadersCategories.innerHTML = '<p class="no-data">暂无数据</p>';
        return;
    }

    let html = '';
    for (const [categoryName, categoryData] of entries) {
        const icon = categoryData.icon || '📦';
        const products = categoryData.products || [];
        const description = categoryData.description || '';

        html += `
            <div class="leaders-category">
                <div class="category-header">
                    <span class="category-icon">${icon}</span>
                    <h3 class="category-name">${categoryName}</h3>
                    <span class="category-count">${products.length} 个产品</span>
                </div>
                <p class="category-desc">${description}</p>
                <div class="leaders-grid">
                    ${products.map(p => renderLeaderCard(p)).join('')}
                </div>
            </div>
        `;
    }

    elements.leadersCategories.innerHTML = html;
    animateLeaderCards(elements.leadersCategories);
}

function animateLeaderCards(container) {
    // Reinitialize Lucide icons for dynamically added content
    refreshIcons();

    const cards = container.querySelectorAll('.leader-card');
    if (prefersReducedMotion) {
        cards.forEach((card) => {
            card.style.opacity = '1';
            card.style.transform = 'none';
        });
        return;
    }
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(16px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 40);
    });
}

function renderLeaderCard(product) {
    const logoSrc = product.logo || '';
    const initial = getInitial(product.name);
    const logoMarkup = logoSrc
        ? `<img src="${logoSrc}" alt="${product.name}" width="40" height="40" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\'leader-logo-placeholder\\'>${initial}</div>'">`
        : `<div class="leader-logo-placeholder">${initial}</div>`;

    return `
        <div class="leader-card" onclick="window.open('${product.website}', '_blank')">
            <div class="leader-header">
                <div class="leader-logo">${logoMarkup}</div>
                <div class="leader-title">
                    <h4 class="leader-name">${product.name}</h4>
                    <p class="leader-company">${product.company || ''}</p>
                </div>
                <span class="leader-region">${product.region || '🌍'}</span>
            </div>
            <p class="leader-desc">${product.description || ''}</p>
            <div class="leader-stats">
                ${product.funding ? `<span class="stat">💰 ${product.funding}</span>` : ''}
                ${product.valuation ? `<span class="stat">📈 ${product.valuation}</span>` : ''}
                ${product.users ? `<span class="stat">👥 ${product.users}</span>` : ''}
            </div>
            <p class="leader-why">💡 ${product.why_famous || ''}</p>
        </div>
    `;
}
