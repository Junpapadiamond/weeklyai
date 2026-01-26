/**
 * WeeklyAI - Blogs Section
 * News and blog content
 */

const Blogs = {
    init() {
        this.initFilters();
        this.loadBlogs();
    },

    /**
     * Initialize source filters
     */
    initFilters() {
        const container = document.getElementById('blogFilters');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const btn = e.target.closest('.filter-btn');
            if (!btn) return;

            container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const source = btn.dataset.source || '';
            this.loadBlogs(source);
        });
    },

    /**
     * Load blogs/news
     */
    async loadBlogs(source = '') {
        const container = document.getElementById('blogsList');
        if (!container) return;

        Animations.showSkeleton(container, 4);

        try {
            const response = await API.getBlogs(30, source);

            if (response.success && response.data) {
                this.render(response.data);
            } else {
                this.showError(container);
            }
        } catch (error) {
            console.error('Failed to load blogs:', error);
            this.showError(container);
        }
    },

    /**
     * Render blog list
     */
    render(blogs) {
        const container = document.getElementById('blogsList');
        if (!container) return;

        container.innerHTML = '';

        if (blogs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>暂无新闻动态</p>
                </div>
            `;
            return;
        }

        blogs.forEach(blog => {
            const card = Cards.createBlogCard(blog);
            container.appendChild(card);
        });

        Animations.animateListItems(container, '.blog-card');
    },

    /**
     * Show error state
     */
    showError(container) {
        container.innerHTML = `
            <div class="error-state">
                <p>😕 加载失败</p>
                <button class="btn btn--secondary" onclick="Blogs.loadBlogs()">重试</button>
            </div>
        `;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Blogs;
} else {
    window.Blogs = Blogs;
}
