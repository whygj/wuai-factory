# 五爱食品工厂管理系统 — 开发指引

## 项目背景

客户：**保定五爱食品有限公司**（小型食品加工厂，产品为甜品/果酱/巧克力）
- 3个用户：内勤（电脑录入）、生产班长（手机/电脑）、老板（手机+电脑查看）
- 所有用户都是电脑小白，UI必须极简——大按钮、大字体、仪表盘优先
- 替代现有混乱的纸质手写记录

## 核心需求（4个模块）

### 1. 仪表盘首页（老板第一眼看到的）
- 大数字卡片：原料种类数、产品种类数、今日生产量、待发货数
- 饼图：原料库存分布
- 柱状图：产品库存排行
- 预警区：低于安全线的原料标红显示
- **手机端体验要好**——老板主要用手机看

### 2. 原料库存管理
- 原料字典：19种原料（巧克力、奶油、果浆、糖浆、明胶等）
- 入库操作：选原料、填数量、提交 → 库存自动增加
- 库存查询：实时查看每种原料当前库存
- 库存预警：低于安全线自动标红

### 3. 生产日报
- 登记每天生产了什么、生产了多少
- 字段：日期、产品（下拉选择）、数量、单位（盒/瓶/锅/kg）、糖度、备注
- **关键：提交后自动扣减原料库存 + 自动增加产品库存**
- 可以简单选择消耗了哪些原料和数量

### 4. 发货管理
- 登记发货：客户名、产品、数量、单价、金额
- **关键：提交后自动扣减产品库存**
- 状态追踪：待发货 → 已发货 → 已签收

## 三条库存联动规则（核心业务逻辑）

```
规则1: 原料入库 → raw_materials.current_stock + N → 写入 inventory_transactions 流水
规则2: 生产登记 → raw_materials.current_stock - N(消耗原料) + products.current_stock + N(产出产品) → 写入 production_records + inventory_transactions
规则3: 发货登记 → products.current_stock - N → 写入 shipment_records + 检查库存是否充足
```

- **必须用数据库事务**确保库存更新和流水记录同时成功或失败
- SQLite使用WAL模式支持3人并发

## 技术栈

- **前端**: Vue 3 + Element Plus + ECharts + Vue Router
  - Vite 构建
  - 响应式设计（Element Plus的el-row/el-col + media query）
  - ECharts 做饼图和柱状图
- **后端**: Python FastAPI + Pydantic + Uvicorn
  - SQLAlchemy ORM（同步模式，不用async）
  - SQLite 数据库 + WAL模式
- **部署**: Docker Compose + Nginx反向代理
  - 域名: factory.agentmj.vip

## 数据库设计

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL DEFAULT 'clerk',  -- 'boss'/'clerk'/'leader'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原料字典
CREATE TABLE raw_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,           -- 巧克力类/油脂类/果酱类/乳制品/粉类/糖浆类/添加剂
    unit TEXT,               -- kg/桶/件/袋/瓶
    current_stock REAL DEFAULT 0,
    safety_stock REAL DEFAULT 0,
    supplier TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 产品字典
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,           -- 慕斯/果酱/巧克力/镜面
    unit TEXT,               -- 盒/瓶/锅/kg
    spec TEXT,
    current_stock REAL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原料出入库流水
CREATE TABLE inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT NOT NULL,  -- 'in' 入库 / 'out' 出库
    raw_material_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT,
    source TEXT,            -- 'purchase'采购入库 / 'production'生产消耗
    related_id INTEGER,     -- 关联的生产记录ID或0
    operator TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id)
);

-- 生产日报
CREATE TABLE production_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT,
    sugar_degree REAL,      -- 糖度
    raw_materials_used TEXT, -- JSON: [{"material_id":1,"quantity":10,"unit":"kg"}]
    operator TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 发货明细
CREATE TABLE shipment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    customer_name TEXT,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT,
    unit_price REAL,
    total_amount REAL,
    status TEXT DEFAULT '待发货',  -- 待发货/已发货/已签收
    operator TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 操作日志
CREATE TABLE operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    action TEXT,
    table_name TEXT,
    record_id INTEGER,
    detail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API 设计

### 认证
- `POST /api/auth/login` — 登录，返回JWT token
- `GET /api/auth/me` — 当前用户信息

### 仪表盘
- `GET /api/dashboard/overview` — 所有KPI数据（原料数、产品数、今日生产、待发货、预警列表）

### 原料管理
- `GET /api/materials` — 原料列表（支持搜索、分页）
- `POST /api/materials` — 新增原料
- `PUT /api/materials/{id}` — 编辑原料
- `POST /api/materials/{id}/inbound` — 入库（增加库存）
- `GET /api/materials/transactions` — 出入库流水

### 产品管理
- `GET /api/products` — 产品列表
- `POST /api/products` — 新增产品
- `PUT /api/products/{id}` — 编辑产品

### 生产日报
- `GET /api/production` — 生产记录列表（支持按日期筛选）
- `POST /api/production` — 新增生产记录（触发库存联动：扣原料+增产品）
- `GET /api/production/{id}` — 单条详情

### 发货管理
- `GET /api/shipments` — 发货列表
- `POST /api/shipments` — 新增发货（触发库存联动：扣产品库存）
- `PUT /api/shipments/{id}/status` — 更新状态

### 统计
- `GET /api/stats/material-distribution` — 原料库存分布（饼图数据）
- `GET /api/stats/product-ranking` — 产品库存排行（柱状图数据）
- `GET /api/stats/production-trend` — 近7天/30天生产趋势

## 前端页面

1. **登录页** `/login` — 简洁登录框
2. **仪表盘** `/` — 首页，KPI卡片+图表+预警
3. **原料管理** `/materials` — 列表+入库按钮
4. **原料入库** `/materials/inbound` — 入库表单
5. **生产登记** `/production/new` — 生产表单（选产品、填数量糖度、选消耗原料）
6. **生产记录** `/production` — 生产历史列表
7. **发货登记** `/shipments/new` — 发货表单
8. **发货列表** `/shipments` — 发货记录+状态追踪

## 前端UI要求（极其重要）

- **Element Plus组件**：el-button, el-form, el-table, el-select, el-dialog, el-card
- **大按钮、大字体**：按钮高度至少44px，字体至少16px
- **颜色方案**：暖色食品风格——主色#E65100（橙棕），辅色#FFF3E0，成功绿#4CAF50，预警红#F44336
- **手机适配**：用Element Plus的响应式布局，手机上导航栏变为底部Tab栏
- **录入表单要极简**：一个表单尽量在一屏内完成，减少点击次数
- **不要紫色/蓝色渐变**，不要白底黑字纯表格风格

## 权限设计

| 功能 | boss（老板） | clerk（内勤） | leader（班长） |
|------|-------------|--------------|----------------|
| 仪表盘 | ✅ | ✅ | ✅ |
| 原料入库 | ❌ | ✅ | ❌ |
| 生产登记 | ❌ | ✅ | ✅（仅生产） |
| 发货登记 | ❌ | ✅ | ❌ |
| 原料/产品管理 | ✅ | ✅ | ✅（只读） |
| 查看所有记录 | ✅ | ✅ | ✅ |
| 系统设置 | ✅ | ❌ | ❌ |

## 初始数据

系统初始化时自动创建3个用户：
- admin / admin123 → boss 角色
- clerk / clerk123 → clerk 角色  
- leader / leader123 → leader 角色

## 项目目录结构

```
wuai-factory/
├── backend/
│   ├── main.py           # FastAPI 入口 + CORS + 路由挂载
│   ├── database.py       # SQLAlchemy 引擎 + Session + 初始化
│   ├── models.py         # 所有 ORM 模型
│   ├── schemas.py        # Pydantic 请求/响应模型
│   ├── crud.py           # 数据库操作（含三大联动逻辑）
│   ├── auth.py           # JWT 认证
│   ├── init_data.py      # 初始化数据（用户+示例原料+产品）
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── api/index.js          # Axios 封装
│       ├── views/
│       │   ├── Login.vue
│       │   ├── Dashboard.vue
│       │   ├── Materials.vue
│       │   ├── MaterialInbound.vue
│       │   ├── ProductionNew.vue
│       │   ├── ProductionList.vue
│       │   ├── ShipmentNew.vue
│       │   └── ShipmentList.vue
│       ├── components/
│       │   ├── Layout.vue        # 左侧导航+顶部栏
│       │   ├── MobileNav.vue     # 手机底部Tab
│       │   ├── KpiCard.vue       # 仪表盘KPI卡片
│       │   └── AlertBar.vue      # 库存预警条
│       └── styles/
│           └── variables.css     # CSS 变量（主题色）
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
└── CLAUDE.md
```

## 代码规范

- Python: 4空格缩进, type hints, Google style docstrings
- Vue: 2空格缩进, Composition API (setup script)
- 提交信息: 中文, 简洁描述
- 数据库操作用 SQLAlchemy ORM，不要裸SQL
- 所有库存变动必须在同一个数据库事务中完成
- 前端所有API调用走统一的 Axios 实例（带JWT token）

## 部署

- Docker Compose 一键启动
- 后端端口: 8000
- 前端端口: 3000（开发）/ 80（生产，Nginx静态文件）
- Nginx 反向代理 factory.agentmj.vip → 前端 + /api → 后端
- 数据库文件: /data/wuai.db（Docker volume 挂载）

## 开发顺序

1. 先完成 backend（数据库 + 所有API + 库存联动逻辑）
2. 再完成 frontend（所有页面 + API对接 + 手机适配）
3. 最后完成 Docker + Nginx 部署配置
4. 每完成一个阶段就 git commit
