# 五爱工厂管理系统 v3 升级交接文档

> 写给：CC（桌面端开发）
> 写于：2026-08-14，by 墨凌
> 前置动作：请先通读源代码（backend/ 全部 + frontend/src/ 核心），再读本文档。本文档假设你已有代码全局认知。

---

## 一、项目现状快照

| 项 | 状态 |
|---|---|
| 版本 | v2.8（git log 最新 `05ef61d`）+ 2个后续fix |
| 线上地址 | https://wuai.agentmj.vip |
| 服务器 | 香港服务器 43.161.214.98（agentmj.vip 全套同机） |
| 技术栈 | FastAPI + SQLAlchemy同步 + SQLite WAL + Vue3 + Element Plus + ECharts + Vite |
| 代码规模 | 后端 ~3300行（crud.py 1461 / main.py 903）前端 ~5200行（17 views + 5 components） |
| 数据库 | 13张表，66个API路由，17个前端路由 |
| 客户 | 保定五爱食品有限公司（3用户：老板/内勤/班长，全是电脑小白） |
| systemd | wuai-factory.service 端口8190 enabled+Restart=always |
| 证书 | 独立SSL，2026-11-12到期，certbot自动续期 |
| GitHub | whygj/wuai-factory（main分支即生产） |

### 部署关键路径（改完代码后的上线动作）
```bash
# 后端
sudo systemctl restart wuai-factory
# 前端（⚠️ 必须带 --include=dev，服务器npm全局配置omit=dev）
cd /home/ubuntu/projects/active/wuai-factory/frontend && npm install --include=dev && npm run build
# 验证
curl -s -o /dev/null -w '%{http_code}' https://wuai.agentmj.vip/
```

### ⚠️ 服务器环境陷阱（血泪教训，勿踩）
1. **系统python3无venv模块** → 建venv用 `/home/ubuntu/.hermes/hermes-agent/venv/bin/python -m venv`
2. **npm omit=dev** → 构建">npm install --include=dev，否则vite装不上
3. **旧文档失真**：CLAUDE.md还是v2.1的（路径写的 `/data/wuai.db`、旧域名factory.agentmj.vip、密码登录）——**以本文档和REQUIREMENTS-V2.md为准，CLAUDE.md需重写**
4. 禁Docker（老李规矩），systemd直跑
5. git push 用 main 分支；禁 `git add -A`，按文件提交

---

## 二、源代码审查发现的问题清单（按严重度）

### 🔴 P0 — 安全/数据正确性（必须修）

**1. JWT_SECRET 每次重启随机生成**
- `auth.py:14` `SECRET_KEY = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))`
- 后果：服务一重启，所有登录态全失效（用户被登出）。客户3人虽少，但每次部署都掉线体验很差，且24h token过期+重启失效叠加。
- 修法：systemd环境变量固化一个持久SECRET（`Environment=JWT_SECRET=<固定值>`），或在项目根写 `.env` 文件加载。**注意生成后不许进git**（.gitignore已有*.env？实际写的是`.env`，确认覆盖）。

**2. CORS写死旧域名**
- `main.py:18` `allow_origins=["https://factory.agentmj.vip"]`
- 域名已换wuai.agentmj.vip。当前同源部署没触发问题，但这是定时炸弹（将来任何跨域调用直接挂）。
- 修法：改成环境变量注入或直接改成新域名。

**3. 回款金额无校验**
- `schemas.py:333` `PaymentRequest.paid_amount: float` 裸float
- `crud.py:690` `record_payment` 直接 `order.paid_amount += data.paid_amount`
- 后果：可输负数（回款变欠款）、可超额（已付款还能再收）、0元回款刷记录。财务数据不可信。
- 修法：`paid_amount: float = Field(gt=0)` + 业务校验 `paid_amount <= total_amount - order.paid_amount`，前端同步禁输。

**4. 采购单状态机无防呆**
- `crud.py:838` `update_purchase_status` 允许"已入库"→手动改回"待到货"（库存已加却显示未入库，可再次入库→**库存翻倍**）
- 修法：状态机加合法迁移表：`待到货→已入库/已取消`，`已入库→（终态，锁死）`。销售订单 `update_sales_order_status`（crud.py:677）同病：已发货/已签收可随意改回待发货。**所有状态字段都应只允许合法迁移**。

**5. 生产记录的 related_id 关联是"补丁式"实现**
- `crud.py:247` 先插transaction(related_id=0)再`db.flush()`后UPDATE回填
- 弱点：若同一操作员并发登记两笔生产，UPDATE的filter（source=production + related_id=0 + operator）会把**前一笔未回填的事务也改掉**。窗口极小但存在。
- 修法：改为 `transaction.related_id = record.id`（flush后直接对象赋值，不走bulk UPDATE）。

### 🟡 P1 — 功能补全（客户价值高）

**6. 操作日志是死功能**
- 后端有 `/api/operation-logs`（main.py:212）+ OperationLog表，每次增删改都在记
- 但**前端没有任何页面调用它**（全前端搜不到operation-logs引用）——老板查"谁改的"无从查起
- 修法：新增"操作日志"页（boss/clerk可见），按表名/日期/操作人筛选。数据已经在积累，只缺UI，性价比极高。

**7. 数据导出缺失**
- REQUIREMENTS-V2.md第420行明确列了"数据导出—Excel导出"，至今没做
- 工厂场景刚需：报税、对账、给中间人看报表
- 修法：后端加 `/api/export/{module}` 用 openpyxl 生成xlsx（销售明细/采购明细/库存快照/应收账款/生产记录），前端各列表页加"导出Excel"按钮。**别用csv**（Excel打开中文乱码，小白不会处理）。

**8. 数据库零备份**
- SQLite单文件 `/home/ubuntu/projects/active/wuai-factory/data/wuai.db`，无任何备份机制。服务器盘一坏，客户全部业务数据归零。
- 修法：cron每日 `sqlite3 .backup` 或复制db文件到 `backups/`（保留30天）+ 考虑推到COS（腾讯云已有cosfs挂载经验）。systemd timer或服务器crontab均可。**这个可以做成部署侧配置，不用进应用代码。**

**9. 用户管理功能残缺**
- 只能审批/拒绝注册，**不能**：改用户角色、停用/启用账号、删除录错的账号、重置（用户离职换手机号场景）
- 修法：UserManage.vue加编辑弹窗（改display_name/roles/status），后端补 PUT /api/users/{id}（仅boss）。

**10. 删除客户/供应商无保护**
- `crud.py:466` delete_customer 直接删，客户有历史订单时删掉→订单customer_id悬空→报表join报错或客户名显示空
- 修法：删除前检查关联订单数，有订单则拒绝（提示"该客户有N笔历史订单，无法删除"）或改为软删除（status=inactive）。

### 🟢 P2 — 体验/工程质量（有余力再做）

**11. 无任何自动化测试**
- 库存联动（采购入库/生产扣料/发货扣成品）是系统命脉，全靠手测。改crud.py任何一行都心惊。
- 修法：pytest + SQLite内存库，至少覆盖三大联动事务 + 状态机迁移 + 权限矩阵。CI可选（GitHub Actions免费）。

**12. 前端无路由级权限守卫**
- router/index.js 无 beforeEach 权限检查，/users 页面班长直接敲URL能进（页面内可能有v-if但数据API GET全放行）
- 修法：router.beforeEach + localStorage的currentRole校验，users/reports等敏感页非boss重定向。

**13. API超时10s + 无重试**
- `frontend/src/api/index.js` timeout: 10000。报表查询数据量上来后可能超时，用户只看到"请求失败"
- 修法：报表类接口timeout放宽到30s，加loading骨架屏。

**14. 移动端体验深化**
- v2.6/v2.7已做了响应式，但表单类页面（生产登记/新销售订单）手机上多行items录入仍繁琐
- 参考：数字键盘自动唤起（input type=number）、常用原料"上次用量"快捷按钮、扫码枪输入物料编码（可后置）

**15. main.py 903行单文件**
- 66个路由全在一个文件，改一处全文件冲突风险。拆成 routers/（auth/users/materials/products/production/shipments/orders/purchases/receivables/dashboard/reports）+ APIRouter挂载。纯重构，零功能变化，为v3扩展铺路。

---

## 三、v3 升级方向建议（业务层）

基于GitHub调研（Odoo Food ERP / ERPNext batch tracking / jshERP等食品制造业ERP标配功能），对照现状，**食品工厂**最值得补的业务能力：

### 方向A：批次追溯（食品行业命门，差异化价值最高）
现状：原料入库无批次、产品无生产批次、发货不知道发的是哪一批。
- 原料表加 `batch_no` + `expiry_date`（保质期）——食品厂原料有保质期，过期料用进产品是重大食安事故
- 生产记录生成产品批次号（如 P20260814-01），自动关联本次消耗的各原料批次
- 发货记录产品批次 → **正向追溯**（这批原料发给了哪些客户）+ **反向追溯**（这个客诉产品用了哪批料）
- 库存预警增加"临期预警"（expiry_date < today+N天）
- 这是Odoo/ERPNext食品方案的标配，也是客户将来过SC认证/客诉处理时的硬需求。**工作量最大，价值也最大**。

### 方向B：成本核算（老板最关心）
现状：只有销售额，没有利润概念。原料有采购价，产品无成本。
- 产品表加 `standard_cost`（标准成本）或按BOM（配方）自动算：生产登记时按耗料×采购价自动累计该批次成本
- 仪表盘加"本月毛利估算"（销售额-耗料成本）
- 销售报表加单笔订单毛利
- 依赖方向A的批次，或先做简化版（移动加权平均成本）

### 方向C：消息提醒（老板手机用得多）
- 库存低于安全线/原料临期/应收款逾期30天 → 仪表盘红色角标 + 可选微信推送（客户通过微信中间人对接，加个企微/公众号推送通道顺理成章，但涉及新依赖，放最后）

### 建议的v3节奏
1. **v3.0**：P0全修 + 操作日志页 + 数据导出 + 用户管理补全 + 备份cron（2-3天）
2. **v3.1**：批次追溯 + 临期预警（3-5天，含DB迁移，需写migration脚本不能只create_all）
3. **v3.2**：成本核算 + 毛利报表（2-3天）
4. **v3.3**：P2工程质量批（测试+路由拆分+权限守卫，穿插进行）

---

## 四、必须遵守的约束（老李规矩）

1. **技术栈冻结**：FastAPI+SQLAlchemy同步+SQLite / Vue3+Element Plus。不引入PostgreSQL/Redis/新框架。3人小厂，SQLite绰绰有余，别过度设计。
2. **UI铁律**：主色#E65100橙棕、大按钮44px、大字体16px+、一屏完成录入、手机自适应、禁紫蓝渐变。用户是电脑小白，复杂度每+1，客户价值-10。
3. **权限原则**：查看全放开，录入按角色（boss全权/clerk八大模块/leader仅生产+试验室）。
4. **库存事务**：任何库存变动必须同事务+with_for_update行锁（现有代码已这么做，别退化）。
5. **版本号**：v3.x.x，bugfix只动最后一位。
6. **部署验证**：每次上线后跑一遍冒烟（登录→仪表盘→列表→登记一笔→检查库存联动）。
7. **禁git add -A**，按文件提交，commit message中文描述清楚。

---

## 五、快速上手地图

```
backend/
  main.py        # 66路由入口，auth/users/materials/products/production/shipments/orders/purchases/receivables/dashboard/reports/stats
  crud.py        # 1461行业务逻辑，三大库存联动事务在这里（inbound_material:121/create_production:199/create_shipment:296/confirm_inbound:851）
  models.py      # 13张表ORM
  schemas.py     # Pydantic模型（注意PaymentRequest等缺校验的）
  auth.py        # JWT+角色权限（JWT_SECRET问题在这）
  sms.py         # 验证码：生产走miragex代理，SMS_DEV_MODE=1时万能码123456
  database.py    # DB_PATH环境变量→data/wuai.db，WAL+foreign_keys已开
frontend/src/
  views/         # 17页面（Login含注册流程三态：login/register/pending）
  components/    # Layout(382行含导航) / BossDashboard / ClerkDashboard / LeaderDashboard / MobileNav / KpiCard
  api/index.js   # axios统一封装，401自动跳登录
  router/        # 17路由，无权限守卫
```

**调试入口**：https://wuai.agentmj.vip/docs（FastAPI交互文档，nginx已放行）
**管理员**：17800105531（李伟/boss），短信验证码登录（阿里云，经api.miragex.agentmj.vip代理）
**本地测试**：临时开SMS_DEV_MODE=1用万能码123456，**测完必须改回0**（systemd drop-in: /etc/systemd/system/wuai-factory.service.d/）

---

## 六、墨凌的协作方式

- 我管部署、服务器、DNS、SSL、监控；CC管代码、构建、git
- CC改完push到main → 通知老李或我 → 我（或CC直接SSH）在香港服务器 `git pull + restart + build` 上线
- 方案有分歧直接在git issue或文档里吵，别各干各的
- 服务器操作涉nginx/删除/新域名 → 必须先问老李（A/B/C方案），这是铁律
