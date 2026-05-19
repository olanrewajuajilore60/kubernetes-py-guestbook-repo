from typing import Sequence

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_kubernetes.core.v1 import Service

from frontend_monitoring import create_frontend_service_monitor
from grafana import create_grafana_external_service, create_guestbook_dashboard
from ingress import (
    create_guestbook_ingress,
    create_guestbook_ingress_external_service,
    create_ingress_namespace,
    create_ingress_nginx,
)
from monitoring import create_kube_prometheus_stack, create_monitoring_namespace
from outputs import load_balancer_url
from service_monitor import ServiceMonitor
from storage import MonitoringStorage, grafana_persistence_values, prometheus_storage_spec


class ObservabilityStack(ComponentResource):
    namespace: str
    ingress_namespace: str
    grafana_admin_user: str
    grafana_admin_password: Output[str]
    grafana_service: Service
    grafana_url: Output[str]
    grafana_node_port: Output[str]
    guestbook_ingress_service: Service
    guestbook_ingress_url: Output[str]
    guestbook_ingress_node_port: Output[str]

    def __init__(
        self,
        name: str,
        app_namespace: str,
        monitored_apps: Sequence[str],
        grafana_service_type: str,
        ingress_service_type: str,
        grafana_admin_user: str,
        grafana_admin_password: Output[str],
        opts: ResourceOptions = None,
    ):
        super().__init__("guestbook:component:ObservabilityStack", name, {}, opts)

        self.namespace = "monitoring"
        self.ingress_namespace = "ingress-nginx"
        self.grafana_admin_user = grafana_admin_user
        self.grafana_admin_password = grafana_admin_password

        monitoring_namespace = create_monitoring_namespace(
            self.namespace,
            ResourceOptions(parent=self),
        )
        ingress_namespace = create_ingress_namespace(
            self.ingress_namespace,
            ResourceOptions(parent=self),
        )
        storage = MonitoringStorage(
            "monitoring-storage",
            self.namespace,
            ResourceOptions(parent=self, depends_on=[monitoring_namespace]),
        )
        monitoring = create_kube_prometheus_stack(
            self.namespace,
            grafana_admin_user,
            grafana_admin_password,
            prometheus_storage_spec(),
            grafana_persistence_values(),
            ResourceOptions(parent=self, depends_on=[monitoring_namespace, storage]),
        )
        ingress_nginx = create_ingress_nginx(
            self.ingress_namespace,
            ResourceOptions(parent=self, depends_on=[monitoring, ingress_namespace]),
        )

        ServiceMonitor(
            "guestbook-redis-exporters",
            monitor_namespace=self.namespace,
            app_namespace=app_namespace,
            app_names=monitored_apps,
            service_port_name="metrics",
            opts=ResourceOptions(parent=self, depends_on=[monitoring]),
        )
        create_frontend_service_monitor(
            self.namespace,
            app_namespace,
            ResourceOptions(parent=self, depends_on=[monitoring]),
        )
        create_guestbook_ingress(
            app_namespace,
            ResourceOptions(parent=self, depends_on=[ingress_nginx]),
        )
        create_guestbook_dashboard(
            self.namespace,
            app_namespace,
            ResourceOptions(parent=self, depends_on=[monitoring]),
        )

        service_type = grafana_service_type or "LoadBalancer"
        self.grafana_service = create_grafana_external_service(
            self.namespace,
            service_type,
            ResourceOptions(parent=self, depends_on=[monitoring]),
        )

        ingress_type = ingress_service_type or "LoadBalancer"
        self.guestbook_ingress_service = create_guestbook_ingress_external_service(
            self.ingress_namespace,
            ingress_type,
            ResourceOptions(parent=self, depends_on=[ingress_nginx]),
        )

        self.grafana_node_port = self.grafana_service.spec.apply(
            lambda spec: str(spec.ports[0].node_port)
            if spec and spec.ports and spec.ports[0].node_port
            else ""
        )
        if service_type == "NodePort":
            self.grafana_url = self.grafana_node_port.apply(
                lambda port: f"http://localhost:{port}" if port else ""
            )
        else:
            self.grafana_url = self.grafana_service.status.apply(load_balancer_url)

        self.guestbook_ingress_node_port = self.guestbook_ingress_service.spec.apply(
            lambda spec: str(spec.ports[0].node_port)
            if spec and spec.ports and spec.ports[0].node_port
            else ""
        )
        if ingress_type == "NodePort":
            self.guestbook_ingress_url = self.guestbook_ingress_node_port.apply(
                lambda port: f"http://localhost:{port}" if port else ""
            )
        else:
            self.guestbook_ingress_url = self.guestbook_ingress_service.status.apply(
                load_balancer_url
            )

        self.register_outputs(
            {
                "namespace": self.namespace,
                "ingress_namespace": self.ingress_namespace,
                "grafana_url": self.grafana_url,
                "grafana_node_port": self.grafana_node_port,
                "guestbook_ingress_url": self.guestbook_ingress_url,
                "guestbook_ingress_node_port": self.guestbook_ingress_node_port,
            }
        )
