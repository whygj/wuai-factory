# 五爱食品工厂管理系统 — 开发指引 v3.0

## 重要：先读 docs/HANDOFF-CC-v3-UPGRADE.md（交接文档）

本文件是技术速查。完整背景、P0-P2问题清单、v3路线图在交接文档里。

## 项目背景

客户：**保定五爱食品有限公司**（小型食品加工厂，甜品/果酱/巧克力）
- 3个用户（老板/内勤/班长），全是电脑小白——UI必须极简：大按钮44px、大字体16px+、一屏完成录入
- 替代纸质手写记录；手机端使用频繁

## 部署关键信息（v3.0 现状）

- **线上**: https://wuai.agentmj.vip（香港服务器 43.161.214.98）
- **systemd**: `wuai-factory.service`，端口 **8190**，禁Docker（老李规矩）
- **数据库**: `data/wuai.db`（SQLite WAL，user_version=3 表示已完成时区迁移）
- **本地Python**: `/home/ubuntu/.hermes/hermes-agent/venv/bin/python`

```bash
# 后端上线
sudo systemctl restart wuai-factory
# 前端上线（服务器npm omit=dev，必须 --include=dev）
cd frontend && npm install --include=dev && npm run build
# 验证
curl -s -o /dev/null -w '%{http_code}' https://wuai.agentmj.vip/
```

### 服务器陷阱
1. 系统python3无venv模块 → 用 hermes venv 的 python -m venv
2. npm omit=dev → 构建前必须 `npm install --include=dev`
3. 测试短信：SMS_DEV_MODE=1 万能码123456（systemd drop-in），**测完必须改回0**
4. git push 用 main；禁 `git add -A`，按文件提交

## 代码结构

```
backend/
  main.py        # 路由入口（~980行，含Excel导出）
  crud.py        # 业务逻辑+库存联动事务
  models.py      # 13张表ORM
  schemas.py     # Pydantic（数量/金额字段都有 gt=0/ge=0 校验，别退化）
  auth.py        # JWT（SECRET持久化在 data/.jwt_secret）+角色权限
  sms.py         # 验证码：MirageX代理 / SMS_DEV_MODE=1 万能码
  database.py    # DB_PATH环境变量 → data/wuai.db，WAL+foreign_keys
  utils.py       # now_cn() 北京时间（所有时间戳用这个，别用utcnow）
  export_excel.py# openpyxl 导出5模块
  migrate_v3.py  # 一次性UTC→北京时区迁移（user_version=3，已执行）
frontend/src/
  views/         # 18页面（含 OperationLogs.vue）
  components/    # Layout / Boss/Clerk/LeaderDashboard / MobileNav / KpiCard / AlertBar
  api/index.js   # axios统一封装（blob导出走 downloadExport）
  router/        # 路由守卫：boss页(/users /operation-logs)非boss重定向
scripts/
  backup_db.sh   # 每日备份（crontab: 30 2 * * *），保留30天
```

## 核心业务规则（改代码前必懂）

1. **三大库存联动**（crud.py，都有 with_for_update 行锁+同事务提交，不可退化）：
   - 采购入库 `confirm_inbound`：待到货→已入库，原料库存+
   - 生产 `create_production`：逐原料锁+扣料，产品库存+
   - 发货 `create_shipment`：产品库存-，订单关联时校验剩余可发量，自动推进订单状态
2. **状态机**（合法迁移表，终态锁死）：
   - 采购单：待到货→已到货/已入库/已取消；已入库是终态；"已入库"必须走确认入库按钮
   - 销售订单：待发货→部分发货→已发货→已签收；有发货记录不能取消
   - 发货：待发货→已发货→已签收，只能向前
3. **权限**：查看全放开（GET），录入按角色。回款仅boss。产品档案 product 模块（boss/clerk）
4. **删除保护**：有订单/发货记录的客户、有采购单/原料关联的供应商拒绝删除
5. **时间**：全部北京时间 `now_cn()`；JWT exp 仍用 UTC（jose按epoch校验）
6. **用户停用**：auth._decode_token 校验 status==approved，停用立即生效

## UI铁律

- 主色 **#E65100**（橙棕），辅色 #FFF3E0；禁紫/蓝渐变
- 大按钮（44px高）、大字体（16px+）、一屏完成录入
- 手机端自适应：≤768px 切卡片列表+底部Tab（MobileNav）
- ECharts 用 GridComponent（不是 GridRenderer，踩过坑）

## 验证清单（每次上线跑一遍）

1. 登录 → 仪表盘 → 各列表页加载
2. 登记一笔采购→确认入库→原料库存+
3. 登记一笔生产→原料库存-、产品库存+
4. 建销售订单→发货→订单状态推进、产品库存-
5. boss登记回款→金额/状态正确；clerk回款→403
6. 导出Excel→文件能打开中文正常
7. 操作日志页有新记录

## v3 后续路线（交接文档第三节）

- v3.1: 批次追溯（原料批次+保质期+产品批次号+正反向追溯+临期预警）——需写migration
- v3.2: 成本核算（移动加权平均/标准成本+毛利报表）
- v3.3: 工程质量批（pytest覆盖库存联动+路由拆分routers/）
