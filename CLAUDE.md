# 五爱食品工厂管理系统 — 开发指引 v2.1

## 重要：请先读 REQUIREMENTS-V2.md 获取完整需求

本文档是技术执行指引。完整需求分析在 `REQUIREMENTS-V2.md`。

## 项目背景

客户：**保定五爱食品有限公司**（小型食品加工厂，产品为甜品/果酱/巧克力）
- 所有用户都是电脑小白，UI必须极简——大按钮、大字体、仪表盘优先
- 替代现有混乱的纸质手写记录

## 现有代码结构

```
wuai-factory/
├── backend/
│   ├── main.py           # FastAPI 入口 + CORS + 路由（275行）
│   ├── database.py       # SQLAlchemy + SQLite WAL
│   ├── models.py         # 7个ORM模型（109行）
│   ├── schemas.py        # Pydantic模型（206行）
│   ├── crud.py           # 数据库操作+库存联动（363行）
│   ├── auth.py           # JWT认证
│   ├── init_data.py      # 初始化数据（3用户+19原料+10产品）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/        # Login, Dashboard, Materials, Production*, Shipment*
│   │   ├── components/   # Layout, MobileNav, KpiCard, AlertBar
│   │   ├── api/index.js  # Axios封装
│   │   └── router/index.js
│   └── vite.config.js
├── REQUIREMENTS-V2.md    # ← 完整需求分析文档
└── CLAUDE.md             # ← 本文件
```

## 技术栈（固定，不要改）

- **后端**: Python FastAPI + Pydantic + SQLAlchemy（同步模式） + SQLite WAL
- **前端**: Vue 3 + Element Plus + ECharts + Vue Router + Vite
- **部署**: systemd + Nginx 反代 (factory.agentmj.vip)
- **Python**: /home/ubuntu/.hermes/hermes-agent/venv/bin/python
- **数据库**: /data/wuai.db

## 开发任务（v2.1 分3批）

### 第一批：基础设施（用户系统+客户+供应商）

#### 1.1 用户系统改造
- User表加 `phone` 字段（手机号，登录用）
- User表加 `roles` 字段（JSON数组，一个人可以有多个角色：["boss","clerk"]）
- 登录改为手机号+密码
- 登录成功返回该用户的角色列表
- 新增 `POST /api/auth/select-role` — 选择当前角色（存到JWT里或session）
- 修改 `init_data.py`：3个用户都加手机号
  - admin/boss: 13800000001
  - clerk/内勤: 13800000002
  - leader/班长: 13800000003
- 密码不变：admin123/clerk123/leader123

#### 1.2 权限中间件重写
- **查看权限**：所有已登录用户都能查看所有模块（GET请求全部放行）
- **录入权限**：按当前角色检查（POST/PUT/DELETE检查）
- 权限配置表（硬编码在代码里即可）：
```python
ROLE_PERMISSIONS = {
    "boss": ["all"],  # 全部权限
    "clerk": ["customer", "supplier", "purchase", "inbound", "production", "sales", "shipment", "lab"],
    "leader": ["production", "lab"],
}
```

#### 1.3 客户管理
- 新增 `customers` 表（name, contact, phone, address, type, level, notes）
- CRUD API: GET/POST/PUT/DELETE /api/customers
- GET /api/customers/{id}/summary（该客户的累计订单、累计金额、最近交易）
- 前端：Customers.vue 列表页 + 新增/编辑弹窗
- 路由：/customers

#### 1.4 供应商管理
- 新增 `suppliers` 表（name, contact, phone, address, category, notes）
- CRUD API: GET/POST/PUT/DELETE /api/suppliers
- 前端：Suppliers.vue 列表页 + 新增/编辑弹窗
- 路由：/suppliers
- raw_materials 表加 `supplier_id` 字段关联供应商

#### 1.5 登录页改造
- Login.vue 改为手机号输入框
- 新增 RoleSelect.vue（角色选择页）
- 如果用户只有1个角色，自动跳转对应仪表盘
- 如果有多个角色，显示角色选择卡片
- Layout.vue 顶部显示当前角色+切换按钮

---

### 第二批：销售管理+采购管理+应收款

#### 2.1 销售订单
- 新增 `sales_orders` 表（order_no, date, customer_id→关联客户, items JSON, total_amount, status, payment_status, paid_amount）
- API:
  - GET/POST /api/sales-orders（列表+创建）
  - PUT /api/sales-orders/{id}/status（更新状态）
  - PUT /api/sales-orders/{id}/payment（登记回款）
  - GET /api/sales-orders/stats（销售统计：按客户/产品/时间段）
- 发货逻辑：销售订单确认发货时自动扣产品库存
- 前端：SalesOrders.vue + SalesOrderNew.vue
- 路由：/sales-orders, /sales-orders/new

#### 2.2 采购管理
- 新增 `purchase_orders` 表（order_no, date, supplier_id→关联供应商, items JSON, total_amount, status）
- API:
  - GET/POST /api/purchases（列表+创建）
  - PUT /api/purchases/{id}/status（确认到货→自动入库→原料库存增加）
- 采购入库联动：确认到货时自动创建 inventory_transactions + 增加原料库存
- 前端：Purchases.vue + PurchaseNew.vue
- 路由：/purchases, /purchases/new

#### 2.3 应收款管理
- GET /api/receivables（所有未回款的销售订单）
- GET /api/receivables/overdue（逾期未回款）
- 前端：Receivables.vue
- 路由：/receivables

#### 2.4 现有发货改造
- shipment_records 表加 `sales_order_id` 关联销售订单
- 发货从销售订单发起（不是单独创建）
- 保留原有的独立发货能力（直接发货不关联订单）

---

### 第三批：仪表盘重做+试验室+收尾

#### 3.1 老板仪表盘（重做Dashboard.vue）
- 拆成3个组件：BossDashboard.vue / ClerkDashboard.vue / LeaderDashboard.vue
- 新增API：
  - GET /api/dashboard/boss（本月销售额、应收款总额、库存预警数、今日动态、客户TOP5、产品TOP5、销售趋势）
  - GET /api/dashboard/clerk（待发货、待入库、库存预警、今日动态）
  - GET /api/dashboard/leader（今日产量、原料够不够、7天趋势）
  - GET /api/dashboard/today-activities（今日所有操作的统一时间线）

#### 3.2 试验室管理
- 新增 `lab_records` 表（date, name, recipe JSON, process_params, result, score, notes）
- API: GET/POST/PUT /api/lab
- 前端：LabRecords.vue + LabRecordNew.vue
- 路由：/lab, /lab/new

#### 3.3 导航栏重做
- Layout.vue 左侧导航更新为完整菜单：
  - 📊 仪表盘
  - 👥 客户管理
  - 🏭 供应商
  - 📦 采购管理
  - 🧈 原料库存
  - 🏭 产品库存
  - ⚙️ 生产管理
  - 🔬 试验室
  - 🚚 销售发货
  - 💰 应收款
  - 📊 经营报表
  - ⚙️ 系统设置（仅boss）
- 录入按钮用 `v-if="canEdit('模块名')"` 控制

#### 3.4 经营报表
- GET /api/reports/sales（销售汇总：按时间/客户/产品）
- GET /api/reports/inventory（库存报表：周转率/价值估算）
- GET /api/reports/production（生产报表：按日/周/月产量）
- 前端：Reports.vue（3个Tab页）
- 路由：/reports

---

## UI要求（极其重要）

- **主色 #E65100**（橙棕色），辅色 #FFF3E0
- **大按钮**（44px高），**大字体**（16px+），极简操作
- **手机端自适应**，底部Tab导航
- **禁止紫色/蓝色渐变，禁止白底黑字纯表格**
- Element Plus组件：el-button, el-form, el-table, el-select, el-dialog, el-card
- 录入表单一屏完成，减少点击次数
- ECharts：折线图、饼图、柱状图

## 代码规范

- Python: 4空格缩进, type hints
- Vue: 2空格缩进, Composition API (`<script setup>`)
- 所有库存变动必须在同一个数据库事务中完成
- 前端所有API调用走统一的 Axios 实例（带JWT token）
- 后端Python路径: /home/ubuntu/.hermes/hermes-agent/venv/bin/python
- 数据库路径: /data/wuai.db

## 验证

每完成一批后：
1. 重启后端：`sudo systemctl restart wuai-factory`
2. 重新build前端：`cd /home/ubuntu/wuai-factory/frontend && npm run build`
3. 测试新API端点
4. 浏览器打开 https://factory.agentmj.vip 验证页面

## Git

每完成一批就 commit + push：
```bash
cd /home/ubuntu/wuai-factory
git add -A
git commit -m "v2.x: 描述"
git push origin main
```
