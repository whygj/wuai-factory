# v3.4 领用记录台账（原料+添加剂） — 需求规格（给CC）

> 需求来源：客户提出（2026-08-16）——生产模块需要"添加剂领用记录"+"生产原料领用记录"。
> 需求本质：添加剂是**监管刚需**（GB 2760 / SC检查查"五专管理"台账）；原料领用是**台账视图**（数据已有，缺一张能直接看的表）。
> 前置：user_version=6（v3.3），本版 migration 6→7。
> 核心设计原则：**零新增录入步骤**——生产登记照常填，领用台账自动生成。3个电脑小白用户，不加"先打领料单再生产"的手续。

## 0. 前置决策（已拍板）

| 决策点 | 结论 | 依据 |
|---|---|---|
| 领用何时发生 | **生产登记提交时自动记**（同步模式） | 小厂生产领料同节奏；若实测两步对不上再做领料单流程（v3.5备选） |
| 添加剂识别方式 | `raw_materials.category == '添加剂'` | 现有数据吉利丁片/粉已归"添加剂"类；**类别是自由文本，判断用精确匹配**，前端下拉建议类别里含"添加剂" |
| 试验室用添加剂 | 也记台账（source=lab） | 试验记录同样受监管，顺手覆盖 |
| 历史数据 | 不回填（零生产记录，无意义） | 与v3.1迁移策略一致 |
| 台账可改删 | **不可改删，只读** | 监管台账，错了就下一条冲正逻辑都不做——录入时前端确认+后端校验兜住 |

## 1. Migration（migrate_v34.py，user_version 6→7，幂等门闩照旧）

```python
class UsageLog(Base):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)                    # 生产日期（非提交时间）
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    material_name = Column(Text, nullable=False)           # 冗余存名——原料改名后台账保持当时叫法（监管台账不可变语义）
    category = Column(Text)                                # 冗余存类别（同上）
    quantity = Column(REAL, nullable=False)                # 领用量
    unit = Column(Text)
    stock_after = Column(REAL)                             # 领用后库存余量（监管看点）
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(Text)                            # 用途："生产 草莓果酱 300盒"
    production_quantity = Column(REAL)
    production_id = Column(Integer, ForeignKey("production_records.id"))  # source=production时必填
    source = Column(Text, default="production")            # production / lab
    related_id = Column(Integer)                           # lab时=lab_records.id
    operator = Column(Text)                                # 领用人=生产登记操作人
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
```

**冗余字段说明**：material_name/category 刻意冗余——台账的监管语义是"当时发生了什么"，主档后改不该漂移历史（与v3.3 material_cost 快照同一哲学）。

## 2. 写入时机（改动最小化）

### 2.1 `create_production`（crud.py）

在现有事务内、`batch_usages` 落表之后、`commit` 之前，对 `materials_used` 每条料追加一行 UsageLog：

- date=data.date, quantity=usage.quantity, unit=usage.unit or material.unit
- stock_after = 扣减后的 material.current_stock（此时已在事务中扣过，直接取值）
- product_name/product_id/production_quantity/production_id/record.id 照填
- operator=操作人

**注意**：一条生产N种料=N行UsageLog，事务回滚时自动一起消失——台账与生产记录强一致。

### 2.2 试验室路径（如果 lab_records 有用料字段）

CC先查：lab_records 现有结构是否记原料消耗。有→同法写入（source=lab）；没有（纯文本配方）→**本版跳过lab**，在交付说明里注明"试验记录不涉库存扣减，无领用事实，不记台账"。不要为了覆盖而硬造字段。

## 3. 查询接口（两个，全角色可看）

### 3.1 `GET /api/usage-logs`

参数：`start_date / end_date / material_id / category / source / page / page_size`（复用现有分页风格）

返回：total + items（含全部台账字段）。按 id 倒序。

### 3.2 `GET /api/usage-logs/additive-summary`

添加剂台账专用汇总（监管表最常用形态）：

```
参数：start_date / end_date
返回：[{material_name, total_used, unit, use_count, last_used_date}]
按 total_used 降序
```

过滤条件：`category == '添加剂'`（精确匹配）。

## 4. 前端

### 4.1 新页面 `/usage-logs`（导航"生产质量"组，名称「领用记录」）

**Tab1 原料领用台账**：
- 筛选：日期范围 + 原料下拉 + 类别下拉
- 表格：日期/原料/类别/数量/单位/用途(产品+产量)/领用人/**领用后余量**/来源(生产/试验)
- 类别=添加剂的行：类别列橙色标签（el-tag type=warning）

**Tab2 添加剂台账**（监管视图）：
- 顶部说明条（浅橙底）："按 GB 2760 食品添加剂管理要求记录，供监督检查使用"
- 汇总表：添加剂/累计用量/使用次数/最近使用
- 明细表：Tab1 过滤 category=添加剂 的数据
- **「导出Excel」按钮**（醒目，检查时直接打表）

### 4.2 生产登记弹窗（ProductionNew.vue）

原料行若类别=添加剂 → 原料名旁加橙色小徽章「添加剂」。仅视觉提示，不加交互。

### 4.3 Chrome 128 红线照旧

新页面 KpiCard/图标一律组件对象或文本，禁 emoji 字符串进动态组件。

## 5. 导出

- `GET /api/export/usage-logs`（参数同3.1）→ 现有Excel通道
- `GET /api/export/additive-usage`（参数同3.2）→ 列：添加剂名称/累计用量/单位/使用次数/最近使用日期/本期明细行……CC按现有 /api/export/{module} 模式实现，表头中文，日期列文本格式（防Excel转日期错乱）

## 6. 明确不做（防过度设计）

- 不做领料单/审批/核销流程（同步模式，实测两步脱节再上v3.5）
- 不做台账编辑/删除/冲正（只读+录入时校验兜底）
- 不做添加剂库存上限预警（GB 2760用量合规计算太重，不是台账职责）
- 不做双签（电子签名无法律效力，纸质台账才需要）
- 不回填历史
- lab路径视现有结构而定，不为覆盖而造字段

## 7. 验收清单（墨凌部署后E2E）

1. migration 6→7 幂等，usage_logs表创建，存量无损
2. 生产登记（含添加剂吉利丁片+普通原料淡奶油）→ 两条UsageLog落表，stock_after=扣减后余量精确
3. 生产事务回滚场景（库存不足422）→ 台账**不落行**（强一致验证）
4. 原料改名后 → 台账历史行仍显示旧名（冗余字段验证）
5. GET /api/usage-logs 分页+日期筛选正确
6. additive-summary 只聚合category=添加剂，普通原料不进
7. 两种Excel导出：文件可开、表头中文、添加剂表含汇总行
8. /usage-logs 页两Tab渲染正常，添加剂行橙色标签
9. 生产弹窗添加剂徽章显示
10. Chrome 128 老内核回归：/usage-logs + 生产弹窗零报错
11. CLAUDE.md 七步冒烟全过
