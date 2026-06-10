# CQAssert - 夯实多模态数据管理能力

前后端分离的Web项目，基于《夯实多模态数据管理能力》详细设计文档V1.0实现。

## 技术栈

- **前端**: React 18 + Vite + Ant Design 5 + React Router 6
- **后端**: Python 3.11+ + FastAPI + SQLAlchemy + Pydantic
- **数据库**: MySQL 8.0
- **缓存**: Redis（可选，用于查询频次控制）

## 项目结构

```
.
├── backend/              # Python后端
│   ├── app/
│   │   ├── main.py       # FastAPI入口（含lifespan启动）
│   │   ├── config.py     # 配置管理
│   │   ├── database.py   # 数据库连接
│   │   ├── models/       # SQLAlchemy模型（28张表）
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py    # 数据集相关模型
│   │   │   ├── asset.py      # 资产/稽核相关模型
│   │   │   └── upload_mid.py # 集团上报中间表+支持表模型（新增）
│   │   ├── routers/      # API路由（8个模块）
│   │   ├── schemas/      # Pydantic数据校验
│   │   ├── services/     # 业务服务层
│   │   ├── upload_engine.py  # 集团上报5步流程引擎（新增）
│   │   ├── services/
│   │   │   ├── audit_engine.py  # 稽核规则引擎
│   │   │   ├── desensitize.py   # 数据脱敏
│   │   │   ├── eop_client.py    # EOP网关客户端
│   │   │   ├── rate_limit.py    # 查询频次控制
│   │   │   └── unique_id.py     # 唯一标识生成
│   ├── requirements.txt
│   ├── run.py            # 开发启动脚本
│   ├── init_db.py        # 数据库初始化
│   └── seed_data.py      # 种子数据
├── frontend/             # React前端
│   ├── src/
│   │   ├── pages/        # 12个业务页面
│   │   ├── components/   # 公共组件
│   │   ├── services/     # API请求封装
│   │   └── App.jsx       # 路由配置
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 快速开始

### 1. 数据库准备

```sql
CREATE DATABASE cqassert DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 配置数据库连接信息

# 初始化数据库表并灌入种子数据
python init_db.py
python seed_data.py

# 启动服务
python run.py
```

后端默认运行在 http://localhost:8000，API文档: http://localhost:8000/docs

### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 http://localhost:5173

## 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| user | user123 | 普通用户 |

## 功能模块实现清单

### 模块一：高质量数据集元模型设计 ✅
- 56字段完整模型，4组分组（基础信息/存储信息/结构属性/生命周期）
- 知识库/语料/提示词扩展属性
- 数据集CRUD API + 质量信息管理
- 7条种子数据集（覆盖全部4种类型）

### 模块二：多模态数据集目录构建 ✅
- 树形目录结构（领域→场景→细类，3层）
- 目录CRUD + 树形展示
- 目录查询与详情展示（Tab页：基础信息/质量/存储/生命周期）

### 模块三：数据资产盘点闭环 ✅
- **资源类**: 系统/数据库/表/字段四层上传中间表
- **资产类**: 标签/指标/API/产品/非结构化上传中间表
- **多模态类**: 高质量数据集上传中间表
- **稽核规则引擎**:
  - 8条多模态稽核规则（MM-001~MM-008）
  - 真实规则评估逻辑（非空/格式/一致性/数量）
  - 稽核结果写入 + 合规状态更新
- **唯一标识生成能力**: 9类资产ID生成原子能力
- **AI补全**: MetadataCompleteLog模型，预留AI补全接口

### 模块四：集团上报功能 ✅

**五步上报流程（根据评审意见重构V1.1）：**

```
本地元数据 → [同步到中间表] → 中间表稽核 → [修改中间表] → 合规→ [同步到结果表] → [上传集团]
                                                                    不合规→ 修改→重新稽核
```

- **4个资源中间表**（System/Database/Table/Field）支持UPSERT同步，集团唯一标识生成后不可覆盖
- **字段生成规则引擎**（COPY/CONCAT/ENUM_MAP/FORMULA）自动填充集团规范字段
- **空值保护机制**：同步时检测空值覆盖风险，弹框三选一确认（取消/跳过空值/全部覆盖）
- **中间表稽核**：执行稽核规则，更新audit_status（pending/pass/fail），不合规原因拼接
- **中间表修改**：仅允许修改中间表（不可修改本地元数据），字段级修改日志记录
- **结果表同步**：仅合规记录（audit_status=pass）进入结果表，生成数据快照
- **集团上传**：从结果表推送集团，生成上传批次号，记录上传日志
- **25日截止预警**：本月25日前完成盘点范围内库表上传，页面Banner预警
- **操作日志**：同步/稽核/修改/结果表/上传 全流程操作记录，可查询明细
- 高质量数据集/非结构化/标签/指标/API/产品 6类资产上报（保留原流程）
- 资源类系统 树形+明细 展示（系统→库→表→字段）
- 四种上传模式：独立上传/整体上传/变更上传/下线上传

### 模块五：元数据管理优化 ✅
- 系统状态定时更新（每日凌晨，上线时间对比）
- 增强查询条件（维护单位/定级备案名称/是否合规）
- 集团主数据编码同步（手动录入 + API集成）
- 资产交接能力（原维护人→新接收人，交接日志）

### 模块六：接口安全适配与EOP接入 ✅
- 数据脱敏服务（手机号/邮箱/电话/姓名/身份证）
- 查询频次控制（每日上限，Redis计数器预留）
- EOP网关客户端（重试3次+指数退避+熔断）
- 23个EOP接口清单文档化

### 新增28张数据表清单

| 表名 | 用途 | 所属模块 |
|---|---|---|
| t_dataset_metadata | 高质量数据集元数据信息 | 数据集 |
| t_dataset_quality | 高质量数据集质量数据 | 数据集 |
| t_dataset_catalog | 数据集目录 | 目录 |
| t_meta_field_config | 元模型字段配置 | 元模型 |
| t_upload_resource_system | 资源类-系统上传中间表 | 上报（旧） |
| t_upload_resource_database | 资源类-数据库上传中间表 | 上报（旧） |
| t_upload_resource_table | 资源类-表上传中间表 | 上报（旧） |
| t_upload_resource_field | 资源类-字段上传中间表 | 上报（旧） |
| t_upload_asset_label | 资产类-标签上传中间表 | 上报（旧） |
| t_upload_asset_indicator | 资产类-指标上传中间表 | 上报（旧） |
| t_upload_asset_api | 资产类-API上传中间表 | 上报（旧） |
| t_upload_asset_product | 资产类-产品上传中间表 | 上报（旧） |
| t_upload_multimodal_unstructured | 多模态类-非结构化上传中间表 | 上报（旧） |
| t_upload_multimodal_dataset | 多模态类-高质量数据集上传中间表 | 上报（旧） |
| **t_upload_mid_system** | **资源类-系统中间表（新流程）** | **上报（新）** |
| **t_upload_mid_database** | **资源类-数据库中间表（新流程）** | **上报（新）** |
| **t_upload_mid_table** | **资源类-表中间表（新流程）** | **上报（新）** |
| **t_upload_mid_field** | **资源类-字段中间表（新流程）** | **上报（新）** |
| **t_mid_field_gen_rule** | **中间表字段生成规则** | **上报（新）** |
| **t_metadata_field_mapping** | **本地到中间表字段映射** | **上报（新）** |
| **t_mid_field_modify_log** | **中间表字段修改日志** | **上报（新）** |
| **t_upload_operation_log** | **上传操作日志** | **上报（新）** |
| **t_upload_result_table** | **集团上传中间结果表** | **上报（新）** |
| **t_classify_mid** | **分级分类中间表** | **上报（新）** |
| **t_metadata_complete_task** | **元数据补全任务** | **上报（新）** |
| t_audit_rule | 稽核规则配置表 | 稽核 |
| t_audit_result | 稽核结果表 | 稽核 |
| t_metadata_complete_log | 元数据补全日志 | 补全 |
| t_asset_handover_log | 资产交接日志 | 交接 |
| t_search_count | 查询频次计数（Redis） | 安全 |

## 注意事项

1. 生产环境请修改 `.env` 中的 `secret_key`
2. MySQL需要支持 utf8mb4 字符集
3. 样例数据、AI补全能力需要对接实际大模型服务
4. EOP接入需要配置真实网关地址和密钥
5. 查询频次控制生产环境应切换为Redis存储
6. 系统状态定时任务需配置外部cron或任务调度平台触发
