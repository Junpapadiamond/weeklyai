const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// 设置模板引擎
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 静态文件
app.use(express.static(path.join(__dirname, 'public')));

// 主页路由
app.get('/', (req, res) => {
    res.render('index');
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`🚀 WeeklyAI 前端运行在 http://localhost:${PORT}`);
});


