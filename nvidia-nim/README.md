# NVIDIA NIM Monitoring Plugin for Site24x7

**Custom Plugin** — Monitors NVIDIA NIM inference endpoints via Prometheus metrics.

---

## Overview
This plugin scrapes metrics from the NVIDIA NIM Prometheus exporter (`http://localhost:8000/v1/metrics`) and exposes them through the Site24x7 Custom Plugin interface. It provides four dashboard tabs: **Inference Performance**, **Token Statistics**, **Resource Usage**, and **Runtime**, covering latency, throughput, GPU cache usage, process health, and Python garbage collection stats.

---

## Installation

### Prerequisites
*   Site24x7 Linux Agent installed on the target server.
*   Python 3.x available to the Site24x7 agent process.
*   NVIDIA NIM instance running with the Prometheus exporter enabled on port **8000**.

### Quick Setup
1.  Ensure the NIM Prometheus exporter is accessible: `curl http://localhost:8000/v1/metrics`
2.  Copy the plugin files to the Site24x7 Agent plugin directory:
    ```bash
    mkdir -p /opt/site24x7/monagent/plugins/nvidia-nim
    cp nvidia-nim.py nvidia-nim.cfg /opt/site24x7/monagent/plugins/nvidia-nim/
    ```
3.  Verify the plugin runs correctly:
    ```bash
    python3 /opt/site24x7/monagent/plugins/nvidia-nim/nvidia-nim.py
    ```
    Expected: Valid JSON output with `status: 1` and metric values.
4.  Restart or wait for the Site24x7 agent to auto-detect and execute the plugin (interval: ~5 min).

### Configuration
Edit `nvidia-nim.cfg` if your NIM endpoint differs from the default:
```ini
[global_configurations]
use_agent_python=1

[instance_1]
nim_endpoint=http://localhost:8000/v1/metrics
```
*   `nim_endpoint`: Full URL to the NIM Prometheus metrics endpoint.

---

## Metrics Summary
The plugin maps the following Prometheus metric families to Site24x7 dashboard categories:

| **Category** | **Metric** | **Description** |
|---|---|---|
| **Inference Performance** | `requests_running` | Requests currently running on GPU |
| | `requests_waiting` | Requests waiting in queue |
| | `e2e_latency_avg` | Average end-to-end request latency (s) |
| | `time_to_first_token_avg` | Average TTFT (s) |
| | `time_per_output_token_avg` | Average TPOT (s) |
| **Token Statistics** | `generation_tokens` | Total output tokens processed |
| | `prompt_tokens` | Total input/prompt tokens processed |
| **Resource Usage** | `gpu_cache_usage` | GPU KV-cache usage (fraction, 1.0 = 100%) |
| | `resident_memory` | Process resident memory (bytes) |
| | `cpu_seconds` | Total CPU time consumed (s) |
| **Runtime** | `num_request_max` | Maximum concurrent requests observed |
| | `request_finish_count` | Total finished requests |
| | `process_max_fds` | Max open file descriptors |
| | `process_open_fds` | Current open file descriptors |
| | `process_start_time_seconds` | Process start epoch time |
| | `process_virtual_memory_bytes` | Process virtual memory size (bytes) |
| | `python_gc_collections_count` | Number of GC events |
| | `python_gc_objects_collected_count` | Objects collected by GC |
| | `python_gc_objects_uncollectable_count` | Uncollectable objects found |
| | `python_info` | Python platform information string |

*The plugin calculates derived averages (latency/TPOT) internally by dividing `_sum` by `_count`.*

---

## Verification
After the agent picks up the plugin, navigate in Site24x7 to:
**Server tab → Plugin Integration → List of plugin monitors → NVIDIA NIM Monitor**

You should see four tabs populated with live metric values. If the plugin reports `status: 0`, ensure:
*   The NIM endpoint (`http://localhost:8000/v1/metrics`) is reachable.
*   The `nvidia-nim.cfg` `nim_endpoint` is correct.
*   Python 3 is the interpreter used by the Site24x7 agent.

---

## References
*   NVIDIA NIM Documentation: [docs.nvidia.com/nim](https://docs.nvidia.com/nim)
*   Prometheus NIM Exporter: Standard `/metrics` endpoint on NIM container/pod.
*   Site24x7 Custom Plugin Docs: [site24x7.com](https://www.site24x7.com)