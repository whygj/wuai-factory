# 五爱食品工厂管理系统

> **保定五爱食品有限公司** — 数字化工厂管理

## 功能

- 📊 **仪表盘首页** — 一目了然看全厂（老板手机首选页）
- 📦 **原料库存管理** — 入库/查询/预警
- 🏭 **生产日报** — 登记生产、自动扣原料、自动增产品
- 🚚 **发货管理** — 登记发货、自动扣产品库存
- 📋 **库存联动** — 三条核心规则自动执行
- ⚠️ **库存预警** — 原料低于安全线自动提醒
- 🔐 **权限管理** — 老板/内勤/班长三种角色

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Element Plus + ECharts |
| 后端 | Python FastAPI + Pydantic |
| 数据库 | SQLite (WAL mode) |
| 部署 | Docker + Nginx |
| 域名 | factory.agentmj.vip |

## 快速开始

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 前端
cd frontend && npm install && npm run dev

# Docker 一键部署
docker-compose up -d
```

## 项目结构

```
wuai-factory/
├── backend/           # FastAPI 后端
│   ├── main.py        # 入口 + 路由
│   ├── models.py      # 数据模型
│   ├── database.py    # 数据库连接
│   ├── crud.py        # 业务逻辑（库存联动核心）
│   └── requirements.txt
├── frontend/          # Vue3 前端
│   ├── src/
│   │   ├── views/     # 页面
│   │   ├── components/  # 组件
│   │   ├── api/       # API 封装
│   │   └── router/    # 路由
│   └── package.json
├── docker-compose.yml
├── nginx.conf
└── CLAUDE.md          # 开发指引
```

## License

MIT
