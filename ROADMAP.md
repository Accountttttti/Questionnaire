# 问卷系统 · 项目进程路线

## 技术栈（已确认）

| 层 | 选型 |
|---|---|
| 前端 | Vue 3（Vite） |
| 后端 | Python + Flask |
| 数据库 | SQLite（一个 `.db` 文件） |

已确认的关键决策：
- **填写 / 看结果免登录**；创建、管理、收藏等仍需登录。
- **计分模型**：每题选项带分值，累加总分，落进分数区间输出对应文案。
- **接龙 / 考试**：仅占位，不做详细功能。
- **首页**：公开问卷广场，展示已发布公开问卷，可填写并产生浏览/使用记录。

## 目录结构

```
questionnaire/
├── ROADMAP.md            # 本文件（进程路线）
├── frontend/             # Vue3 前端
│   └── src/
│       ├── views/        # 页面：登录、首页、创建、我的、填写、结果
│       ├── components/   # 组件：题目编辑器、结果卡片等
│       ├── api/          # 封装后端接口调用
│       └── store/        # 登录态等全局状态
└── backend/              # Flask 后端
    ├── app.py            # 入口 + 路由
    ├── db.py             # 数据库初始化
    ├── models.py         # 表结构
    └── questionnaire.db  # SQLite 数据文件（运行后生成）
```

## 数据模型（概览）

- `users`：id、username、password_hash、token、avatar、email、phone
- `questionnaires`：id、user_id、type、title、status（draft/published）
- `questions`：id、questionnaire_id、type（single/scale）、title、order
- `options`：id、question_id、text、score、order（量表反向计分=翻转 score，不加字段）
- `result_cards`：id、questionnaire_id、min_score、max_score、text、order
- `user_actions`：user_id、questionnaire_id、action（favorite/like/use/browse）
- `responses`：id、questionnaire_id、user_id（可空）、answers、total_score、result_text

## 阶段路线

### 阶段 0 · 项目初始化
- [ ] 建目录：`frontend/` + `backend/`
- [ ] 前端：Vite 创建 Vue3 项目，能启动
- [ ] 后端：Flask + SQLite 初始化，跑通一个 `hello` 接口
- [ ] 前后端联通（CORS 配置）
- **检查点**：浏览器能调到后端接口

### 阶段 1 · 登录 / 注册
- 登录态：token 存 localStorage，后端生成随机 token
- 数据库：原生 sqlite3；`users` 表（id / username / password_hash / avatar / email / phone / created_at）
- 接口：`POST /api/register`、`POST /api/login`、`GET /api/me`
- 密码：werkzeug 哈希，不存明文
- 前端：vue-router（登录页 ↔ 主界面）+ 路由守卫；先不用 Pinia

- [x] 后端：建库 + users 表
- [x] 后端：注册接口
- [x] 后端：登录接口（含 token）
- [x] 前端：装 vue-router + 页面骨架
- [x] 前端：登录/注册页
- [x] 前端：登录态保持 + 路由守卫
- **检查点**：注册→登录→刷新页面仍保持登录 ✅ 已通过

### 阶段 2 · 创建问卷（核心编辑器）
- [ ] 后端：问卷/题目/选项/结果卡片 的增删改查接口
- [ ] 前端：新建问卷（选类型 → 填名称）
- [ ] 添加题目：单选题（选项带分值）、量表题（1~5）
- [ ] 题目编辑：删除、调顺序
- [ ] 设置结果卡片：多张「分数区间 + 文案」，含兜底
- **检查点**：能完整建一份问卷并存进数据库

### 阶段 3 · 首页 / 新建 / 我的
- [ ] 左侧分栏：首页 / 新建 / 我的
- [ ] 新建：新建按钮 + 创建过的问卷列表
- [ ] 我的：创建 / 收藏 / 喜爱 / 使用 / 浏览 五类
- [ ] 用户名 + 头像（预设头像，暂不做上传）
- [ ] 用户信息：邮箱 / 绑定手机号（占位，不做功能）
- [ ] 首页：公开问卷广场（展示已发布公开问卷，可填写，产生浏览/使用记录）
- **检查点**：能查看自己各类问卷

### 阶段 4 · 填写端 & 计算分数
- [ ] 填写页：打开问卷 → 逐题作答 → 提交
- [ ] 后端计算总分，返回匹配的结果卡片文案
- [ ] 存作答记录（responses 表：答案 + 总分 + 结果）
- [ ] 结果页展示（分数 + 文案）
- **检查点**：答完一份问卷，正确显示结果文案

### 阶段 5 · 分享
- [ ] 分享链接（唯一 ID，免登录可填）
- [ ] 分享图片（`html2canvas` 截图，第二阶段再做）
- **检查点**：复制链接，别人能免登录打开填写

### 阶段 6 · 接龙 / 考试占位
- [ ] 类型选择里预留入口，点击提示「开发中」
- **检查点**：三种类型可选，占位的能正常提示

## 当前状态

- [x] 需求讨论 + 技术选型（2026-09-27）
- [x] 阶段 0 项目初始化（2026-09-27）
- [x] 阶段 1 登录 / 注册（2026-09-27）
- [ ] 阶段 2 问卷编辑器 ← **下一步**



好问题，这一步是从「本地开发」跨到「上线部署」，概念上有个关键转变要先讲清楚：

  你现在 vs 上线后
  - 现在：前端 vite 跑在 5174，后端 flask 跑在 5000，靠 vite 的 proxy 把 /api 转发到后端。
  - 上线后：把前端 npm run build 打包成静态文件，用一个 Nginx 同时干两件事——① 直接把静态页面发给访客；② 把 /api 和
  /uploads 转发给后端。用户只访问一个地址，看不到 5174/5000 这些端口。vite 的 proxy 就不需要了。

  你要做的几件事（按顺序）

  1. 备案（大陆服务器最大的坎）
  阿里云大陆服务器，如果要绑定域名开网站，必须做 ICP 备案，需要域名 + 实名，周期通常 1～3
  周。这块最耗时，建议现在就先去提交。如果想绕过备案，只能用公网 IP 直接访问（http://1.2.3.4），但严格来说大陆 80
  端口提供 web 服务也要备案，个人测试用非 80 端口是常见做法。
  2. 安全组开端口
  在阿里云控制台「安全组」里放行 80（或你用的端口），否则外面根本连不进来。
  3. 服务器装环境
  Python3 + pip、gunicorn（生产级 WSGI 服务器，替代 flask run）、Nginx。
  4. 部署后端
  代码传上去，装依赖，用 gunicorn 跑起来，再配 systemd 让它开机自启、崩了自动重启。
  5. 部署前端
  本地 npm run build 出 dist/，上传，让 Nginx 指向它。
  6. Nginx 配置
  一个配置文件搞定：静态文件 + /api /uploads 反代到 gunicorn。
  7. 收尾细节
    - SQLite 完全够用，不用换 MySQL（单文件，记得备份即可）。
    - backend/uploads/ 目录要在服务器上建好、可写。
    - SMTP 已经配好了（config.py 里那份真实账号密码别传到公开仓库）。
    - Flask 的 secret key 换成随机的、关掉 debug。

  2核2G 对 Flask + SQLite + 静态站完全够，gunicorn 开 2 个 worker 就行。

  一个需要你定的点：你有域名吗？备案要不要现在就一起弄？这决定了我们是走「域名 + 备案」的正式路线，还是先用「公网 IP +
  端口」快速跑起来给你朋友测。

  确定方向后，我可以带着你一步步来，先搭服务器环境。你想先从哪块开始？