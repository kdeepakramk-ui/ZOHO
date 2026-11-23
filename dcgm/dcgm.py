#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import os
import sys
from typing import Any, Dict, List, Optional

# Mandatory Site24x7 Plugin Constants
PLUGIN_VERSION = 2
HEARTBEAT = "true"

# Metric units for individual categories (Tabular data)
PERF_UNITS = {
    "GPU_Utilization": "%",
    "Memory_Copy_Utilization": "%",
    "SM_Clock": "MHz",
    "Memory_Clock": "MHz",
    "Encoder_Utilization": "%",
    "Decoder_Utilization": "%",
    "SM_Active": "fraction",
    "SM_Occupancy": "fraction",
    "Tensor_Active": "fraction",
    "FP16_Active": "fraction",
    "FP32_Active": "fraction",
    "FP64_Active": "fraction",
    "PCIe_TX_Throughput": "KB/s",
    "PCIe_RX_Throughput": "KB/s"
}

RESOURCE_UNITS = {
    "Memory_Used": "MB",
    "Memory_Free": "MB",
    "Memory_Total": "MB",
    "Framebuffer_Utilization": "%"
}

HEALTH_UNITS = {
    "Temperature": "C",
    "Memory_Temperature": "C",
    "Power_Usage": "W",
    "Fan_Speed": "%",
    "Energy_Consumption": "mJ",
    "Clock_Throttle_Reasons": "bitmask",
    "Correctable_Remapped_Rows": "count",
    "Uncorrectable_Remapped_Rows": "count",
    "XID_Errors": "count",
    "PState": "state",
    "Slowdown_Temperature": "C"
}

# Global units registry
METRIC_UNITS = {
    "GPU_Performance_Metrics": PERF_UNITS,
    "GPU_Resource_Metrics": RESOURCE_UNITS,
    "GPU_Health_Metrics": HEALTH_UNITS,
    "Average_GPU_Utilization": "%",
    "Average_Memory_Utilization": "%",
    "Average_Temperature": "C",
    "Total_Power_Draw": "W"
}

# Dashboard Tab Configuration
TABS = {
    "Performance": {
        "order": 1,
        "tablist": [
            "Average_GPU_Utilization",
            "Average_Memory_Utilization",
            "GPU_Performance_Metrics"
        ]
    },
    "Resources": {
        "order": 2,
        "tablist": [
            "GPU_Device_Count",
            "GPU_Resource_Metrics"
        ]
    },
    "Health": {
        "order": 3,
        "tablist": [
            "Average_Temperature",
            "Total_Power_Draw",
            "GPU_Health_Metrics"
        ]
    }
}

class Plugin:
    def __init__(self):
        self.data = {}
        self.data["plugin_version"] = PLUGIN_VERSION
        self.data["heartbeat_required"] = HEARTBEAT
        self.data["units"] = METRIC_UNITS
        self.data["tabs"] = TABS
        self.data["Name"] = "NVIDIA_DCGM_Monitor"

    def getData(self) -> Dict[str, Any]:
        try:
            # Fetch metrics from DCGM Prometheus exporter
            response = urllib.request.urlopen('http://localhost:9400/metrics', timeout=10)
            content = response.read().decode('utf-8')

            # Parse metrics per GPU
            gpu_data = self._parse_multi_gpu_metrics(content)

            if not gpu_data:
                self.data["status"] = 0
                self.data["msg"] = "No GPU metrics found in exporter output"
                return self.data

            # Build Site24x7 Tabular lists
            perf_list = []
            resource_list = []
            health_list = []

            gpu_utils = []
            mem_utils = []
            temps = []
            powers = []

            for gpu_id, m in gpu_data.items():
                gpu_name = f"GPU {gpu_id}"

                # Performance Tab
                perf_list.append({
                    "name": gpu_name,
                    "GPU_Utilization": m.get("gpu_util", 0),
                    "Memory_Copy_Utilization": m.get("mem_util", 0),
                    "SM_Clock": m.get("sm_clock", 0),
                    "Memory_Clock": m.get("mem_clock", 0),
                    "Encoder_Utilization": m.get("enc_util", 0),
                    "Decoder_Utilization": m.get("dec_util", 0),
                    "SM_Active": m.get("sm_active", 0),
                    "SM_Occupancy": m.get("sm_occupancy", 0),
                    "Tensor_Active": m.get("tensor_active", 0),
                    "FP16_Active": m.get("fp16_active", 0),
                    "FP32_Active": m.get("fp32_active", 0),
                    "FP64_Active": m.get("fp64_active", 0),
                    "PCIe_TX_Throughput": m.get("pcie_tx", 0),
                    "PCIe_RX_Throughput": m.get("pcie_rx", 0)
                })

                # Resource Tab
                fb_used = m.get("fb_used", 0)
                fb_total = m.get("fb_total", 0)
                resource_list.append({
                    "name": gpu_name,
                    "Memory_Used": fb_used,
                    "Memory_Free": m.get("fb_free", 0),
                    "Memory_Total": fb_total,
                    "Framebuffer_Utilization": round((fb_used / fb_total * 100), 2) if fb_total > 0 else 0
                })

                # Health Tab
                health_list.append({
                    "name": gpu_name,
                    "Temperature": m.get("temp", 0),
                    "Memory_Temperature": m.get("mem_temp", 0),
                    "Power_Usage": m.get("power", 0),
                    "Fan_Speed": m.get("fan", 0),
                    "Energy_Consumption": m.get("energy", 0),
                    "Clock_Throttle_Reasons": m.get("clock_throttle", 0),
                    "Correctable_Remapped_Rows": m.get("corr_remap", 0),
                    "Uncorrectable_Remapped_Rows": m.get("uncorr_remap", 0),
                    "XID_Errors": m.get("xid_errors", 0),
                    "PState": m.get("pstate", 0),
                    "Slowdown_Temperature": m.get("slowdown_temp", 0)
                })

                # Collect values for aggregates
                gpu_utils.append(m.get("gpu_util", 0))
                mem_utils.append(m.get("mem_util", 0))
                temps.append(m.get("temp", 0))
                powers.append(m.get("power", 0))

            # Populate top-level aggregate metrics
            self.data["GPU_Device_Count"] = len(gpu_data)
            self.data["Average_GPU_Utilization"] = round(sum(gpu_utils) / len(gpu_utils), 2)
            self.data["Average_Memory_Utilization"] = round(sum(mem_utils) / len(mem_utils), 2)
            self.data["Average_Temperature"] = round(sum(temps) / len(temps), 2)
            self.data["Total_Power_Draw"] = round(sum(powers), 2)

            # Assign tabular data
            self.data["GPU_Performance_Metrics"] = perf_list
            self.data["GPU_Resource_Metrics"] = resource_list
            self.data["GPU_Health_Metrics"] = health_list

            self.data["status"] = 1
            self.data["msg"] = "Success"

        except Exception as e:
            self.data["status"] = 0
            self.data["msg"] = str(e)
            # Remove tabs on error so Site24x7 shows the error message prominently
            self.data.pop("tabs", None)

        return self.data

    def _parse_multi_gpu_metrics(self, content: str) -> Dict[str, Dict[str, float]]:
        """
        Parses Prometheus output and groups metrics by GPU ID.
        Returns: { "0": { "gpu_util": 45, ... }, "1": { ... } }
        """
        gpu_map = {}

        # Field ID to internal key mapping
        mapping = {
            "DCGM_FI_DEV_GPU_UTIL": "gpu_util",
            "DCGM_FI_DEV_MEM_COPY_UTIL": "mem_util",
            "DCGM_FI_DEV_ENC_UTIL": "enc_util",
            "DCGM_FI_DEV_DEC_UTIL": "dec_util",
            "DCGM_FI_DEV_POWER_USAGE": "power",
            "DCGM_FI_DEV_GPU_TEMP": "temp",
            "DCGM_FI_DEV_MEM_TEMP": "mem_temp",
            "DCGM_FI_DEV_SM_CLOCK": "sm_clock",
            "DCGM_FI_DEV_MEM_CLOCK": "mem_clock",
            "DCGM_FI_DEV_FB_USED": "fb_used",
            "DCGM_FI_DEV_FB_FREE": "fb_free",
            "DCGM_FI_DEV_FB_TOTAL": "fb_total",
            "DCGM_FI_DEV_FAN_SPEED": "fan",
            "DCGM_FI_DEV_ENERGY_CONSUMPTION": "energy",
            "DCGM_FI_DEV_SM_ACTIVE": "sm_active",
            "DCGM_FI_DEV_SM_OCCUPANCY": "sm_occupancy",
            "DCGM_FI_DEV_TENSOR_ACTIVE": "tensor_active",
            "DCGM_FI_DEV_PIPE_FP64_ACTIVE": "fp64_active",
            "DCGM_FI_DEV_PIPE_FP32_ACTIVE": "fp32_active",
            "DCGM_FI_DEV_PIPE_FP16_ACTIVE": "fp16_active",
            "DCGM_FI_DEV_PCIE_TX_THROUGHPUT": "pcie_tx",
            "DCGM_FI_DEV_PCIE_RX_THROUGHPUT": "pcie_rx",
            "DCGM_FI_DEV_CLOCK_THROTTLE_REASONS": "clock_throttle",
            "DCGM_FI_DEV_CORRECTABLE_REMAP_ROWS": "corr_remap",
            "DCGM_FI_DEV_UNCORRECTABLE_REMAP_ROWS": "uncorr_remap",
            "DCGM_FI_DEV_XID_ERRORS": "xid_errors",
            "DCGM_FI_DEV_PSTATE": "pstate",
            "DCGM_FI_DEV_SLOWDOWN_TEMP": "slowdown_temp",
            "DCGM_FI_DEV_FB_RESERVED": "fb_reserved"
        }

        for line in content.splitlines():
            if line.startswith('#') or not line.strip():
                continue

            try:
                # Format: metric_name{labels} value
                parts = line.rsplit(' ', 1)
                if len(parts) != 2:
                    continue

                raw_metric, value_str = parts
                value = float(value_str)

                # Extract metric name and labels
                metric_name = raw_metric.split('{')[0]

                if metric_name not in mapping:
                    continue

                # Extract GPU ID from labels: {gpu="0",...}
                gpu_id = "0" # Default
                if '{' in raw_metric:
                    labels_part = raw_metric.split('{')[1].split('}')[0]
                    for label in labels_part.split(','):
                        if label.startswith('gpu="'):
                            gpu_id = label.split('"')[1]
                            break

                if gpu_id not in gpu_map:
                    gpu_map[gpu_id] = {}

                gpu_map[gpu_id][mapping[metric_name]] = value

            except (ValueError, IndexError):
                continue

        return gpu_map

if __name__ == '__main__':
    plugin = Plugin()
    data = plugin.getData()
    # Print clean JSON for Site24x7 agent
    print(json.dumps(data))
