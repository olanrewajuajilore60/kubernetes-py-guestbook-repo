from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import ContainerArgs, ContainerPortArgs

from service_monitor import ServiceMonitor

FRONTEND_METRICS_PORT = 9115
FRONTEND_METRICS_PORT_NAME = "frontend-metrics"


def frontend_exporter() -> ContainerArgs:
    return ContainerArgs(
        name="frontend-blackbox-exporter",
        image="prom/blackbox-exporter:v0.25.0",
        ports=[
            ContainerPortArgs(
                name=FRONTEND_METRICS_PORT_NAME,
                container_port=FRONTEND_METRICS_PORT,
            )
        ],
    )


def frontend_service_annotations() -> dict:
    return {
        "prometheus.io/scrape": "true",
        "prometheus.io/port": str(FRONTEND_METRICS_PORT),
        "prometheus.io/path": "/metrics",
    }


def create_frontend_service_monitor(
    monitor_namespace: str,
    app_namespace: str,
    opts: ResourceOptions,
) -> ServiceMonitor:
    return ServiceMonitor(
        "guestbook-frontend",
        monitor_namespace=monitor_namespace,
        app_namespace=app_namespace,
        app_names=["frontend"],
        service_port_name=FRONTEND_METRICS_PORT_NAME,
        path="/probe",
        params={
            "module": ["http_2xx"],
            "target": ["http://localhost:80"],
        },
        opts=opts,
    )
