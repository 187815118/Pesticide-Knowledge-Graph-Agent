#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$PROJECT_ROOT/run"

stop_service() {
    local name="$1"
    local pid_file="$RUN_DIR/$name.pid"

    if [[ ! -f "$pid_file" ]]; then
        echo "$name: no PID file, skip."
        return
    fi

    local pid
    pid="$(cat "$pid_file")"

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "$name: process already stopped."
        rm -f "$pid_file"
        return
    fi

    echo "Stopping $name (PID $pid) ..."

    # Services are started with setsid, so terminate only their process group.
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true

    for _ in {1..15}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "$name stopped."
            rm -f "$pid_file"
            return
        fi
        sleep 1
    done

    echo "$name did not stop gracefully; forcing shutdown."
    kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    rm -f "$pid_file"
}

# Stop consumers before the LLM backend.
stop_service spring-boot
stop_service agent-api
stop_service vllm

echo "Server-side services stopped."
