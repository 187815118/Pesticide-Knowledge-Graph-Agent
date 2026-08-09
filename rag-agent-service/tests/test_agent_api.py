import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.main as app_main


def main() -> int:
    original_run_agent = app_main.run_agent
    client = TestClient(app_main.app)

    def fake_run_agent(question):
        return {
            "answer": "Sparta's active substance is spinetoram. [D1]",
            "tool_trace": [
                {
                    "tool": "query_active_substance",
                    "arguments": {"pesticide_name": "Sparta"},
                    "result": ["spinetoram"],
                }
            ],
            "execution_state": {
                "user_question": question,
                "observations": [
                    {
                        "tool": "query_active_substance",
                        "arguments": {"pesticide_name": "Sparta"},
                        "result": ["spinetoram"],
                    }
                ],
            },
        }

    try:
        app_main.run_agent = fake_run_agent
        response = client.post(
            "/agent/query",
            json={"question": "  What is the active substance of Sparta?  "},
        )
        if response.status_code != 200:
            raise AssertionError(f"正常请求应返回 200，实际: {response.status_code}")
        body = response.json()
        if body["question"] != "What is the active substance of Sparta?":
            raise AssertionError("question 应去除首尾空格")
        if body["answer"] != "Sparta's active substance is spinetoram. [D1]":
            raise AssertionError("answer 未正确返回")
        if body["tool_trace"][0]["tool"] != "query_active_substance":
            raise AssertionError("tool_trace 未正确返回")
        if body["execution_state"]["observations"][0]["result"] != ["spinetoram"]:
            raise AssertionError("execution_state 未正确返回")

        empty_response = client.post("/agent/query", json={"question": "   "})
        if empty_response.status_code not in {400, 422}:
            raise AssertionError("空 question 应被 400 或 422 拒绝")

        def failing_run_agent(question):
            raise RuntimeError("backend unavailable")

        app_main.run_agent = failing_run_agent
        error_response = client.post(
            "/agent/query",
            json={"question": "What is the active substance of Sparta?"},
        )
        if error_response.status_code != 500:
            raise AssertionError("run_agent 异常应返回 HTTP 500")
        if "Agent 查询失败" not in error_response.json().get("detail", ""):
            raise AssertionError("500 detail 应包含简洁 Agent 错误信息")
    finally:
        app_main.run_agent = original_run_agent

    print("验收通过: Agent API 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
