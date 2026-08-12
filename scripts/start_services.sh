#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
RUN_DIR="$PROJECT_ROOT/run"

mkdir -p "$LOG_DIR" "$RUN_DIR"

# ---------- Config ----------
LLM_GPU="${LLM_GPU:-3}"
RAG_GPU="${RAG_GPU:-6}"

LLM_MODEL_NAME="${LLM_MODEL:-qwen2.5-7b-instruct}"
LLM_BASE_URL="${LLM_BASE_URL:-http://127.0.0.1:8000/v1}"
LLM_API_KEY="${LLM_API_KEY:-local}"

# Infer current server cache locations from project location.
USER_DATA_ROOT="$(dirname "$(dirname "$(dirname "$PROJECT_ROOT")")")"
LLM_HF_HOME="${LLM_HF_HOME:-$USER_DATA_ROOT/hf_cache}"
RAG_HF_HOME="${RAG_HF_HOME:-$(dirname "$PROJECT_ROOT")/.cache/huggingface}"

MODEL_CACHE="${MODEL_CACHE:-$LLM_HF_HOME/hub/models--Qwen--Qwen2.5-7B-Instruct-AWQ}"

# ---------- Conda ----------
CONDA_EXE="${CONDA_EXE:-$(command -v conda || true)}"

if [[ -z "$CONDA_EXE" ]]; then
    for candidate in "$HOME/anaconda3/bin/conda" "$HOME/miniconda3/bin/conda"; do
        if [[ -x "$candidate" ]]; then
            CONDA_EXE="$candidate"
            break
        fi
    done
fi

if [[ -z "$CONDA_EXE" || ! -x "$CONDA_EXE" ]]; then
    echo "ERROR: conda not found."
    exit 1
fi

# ---------- Passwords ----------
if [[ -z "${NEO4J_PASSWORD:-}" ]]; then
    read -rsp "NEO4J_PASSWORD: " NEO4J_PASSWORD
    echo
    export NEO4J_PASSWORD
fi

if [[ -z "${MYSQL_PASSWORD:-}" ]]; then
    read -rsp "MYSQL_PASSWORD: " MYSQL_PASSWORD
    echo
    export MYSQL_PASSWORD
fi

echo
echo "Ensure Windows Neo4j and the SSH reverse tunnel are already running."
echo "LLM GPU: $LLM_GPU"
echo "RAG GPU: $RAG_GPU"
echo

# ---------- Helpers ----------
port_open() {
    local port="$1"
    ss -ltn | grep -qE "[:.]${port}[[:space:]]"
}

wait_http() {
    local name="$1"
    local url="$2"
    local timeout="${3:-120}"

    echo "Waiting for $name ..."

    for ((i=1; i<=timeout; i++)); do
        if curl -s --max-time 2 -o /dev/null "$url"; then
            echo "$name is ready."
            return 0
        fi
        sleep 1
    done

    echo "ERROR: $name did not become ready in ${timeout}s."
    return 1
}

save_pid() {
    echo "$2" > "$RUN_DIR/$1.pid"
}

# ---------- 1. vLLM ----------
if port_open 8000; then
    echo "vLLM :8000 is already running."
else
    if [[ ! -f "$MODEL_CACHE/refs/main" ]]; then
        echo "ERROR: Qwen model cache not found:"
        echo "$MODEL_CACHE"
        exit 1
    fi

    REV="$(cat "$MODEL_CACHE/refs/main")"
    MODEL="$MODEL_CACHE/snapshots/$REV"

    echo "Starting Qwen/vLLM ..."

    setsid "$CONDA_EXE" run --no-capture-output -n pesticide-llm \
        env \
        CUDA_VISIBLE_DEVICES="$LLM_GPU" \
        HF_HOME="$LLM_HF_HOME" \
        HF_HUB_OFFLINE=1 \
        TRANSFORMERS_OFFLINE=1 \
        vllm serve "$MODEL" \
        --served-model-name "$LLM_MODEL_NAME" \
        --host 127.0.0.1 \
        --port 8000 \
        --gpu-memory-utilization 0.65 \
        --max-model-len 4096 \
        --max-num-seqs 2 \
        --enable-auto-tool-choice \
        --tool-call-parser hermes \
        > "$LOG_DIR/vllm.log" 2>&1 < /dev/null &

    save_pid vllm "$!"

    if ! wait_http "vLLM" "http://127.0.0.1:8000/v1/models" 180; then
        echo "See: $LOG_DIR/vllm.log"
        exit 1
    fi
fi

# ---------- 2. FastAPI Agent ----------
if port_open 8001; then
    echo "FastAPI Agent :8001 is already running."
else
    echo "Starting FastAPI Agent ..."

    setsid "$CONDA_EXE" run --no-capture-output -n pesticide-rag \
        env \
        CUDA_VISIBLE_DEVICES="$RAG_GPU" \
        HF_HOME="$RAG_HF_HOME" \
        HF_HUB_OFFLINE=1 \
        LLM_BASE_URL="$LLM_BASE_URL" \
        LLM_API_KEY="$LLM_API_KEY" \
        LLM_MODEL="$LLM_MODEL_NAME" \
        NEO4J_PASSWORD="$NEO4J_PASSWORD" \
        uvicorn app.main:app \
        --app-dir "$PROJECT_ROOT/rag-agent-service" \
        --host 127.0.0.1 \
        --port 8001 \
        > "$LOG_DIR/agent-api.log" 2>&1 < /dev/null &

    save_pid agent-api "$!"

    if ! wait_http "FastAPI Agent" "http://127.0.0.1:8001/health" 120; then
        echo "See: $LOG_DIR/agent-api.log"
        exit 1
    fi
fi

# ---------- 3. Spring Boot ----------
if port_open 4399; then
    echo "Spring Boot :4399 is already running."
else
    echo "Starting Spring Boot ..."

    setsid "$CONDA_EXE" run --no-capture-output -n pesticide-rag \
        env \
        NEO4J_PASSWORD="$NEO4J_PASSWORD" \
        MYSQL_PASSWORD="$MYSQL_PASSWORD" \
        AGENT_API_BASE_URL="http://127.0.0.1:8001" \
        mvn -f "$PROJECT_ROOT/pom.xml" spring-boot:run \
        > "$LOG_DIR/spring-boot.log" 2>&1 < /dev/null &

    save_pid spring-boot "$!"

    if ! wait_http "Spring Boot" "http://127.0.0.1:4399/" 120; then
        echo "See: $LOG_DIR/spring-boot.log"
        exit 1
    fi
fi

echo
echo "========================================"
echo "All server-side services are ready."
echo
echo "vLLM:       http://127.0.0.1:8000"
echo "Agent API:  http://127.0.0.1:8001"
echo "Web App:    http://127.0.0.1:4399"
echo "Agent Demo: http://127.0.0.1:4399/agent.html"
echo "========================================"
