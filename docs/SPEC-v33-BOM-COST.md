# v3.3 BOM配方+成本核算 — 需求规格（给CC）

> 依据：墨凌流程分析 + CC四项技术预判（2026-08-16 全数采纳）+ v3.1/v3.2 已有设施。
> 前置：user_version=5（v3.2），本版 migration 5→6。
> 定位：最后一块拼图——班长少抄数、老板看清钱。

## 0. 前置决策（拍板，不留自由发挥）

| 决策点 | 结论 | 依据 |
|---|---|---|
| BOM结构 | **基准批量**（如"每100盒用黑巧2kg"），不做配方版本 | CC预判①，换算在后端做 |
| 成本口径 | **实际消耗法**：`Σ(batch_usages.quantity × material_batches.unit_price)`，未分批回退 `raw_materials.purchase_price` | CC预判②，v3.1桩直接兑现 |
| 毛利口径 | **月度粗毛利 = 当月订单收入 − 当月生产原料消耗**，页面明示「不含人工水电房租」 | CC预判④，单笔归因留给v3.4 |
| 领料方式 | 选产品+填产量→按BOM后端换算预填→**可改**（原料替代场景）→FEFO照旧 | CC预判③ |
| BOM维护权限 | boss + leader（班长最懂配方）；领料照旧 leader+clerk | 生产质量域 |

## 1. Migration（migrate_v33.py，user_version 5→6，幂等门闩）

```python
class Bom(Base):
    __tablename__ = "boms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    base_quantity = Column(REAL, nullable=False)        # 基准批量：如100（盒）
    base_unit = Column(Text, nullable=False)            # 基准单位：盒
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    material_quantity = Column(REAL, nullable=False)    # 该批量下用量：2（kg）
    material_unit = Column(Text, nullable=False)        # kg
    notes = Column(Text)
    created_at / updated_at
    # UNIQUE(product_id, material_id) —— 一个产品一份配方，一料一行；改配方=改行，无版本

# production_records 加两列（存成本快照，报表不再回算历史）
ALTER TABLE production_records ADD COLUMN material_cost REAL;          # 该次生产原料成本（可空=登记时算不出）
ALTER TABLE production_records ADD COLUMN bom_snapshot TEXT;           # 本次生产用的配方快照JSON（可空）
```

**material_cost 快照的意义**：批次进价会变、配方会改，报表按快照算，历史不漂移。

## 2. BOM 维护

### 2.1 接口

- `GET /api/products/{id}/bom` — 查看（全角色）
- `PUT /api/products/{id}/bom` — **boss+leader**，整体保存：`{base_quantity: 100, base_unit: "盒", items: [{material_id, material_quantity, material_unit}]}` 整体替换（先删后插，事务内）
- 校验：base_quantity>0、每行用量>0、material存在；单位不做换算校验（原料kg对产品盒是常态，警告都不用）

### 2.2 UI

产品管理页（Products.vue）行内「配方」按钮 → 弹窗：基准批量+原料行（选原料/用量/单位），无配方的产品显示"未设置配方"空态+引导按钮。**弹窗内显示成本试算**：按当前批次进价/回退价实时算出"每基准批量成本"和"单位成本"（只读展示）。

## 3. 生产领料改造（ProductionNew.vue + 换算接口）

### 3.1 换算接口

- `POST /api/production/preview-bom`：`{product_id, quantity, unit}` → 按基准批量等比换算返回每料用量明细（含当前库存是否够）。**纯计算无副作用**，前端预填用。

### 3.2 前端流程

1. 班长选产品+填产量
2. 有BOM → 调 preview-bom 预填全部原料用量（**每行可改**，可删行可加行——替代原料场景）
3. 无BOM → 现状手填，顶部提示「该产品未设配方，可在产品管理中设置」
4. 提交走现有 `POST /api/production`，**后端不动**（用量已在请求里）
5. `create_production` 内加一步：登记成功时计算 material_cost 快照写入（用batch_usages×批次价，未分批部分回退原料档案价；全算不出则留空）+ bom_snapshot 存提交时用量

### 3.3 库存不足预检

preview-bom 返回每料 `sufficient: true/false`，前端行内红字提示「库存不足，当前X需Y」——**事前预检**，提交时后端照旧校验（双保险）。

## 4. 成本与毛利报表

### 4.1 生产成本页（/cost，导航"经营分析"组）

- 月度卡片：当月生产次数/总产量/原料消耗总额（Σ material_cost 快照）
- 明细表：按生产记录列——日期/产品/数量/原料成本/单位成本/操作人
- 产品维度汇总：每款产品当月产量×成本（老板看哪款烧钱）

### 4.2 毛利视图（并入经营报表 Reports.vue 加"毛利"Tab）

```
本月销售收入（订单额）      ¥120,000
本月原料消耗（生产成本）    ¥50,000
—— 粗毛利                  ¥70,000（58%）
注：不含人工/水电/房租/包装
```

**月度口径**（CC预判④）：收入=当月订单total，消耗=当月生产快照。两者天然有时间错位（3月生产4月卖），页面用小字注明「按月汇总，生产与销售存在时间错位」。

### 4.3 权限

查看=全角色。成本数据敏感？——3人厂老板内勤班长都该看，不设限。

## 5. 明确不做（防过度设计）

- 不做配方版本/生效日期（改了就改了，bom_snapshot留底）
- 不做人工/水电/包装成本录入（无数据源，明示口径即可）
- 不做单笔订单毛利归因（v3.4看数据再说）
- 不做BOM审批流
- 不做单位自动换算（kg/L/盒并存，靠人填对）
- 不做成本重算工具（快照即历史，错了下次改对，不回溯）

## 6. 验收清单（墨凌部署后E2E）

1. migration 5→6 幂等，boms表+production_records两列，存量无损
2. 设配方"每100盒：E2E原料2kg" → 落表
3. preview-bom：产量300盒 → 返回E2E原料6kg、含库存够否
4. 无配方产品预览 → 提示未设配方
5. 生产300盒（预填6kg改5kg提交）→ 库存扣5kg、material_cost快照=5×批次价、bom_snapshot记录5kg
6. 未分批原料生产 → material_cost回退档案价计算
7. /cost 页当月成本汇总正确（与快照Σ一致）
8. Reports毛利Tab：收入-消耗-粗毛利三行+口径注释
9. BOM维护权限：clerk改配方→403；leader可改
10. Chrome 128 老内核：/cost、配方弹窗、生产预填零报错（KpiCard红线照旧）
11. CLAUDE.md 七步冒烟全过（三大联动未被碰坏）
