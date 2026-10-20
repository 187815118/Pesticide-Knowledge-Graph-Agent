# 演示图片与回放来源

演示使用原项目 `src/main/resources/static/agent.html`，通过 `scripts/serve_recorded_demo.py` 回放仓库已保存的输出。

| 示例 | 原评测案例 | 图片 |
|---|---|---|
| 商品名查询活性成分 | `aq001` | 可在页面点击第一个示例 |
| abamectin 作用机制 / IRAC 类别 | `aq006` | `../images/demo-rag.png` |
| Sparta 活性成分 → RAG 作用机制 | `aq012` | `../images/demo-multistep.png` |

原始记录：`rag-agent-service/evaluation/results/agent_eval_frozen_v3.json`，数据集版本 `frozen-agent-v3`。提取时基准提交为 `b1200b13a85746fb7948b4a6db695dc7490e4d63`。

`recorded-responses.json` 逐字保留所选案例的回答、工具名称、参数与结果，省略了截图不需要的任务标识、时延和冗余运行状态。回放不修改模型回答的措辞和科学表述，因此也保留原输出的局限。

```bash
python scripts/serve_recorded_demo.py
```

打开 <http://127.0.0.1:8765/agent.html>。服务使用 Python 标准库，仅监听本机；只对三个固定问题返回记录，不调用 LLM、Neo4j、MySQL，也不持久化提交的问题。

截图顶部标有“历史评测回放”，以区别于完整系统的实时运行。除了该标识和将第二个示例替换为冻结题集中的确切问题，页面使用原始 Agent UI。

截图于 2026-10-20 获取。入口图见 `../images/demo-start.png`；完整的多步图同时包含 Final Answer、Agent Execution Trace 和 Evidence / Sources。
