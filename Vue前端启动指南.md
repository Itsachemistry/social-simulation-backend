# 社交仿真系统 - Vue版本启动指南

## 📋 项目状态

✅ **Vue前端迁移已完成！**

- ✅ Vue 3 + Vite 现代化前端架构
- ✅ 11个功能组件完整迁移
- ✅ Composition API 重构
- ✅ 响应式数据管理
- ✅ 现代化UI界面

## 🚀 一键启动

### Windows系统

#### 方式1：双击启动（推荐）
```bash
# 启动系统
双击: 启动社交仿真系统.bat

# 关闭系统  
双击: 关闭社交仿真系统.bat
```

#### 方式2：命令行启动
```bash
# 启动前后端
start_all_vue.bat

# 关闭前后端
stop_all.bat
```

### Linux/macOS系统

```bash
# 启动前后端
./start_all_vue.sh

# 关闭前后端
./stop_all.sh
```

## 📍 访问地址

启动成功后，访问以下地址：

- **前端页面**: http://localhost:8080 (Vue + Vite)
- **后端API**: http://localhost:5000
- **API文档**: http://localhost:5000/api/visualization/options

## 🛠️ 手动启动（开发调试）

### 启动后端
```bash
# 激活虚拟环境
call venv\Scripts\activate  # Windows
source venv/bin/activate    # Linux/macOS

# 安装依赖
pip install -r requirements.txt

# 启动Flask服务器
python run_server.py
```

### 启动前端
```bash
# 切换到Vue项目目录
cd frontend-vue

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

## 📦 功能模块

### 已完成的Vue组件：

1. **SideBar.vue** - 侧边栏导航
2. **EnvSetupPanel.vue** - 环境配置面板
3. **AgentPanel.vue** - 智能体管理
4. **HistogramPanel.vue** - 数据分布图表
5. **AttitudePanel.vue** - 态度分析
6. **WordcloudPanel.vue** - 词云分析
7. **TreePanel.vue** - 转播树可视化
8. **SinglePanel.vue** - 单帖深度分析
9. **PostList.vue** - 帖子列表
10. **TimeSelector.vue** - 时间选择器
11. **MainArea.vue** - 主显示区域

### 技术栈：

- **前端**: Vue 3 + Vite + JavaScript
- **图表**: Chart.js + D3.js
- **HTTP**: Axios
- **UI**: 自定义CSS + 响应式设计
- **后端**: Flask + Python

## 🔧 开发说明

### 前端开发
```bash
cd frontend-vue
npm run dev    # 开发模式
npm run build  # 生产构建
npm run preview # 预览构建结果
```

### 后端API
- 基础URL: http://localhost:5000/api
- 支持跨域请求 (CORS)
- RESTful API设计

## 📝 与旧版本对比

| 功能 | 旧版本 (HTML/JS) | 新版本 (Vue) |
|------|------------------|-------------|
| 框架 | 原生JS + HTML | Vue 3 + Vite |
| 构建工具 | 无 | Vite (快速HMR) |
| 组件化 | 无 | 完整组件架构 |
| 状态管理 | 全局变量 | Vue响应式 |
| 代码复用 | 低 | 高 |
| 开发体验 | 一般 | 优秀 |
| 维护性 | 低 | 高 |

## ⚠️ 注意事项

1. **首次运行**：会自动安装前端依赖，需要等待几分钟
2. **端口占用**：确保5000和5173端口未被占用
3. **虚拟环境**：确保已创建Python虚拟环境 `venv`
4. **Node.js**：确保已安装Node.js (建议v16+)

## 🐛 故障排除

### 常见问题：

1. **前端无法访问**
   - 检查8080端口是否被占用
   - 确认npm依赖安装完成

2. **后端API错误**
   - 检查5000端口是否被占用
   - 确认Python依赖安装完成
   - 检查虚拟环境是否正确激活

3. **跨域问题**
   - 后端已配置CORS，通常不会有跨域问题

4. **网络请求失败**
   - 确认前后端都已正常启动
   - 检查防火墙设置

---

🎉 **恭喜！Vue前端迁移已完成，享受现代化的开发体验吧！**


现在我想这个系统达成的效果是，首先用户可以在前端设置好一些参数，然后选择好哪些agent参与本次仿真，之后，用户可以指定运行多少个时间片，用户点击开始仿真，仿真过程上，你需要帮我看一下代码，确认一下按照以下流程进行，首先划分时间片，然后依次把本时间片所有内容喂给agent，如果遇到意见领袖的话，它需要先得到本时间片内所有帖子生成的简报，完成一次轻推情绪立场更新，然后再开始阅读流程，这是它和普通agent不一样的地方，然后读完所有帖子后，阅读帖子的时候当然都要用llm来给出情绪立场更新建议，如果agent判定完决定发言，那么它程序就会根据它的类型来生成prompt，发送给llm，得到agent的发言，后端会把它的内容数据处理后拼凑好json对象，然后进入下一轮的帖子池中供agent们阅读，最后过程中相关的所有内容都输出到一个txt文件里，包括每次调用llm构造出来的prompt，还有收到的结果，你懂我意思吗？你帮我逐个点过一下。这些内容的相关代码我们应该都写好了，你帮我确认我们这个流程完整。没有的话指出来一下我们讨论