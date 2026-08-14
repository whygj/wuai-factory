# v3.0.7 库存盘点调整 — 开发规格（给CC）

> 目标：止住账实漂移。半天量级，独立于 v3.1 批次追溯先行上线。
> 原则：最小改动、复用现有事务/行锁/操作日志设施、boss 专属。
> 来源：墨凌流程分析断点① + CC核验确认（REQUIREMENTS-V2 遗留 P2）。

## 1. 范围

- 原料盘点：`POST /api/materials/{id}/adjust`
- 产品盘点：`POST /api/products/{id}/adjust`（CC原方案只提了原料，产品库存同样会漂——生产误计/破损，两个都要）
- Materials.vue / Products.vue 加"盘点"按钮 + 弹窗

## 2. API 设计

### 请求

```
POST /api/materials/{id}/adjust
{
  "actual_stock": 480.0,
  "reason": "6月大盘点，面粉受潮损耗"
}
```

- `actual_stock`：实际清点结果，>= 0，必填
- `reason`：必填，>= 2 字符（差异必须留痕，老板以后查账要能看懂为什么改）

### 行为（单事务，参照现有三条库存联动的写法）

1. `with_for_update` 锁定原料行
2. `diff = actual_stock - current_stock`；`diff == 0` → 422「账实一致，无需调整」
3. 更新 `current_stock = actual_stock`
4. **写 inventory_transactions 流水**：type=`盘点调整`，quantity=diff（带符号：盘盈 + / 盘亏 −），备注=reason，operator=当前用户。没有这条流水，月底对账就对不上——这是本次的红线
5. 写操作日志（复用 v3.0 log_operation）：动作=盘点调整，对象=原料名，详情=`账面500→实际480，差异-20：{reason}`

### 响应

```json
{"old_stock": 500.0, "new_stock": 480.0, "diff": -20.0}
```

### 权限

boss 专属，非 boss → 403「仅老板可盘点调整」（与回款登记同款防御）。盘点是改账动作，班长/内勤物理清点可以，改账必须过老板的手。

### Products 侧

完全同理：`POST /api/products/{id}/adjust`，走 product 侧的 inventory_transactions 通道（生产入库同款）。

## 3. UI（电脑小白标准）

- 行内「盘点」按钮，仅 boss 可见（沿用现有角色判断写法）
- 弹窗三要素：
  1. 账面库存（只读，灰底展示）
  2. 实际数量（number input）
  3. 盘点原因（textarea，必填）
- 实时差异提示：盘盈 +20 绿色 / 盘亏 −20 红色 / 一致则提交按钮禁用
- 成功提示：`已调整：账面 500 → 实际 480（-20）`

## 4. 边界与约束

- `actual_stock < 0` → 422；`reason` 空 → 422
- 与生产/发货并发：现有行锁模式已覆盖
- **盘点流水不可删不可改**：不提供任何 adjust 相关的 PUT/DELETE
- 流水查询页本版不新加（v3.1 批次一起做台账页）

## 5. 验收清单（墨凌部署后逐条 E2E）

1. boss 盘点原料 500→480：库存变 480、流水 −20、操作日志有记录
2. clerk/leader 调 adjust → 403
3. reason 为空 → 422
4. diff=0 → 422
5. Products 侧同样 4 条
6. Chrome 128 老内核回归一遍 Materials/Products 页（emoji/icon 红线照旧）
