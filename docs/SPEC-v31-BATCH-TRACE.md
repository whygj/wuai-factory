# v3.1 批次追溯 — 需求规格（给CC）

> 目标：食品厂SC认证硬需求——原料批次+保质期+正反向追溯+临期预警，预埋退货两路径。
> 依据：墨凌流程分析 + CC核验（2026-08-15）+ CC技术提醒（多批次消耗结构）。
> 前置阅读：CLAUDE.md（状态机/三大联动/权限/UI铁律），SPEC-v307-STOCKTAKE.md（盘点已上线，勿动）。

## 0. 现状数据（迁移策略的依据）

线上库：19 原料 / 10 产品 / **0 生产记录 / 0 发货记录**——系统刚上线未录入真实业务。
**迁移策略：存量数据全部走"未分批"兼容层，不做历史回填**。这是唯一不需要数据修复的窗口期，错过就复杂了。

## 1. 表结构（migration：migrate_v31.py，user_version 3→4）

### 1.1 新表 material_batches（原料批次）

```python
class MaterialBatch(Base):
    __tablename__ = "material_batches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    batch_no = Column(Text, nullable=False)              # 批次号：默认自动生成 YYYYMMDD-序号，可手改
    quantity_in = Column(REAL, nullable=False)           # 本批入库量
    quantity_remaining = Column(REAL, nullable=False)    # 本批剩余量（消耗按FEFO扣）
    unit_price = Column(REAL)                            # 本批进价（v3.2成本核算直接用，先存着）
    production_date = Column(Date)                       # 生产日期（供应商标签）
    expiry_date = Column(Date)                           # 保质期到（供应商标签，可空=不管理）
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    status = Column(Text, default="在库")                # 在库/耗尽/报废
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
    # UNIQUE(material_id, batch_no)
```

### 1.2 新表 batch_usages（批次消耗明细）——CC提醒的核心结构

> CC原话：「一次生产消耗多个批次，单字段外键装不下」。所以用关联表，不用任何单字段。

```python
class BatchUsage(Base):
    __tablename__ = "batch_usages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    production_id = Column(Integer, ForeignKey("production_records.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("material_batches.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    quantity = Column(REAL, nullable=False)              # 从该批次扣的量
    created_at = Column(DateTime, default=now_cn)
```

### 1.3 存量表轻量加列

- `products.production_batch_no_prefix`（Text，可空）：产品批次号前缀规则，默认 `{产品名缩写}{YYYYMMDD}-{当日序号}`，本版只存规则不做产品批次表——**产品批次=生产记录本身**（一条生产记录一个批次），不做过度设计。

### 1.4 退货预埋（v3.2 用，本版只建表不建路由）

```python
class ReturnRecord(Base):
    __tablename__ = "return_records"
    id, date, customer_id, sales_order_id, product_id
    quantity, unit_price, total_amount
    return_type = Column(Text, nullable=False)           # 退回入库 / 报废退回（CC提的两路径）
    product_batch_ref = Column(Text)                     # 退回的是哪个生产批次（文本引用，轻量）
    status, operator, notes, created_at
```

## 2. 业务流改造（三大联动动其二，事务结构照旧）

### 2.1 采购确认入库（confirm_inbound）——唯一创建批次的地方

- 确认入库时：除现有逻辑外，**若填了批次号/保质期 → 创建 material_batch 记录**；没填 → 不建批次记录，走旧逻辑（兼容层）
- 入库弹窗加三个可选字段：批次号（留空自动生成）、生产日期、保质期到
- 批次 quantity_in = quantity_remaining = 本单该原料入库量

### 2.2 生产领料（create_production）——FEFO 扣批次

- 班长选原料后，若有在库批次：按 **FEFO（先到期先出，无到期日的按入库先后）** 自动分配扣减顺序，写入 batch_usages
- 原料无批次记录（历史数据/未分批）：不写 batch_usages，只走现有原料总库存扣减——**追溯链断在"未分批"，可接受**
- 前端 ProductionNew 弹窗：每行原料旁显示「将消耗批次：B1(50)→B2(30)」预览（只读提示，不让班长手选批次——小白用户不给他选择负担）
- 库存不足校验照旧（总库存维度，不按批次校验，避免跨批次凑数把人绕晕）

### 2.3 临期预警

- `GET /api/batches/expiring?days=30`：quantity_remaining>0 且 expiry_date ≤ 今天+days，按剩余天数升序
- AlertBar（现有组件）加临期提醒条目；boss/clerk 仪表盘加临期卡片
- 阈值默认30天，Settings 可调（P2，可砍）

## 3. 追溯查询页（/batch-trace，导航放"生产质量"组）

**反向追溯（原料→产品）**：选一个原料批次 → 查 batch_usages → 关联生产记录 → 显示：生产日期/产品/数量/糖度/操作人/该批产品发往哪些客户（经发货记录）

**正向追溯（产品批次→原料）**：选一条生产记录 → 显示消耗的所有原料批次（多批次全列）+ 各批次供应商/生产日期/保质期

- 查询结果表格化，支持 Excel 导出（走现有 /api/export 通道加 module=batch-trace）
- 权限：查看全放开（GET），与现有原则一致

## 4. 顺手带上（CC反馈的SMS修正，sms.py 十行以内）

1. 登录/注册成功后 **整条删除** `_code_store[phone]`（现在只 pop code，条目残留导致60秒频控误伤）
2. 删除死代码 `is_phone_verified` / `verified` 标记
3. 频控 60→30 秒（体验项）

## 5. 明确不做（防过度设计，CC的老规矩）

- 不做产品批次独立表（生产记录即批次）
- 不做条码/扫码
- 不做批次级成本计算（v3.2 用 unit_price 存量直接算，不本版做）
- 不做批次的手工调整/拆并（盘点走 v3.0.7 原料总库存，批次余量不提供盘点——差异随原料总库存调整，批次余量为追溯参考值，不追求绝对精确）
- ReturnRecord 本版只建表，路由/页面 v3.2 做
- 不引入 Alembic（手写 migrate_v31.py，照 migrate_v3.py 模式，user_version 门闩）

## 6. 验收清单（墨凌部署后逐条 E2E）

1. migration：user_version 3→4，四新表创建，存量19原料/10产品无损
2. 采购入库带批次+保质期 → material_batches 落表，FEFO 排序正确
3. 不填批次的入库 → 不建批次记录，旧流程零变化
4. 生产消耗有批次原料 → batch_usages 按FEFO落表（一料跨两批=两行）
5. 生产消耗无批次原料 → 不写 batch_usages，原料总库存照扣
6. 反向追溯：原料批次→生产→客户 全链路显示
7. 正向追溯：生产记录→多批次原料+供应商+保质期
8. 临期30天：造一条31天/一条29天到期批次，只有29天那条出现
9. SMS：登录成功后立即重发不再撞60秒频控（30秒窗口）
10. Chrome 128 老内核回归：新页面/新弹窗零报错（KpiCard 红线照旧）
11. 现有验收清单（CLAUDE.md 七步冒烟）全过——确认没碰坏三大联动
