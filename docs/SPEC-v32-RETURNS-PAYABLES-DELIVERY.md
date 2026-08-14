# v3.2 退货+应付+送货单 — 需求规格（给CC）

> 依据：墨凌流程分析 + CC四项技术预判（2026-08-15全数采纳）+ v3.1已预埋的 return_records 表。
> 前置：user_version=4（v3.1），本版 migration 4→5。

## 0. 范围与前置决策（不留自由发挥空间）

| 决策点 | 结论 | 依据 |
|---|---|---|
| 退货冲应收方向 | **方案A：直接减订单 total_amount + 操作日志留痕**（原额X→现额Y） | 3人小厂，B方案的抵扣逻辑复杂度不值 |
| 全额回款后退货 | 允许 paid_amount > total_amount，应收列表显示「应退款X元」（负应收） | 不能假装这种情况不存在 |
| 退货库存语义 | **退回入库仅加 current_stock 总量，不做可用库存区分**（已告知老李此限制） | 现状无批次隔离，天然限制 |
| 送货单打印源 | **从发货记录（ShipmentRecord）打印，不从订单** | 分批发货场景司机拉的是"这一车" |
| 纸型 | A4 纵向 | 办公室打印机默认纸 |

## 1. Migration（migrate_v32.py，user_version 4→5，幂等门闩照旧）

```python
# 1) purchase_orders 加两列（CC预判①：无字段可复用，必须加列）
ALTER TABLE purchase_orders ADD COLUMN paid_amount REAL DEFAULT 0;
ALTER TABLE purchase_orders ADD COLUMN payment_status TEXT DEFAULT '未付款';

# 2) 新表 purchase_payments（付款流水）
class PurchasePayment(Base):
    __tablename__ = "purchase_payments"
    id, purchase_order_id(FK), amount(REAL>0), date(Date),
    method(Text)            # 转账/现金/承兑，自由文本
    status(Text, default="有效")   # 有效/已作废
    operator, notes, created_at

# 3) return_records 表v3.1已建，本版只加路由——若缺列(date/customer_id等已含)则零改动
```

## 2. 供应商付款（老板管钱的另一半）

### 2.1 接口

- `POST /api/purchases/{id}/payments` `{amount, date, method, notes}` — **boss专属403**（与回款登记同款防御，钱出账必过老板）
- `PUT /api/purchase-payments/{id}/void` — **boss专属**。作废=逆向恢复：paid_amount -= 该笔，重算 payment_status，流水 status='已作废'（**流水不物理删**），操作日志留痕
- 付款后自动重算：`paid_amount==0→未付款 / 0<已付<total→部分付款 / 已付>=total→已付款`（复用sales侧状态机命名，保持一致）

### 2.2 应付款页（/payables，导航"销售财务"组）

- 顶部汇总卡片：总应付 / 本月已付 / 欠款总额（3张KpiCard，**icon用组件对象别用emoji字符串——Chrome128红线**）
- 明细表：按采购单列——单号/日期/供应商/总额/已付/欠款/状态/操作(付款登记)
- 供应商维度小计可不做（列表搜索够用），老板问"欠某家多少"直接搜

### 2.3 权限

付款登记/作废=boss专属；应付款页查看=全角色（与"查看全开放"原则一致）。

## 3. 退货

### 3.1 接口与状态机

- `POST /api/returns` — **clerk + boss 可登记**（退货是销售侧业务录入，内勤处理常态；leader不可）
- 请求：`{date, customer_id, sales_order_id, product_id, quantity, unit_price, return_type, notes}`
  - `return_type`: `退回入库` / `报废退回`（CC预埋的两路径）
- 事务行为（单事务+行锁）：
  1. 写 return_records（status=有效）
  2. 订单 `total_amount -= quantity × unit_price`，**操作日志记「退货冲减：原额X→现额Y」**（方案A留痕）
  3. return_type=退回入库 → 产品 `current_stock += quantity` + product_transactions 流水（type=退货入库，复用v3.0.7通道）
  4. return_type=报废退回 → 不碰库存
- `PUT /api/returns/{id}/void` — **boss专属**。作废=完全逆向：total_amount加回、退回入库的减回、流水记负向冲正行、status=已作废
- 校验：quantity>0；退货数量不得超过该订单该产品已发数量（查shipment_records聚合，防虚退）

### 3.2 应收款页联动

- 未收金额 = total_amount - paid_amount，退货后自动变小（零额外代码）
- paid_amount > total_amount 的订单 → 应收列表该行红字显示「应退款 ¥X」

### 3.3 页面入口

退货登记入口放**销售发货页**（行内「退货」按钮，自动带出订单/客户/产品）+ 应收款页顶部「登记退货」按钮。不单独做退货列表页——退货记录在订单详情弹窗里列出（含作废按钮）。

## 4. 送货单打印（零后端）

### 4.1 入口

- 发货记录列表行内「打印」按钮 → 打开打印视图（新窗口或覆盖层）
- 数据源：现有 shipment 接口 + 订单明细，**不新增任何后端路由**

### 4.2 版式（A4纵向，@media print）

```
        五爱食品 送货单
单号：SHP-20260815-001        日期：2026-08-15
客户：烘焙店B  138xxxx  地址：xxx
─────────────────────────────
产品      规格    数量   单位   单价    金额
草莓果酱  500g    40     箱    120    4,800
─────────────────────────────
合计：¥4,800
司机签字：________  客户签字：________
收货日期：________
（小字：退货请在收货时当面清点提出）
─────────────────────────────
打印时间/操作人（页脚灰字）
```

- `window.print()` 触发；`@media print` 隐藏导航/按钮/侧栏
- 单价可空（订单没填单价时金额列显示—）

## 5. 明确不做（防过度设计）

- 不做供应商对账单导出（Excel导出通道后续要就加 module=purchases，本版不加）
- 不做退货的批次回写（退回货不回写material_batches/product批次，v3.1定位就是参考值）
- 不做可用库存/冻结库存区分（老李已知情）
- 不做付款审批流（3人厂无审批）
- 不做打印模板切换（单一A4模板）

## 6. 验收清单（墨凌部署后E2E）

1. migration 4→5 幂等，存量采购单 paid_amount=0/未付款 无损
2. boss付款登记100（订单总额300）→ paid_amount=100、状态=部分付款、流水落表
3. clerk付款 → 403
4. 付款作废 → paid_amount恢复、流水status=已作废（不物理删）、状态重算
5. 退回入库退货10件 → 订单total减、产品库存+10、product_transactions流水、操作日志「原额→现额」
6. 报废退回 → 订单total减、库存不动
7. 超过已发数量退货 → 422
8. 退货作废 → total恢复、库存减回、负向流水
9. 全额回款订单退货 → 应收列表显示「应退款」
10. 送货单打印：发货记录点打印 → A4版式含双签字栏，print CSS隐藏导航
11. Chrome 128 老内核回归：/payables + 退货弹窗 + 打印视图零报错（KpiCard icon红线）
12. CLAUDE.md 七步冒烟全过（三大联动未被碰坏）
