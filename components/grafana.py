from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import ConfigMap, Service, ServicePortArgs, ServiceSpecArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

from dashboards import guestbook_dashboard_json


def create_guestbook_dashboard(
    namespace: str,
    app_namespace: str,
    opts: ResourceOptions,
) -> ConfigMap:
    return ConfigMap(
        "guestbook-grafana-dashboard",
        metadata=ObjectMetaArgs(
            name="guestbook-dashboard",
            namespace=namespace,
            labels={
                "grafana_dashboard": "1",
            },
        ),
        data={
            "guestbook-dashboard.json": guestbook_dashboard_json(app_namespace),
        },
        opts=opts,
    )


def create_grafana_external_service(
    namespace: str,
    service_type: str,
    opts: ResourceOptions,
) -> Service:
    return Service(
        "grafana-external",
        metadata=ObjectMetaArgs(
            name="grafana-external",
            namespace=namespace,
            labels={
                "app.kubernetes.io/name": "grafana",
                "app.kubernetes.io/instance": "monitoring",
            },
        ),
        spec=ServiceSpecArgs(
            type=service_type,
            selector={
                "app.kubernetes.io/name": "grafana",
                "app.kubernetes.io/instance": "monitoring",
            },
            ports=[
                ServicePortArgs(
                    name="http",
                    port=80,
                    target_port=3000,
                )
            ],
        ),
        opts=opts,
    )
