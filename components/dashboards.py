import json


def guestbook_dashboard_json(namespace: str) -> str:
    return json.dumps(
        guestbook_dashboard(namespace),
        separators=(",", ":"),
    )


def guestbook_dashboard(namespace: str) -> dict:
    return {
        "uid": "guestbook-overview",
        "title": "Guestbook Overview",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "30s",
        "time": {
            "from": "now-1h",
            "to": "now",
        },
        "panels": [
            graph_panel(
                1,
                "Frontend Request Rate",
                0,
                0,
                12,
                8,
                'sum(rate(nginx_ingress_controller_requests{ingress="guestbook-frontend"}[5m])) by (status)',
                "Requests per second by HTTP status",
            ),
            graph_panel(
                2,
                "Frontend Error Rate",
                12,
                0,
                12,
                8,
                'sum(rate(nginx_ingress_controller_requests{ingress="guestbook-frontend",status=~"4..|5.."}[5m])) by (status)',
                "Error responses per second",
            ),
            graph_panel(
                3,
                "Frontend Direct Probe Success",
                0,
                8,
                12,
                8,
                'probe_success{service="frontend"}',
                "Blackbox probe success by frontend pod",
            ),
            graph_panel(
                4,
                "Frontend Direct Probe Latency",
                12,
                8,
                12,
                8,
                'probe_duration_seconds{service="frontend"}',
                "Blackbox probe duration seconds",
            ),
            graph_panel(
                5,
                "Frontend CPU",
                0,
                16,
                12,
                8,
                f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod=~"frontend-.*",container!="",container!="POD"}}[5m])) by (pod)',
                "Pod CPU usage in cores",
            ),
            graph_panel(
                6,
                "Frontend Memory",
                12,
                16,
                12,
                8,
                f'container_memory_working_set_bytes{{namespace="{namespace}",pod=~"frontend-.*",container!="",container!="POD"}}',
                "Pod memory working set bytes",
            ),
            graph_panel(
                7,
                "Redis Commands",
                0,
                24,
                12,
                8,
                "sum(rate(redis_commands_processed_total[5m])) by (service)",
                "Redis command rate from redis_exporter",
            ),
            graph_panel(
                8,
                "Redis Connected Clients",
                12,
                24,
                12,
                8,
                "redis_connected_clients",
                "Connected Redis clients",
            ),
            graph_panel(
                9,
                "Pod Restarts",
                0,
                32,
                12,
                8,
                f'kube_pod_container_status_restarts_total{{namespace="{namespace}",pod=~"frontend-.*|redis-.*"}}',
                "Container restart count",
            ),
            graph_panel(
                10,
                "Frontend Network Receive",
                12,
                32,
                12,
                8,
                f'sum(rate(container_network_receive_bytes_total{{namespace="{namespace}",pod=~"frontend-.*"}}[5m])) by (pod)',
                "Network receive rate in bytes per second",
            ),
        ],
    }


def graph_panel(
    panel_id: int,
    title: str,
    x: int,
    y: int,
    width: int,
    height: int,
    expr: str,
    legend: str,
) -> dict:
    return {
        "id": panel_id,
        "type": "timeseries",
        "title": title,
        "gridPos": {
            "x": x,
            "y": y,
            "w": width,
            "h": height,
        },
        "targets": [
            {
                "expr": expr,
                "legendFormat": legend,
                "refId": "A",
            }
        ],
    }
