# data-analysis-agent (基于 LangGraph + Docker 沙盒)
一个数据分析agent，根据数据生成对应python代码进行分析、修改，能运行代码，并返回结果，返回文件

## 简介
这是一个基于 **LangGraph** 和 **OpenAI 大模型** 的数据分析智能 Agent。  
它可以自动读取用户上传的数据文件（CSV、Excel、JSON），生成 Python 分析代码，并在隔离的 **Docker 沙盒** 中安全运行，最后返回：
- 描述性统计结果（CSV）
- 可视化图表（PNG）
- 执行的 Python 代码文件

整个流程完全自动化，无需用户编写代码，只需上传数据并指定分析任务即可。


## 项目结构

data-analysis-agent/
├─ README.md                # 使用说明
├─ .env.example             # 环境变量模板
├─ docker-compose.yml       # 一键启动沙盒服务
├─ uploads/                 # 用户上传的数据文件目录
├─ outputs/                 # 执行结果输出目录
├─ agent/                   # 主 Agent 代码
│  ├─ requirements.txt
│  ├─ run_agent.py          # 启动入口
│  ├─ config.py             # 全局配置
│  ├─ graph/                # LangGraph 流程定义
│  │  ├─ state.py
│  │  └─ build.py
│  ├─ nodes/                # 各种节点逻辑
│  │  ├─ prepare.py
│  │  ├─ collect_results.py
│  │  └─ finalize.py
│  └─ tools/                # 工具定义
│     └─ sandbox_tool.py
└─ sandbox/                 # Docker 沙盒服务
   ├─ Dockerfile
   └─ sandbox_app.py

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone <your-repo-url> data-analysis-agent
cd data-analysis-agent

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r agent/requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
cp .env.example .env
```

配置内容：

```env
OPENAI_API_KEY=替换为你的OpenAI Key
SANDBOX_URL=http://localhost:5000/run
OUTPUT_DIR=outputs
UPLOADS_DIR=uploads
```

### 3. 启动 Docker 沙盒

```bash
docker compose up -d sandbox
```

这会启动一个 Flask 服务，监听 `http://localhost:5000/run`，并在容器内执行 Python 代码。容器挂载了 `uploads/` 到 `/app/data/`（只读）。

### 4. 准备数据

将 CSV/Excel/JSON 文件放入 `uploads/`，例如：

```
uploads/sample.csv
```

### 5. 运行 Agent

```bash
python agent/run_agent.py --file uploads/sample.csv --task "统计描述、可视化"
```

### 6. 查看结果

* **outputs/analysis\_code.py**：生成的 Python 代码
* **outputs/result.csv**：描述性统计结果
* **outputs/plot\_1.png**、`plot_2.png`：可视化图表
* 控制台输出：LLM 的最终总结说明

---

## 开发说明

* **Agent**：基于 LangGraph 实现，节点划分为 `prepare` → `agent` → `tools` → `collect` → `finalize`。
* **Tool**：`sandbox_tool.py` 定义了调用 Docker 沙盒 API 的工具函数。
* **Sandbox**：`sandbox_app.py` 使用 Flask 提供 `/run` 接口，接收 Python 代码并执行，返回 stdout/stderr、图像和 CSV。

---

## 注意事项

* 运行沙盒前，请确保 **Docker Desktop** 已启动。
* 上传的数据文件只能通过容器内路径 `/app/data/<文件名>` 访问。
* 代码执行被限制在容器中，防止访问外部网络和非挂载目录。
* 若需要扩展功能，可以修改 `agent/nodes/prepare.py` 来定义额外的分析逻辑。

---

## 示例

假设上传 `sample.csv`（包含一列 `age`），运行：

```bash
python agent/run_agent.py --file uploads/sample.csv --task "统计描述、可视化"
```

将会得到：

* `result.csv`：包含平均值、方差、最小值、最大值等
* `plot_1.png`：年龄分布直方图
* 控制台输出：数据集的基本统计结论