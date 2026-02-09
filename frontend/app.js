const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Optional override for the browser-side API base URL.
// If empty, frontend/public/js/main.js will auto-select:
// - localhost -> http://localhost:5000/api/v1
// - otherwise -> /api/v1
const apiBaseUrl = process.env.API_BASE_URL || '';

// 设置模板引擎
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 静态文件
app.use(express.static(path.join(__dirname, 'public')));

// 主页路由
app.get('/', (req, res) => {
  res.render('index', { apiBaseUrl });
});

// 前端路由占位，避免直接访问 404
app.get(['/blog', '/search', '/product/:id'], (req, res) => {
  res.render('index', { apiBaseUrl });
});

// Vercel serverless expects a handler export; local dev expects a listening server.
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`🚀 WeeklyAI 前端运行在 http://localhost:${PORT}`);
    if (apiBaseUrl) console.log(`   API_BASE_URL=${apiBaseUrl}`);
  });
}

module.exports = app;

