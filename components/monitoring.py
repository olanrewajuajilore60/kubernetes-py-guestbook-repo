from pulumi import Output, ResourceOptions
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs


def create_monitoring_namespace(
    namespace: str,
    opts: ResourceOptions,
) -> Namespace:
    return Namespace(
        namespace,
        metadata=ObjectMetaArgs(name=namespace),
        opts=opts,
    )


def create_kube_prometheus_stack(
    namespace: str,
    grafana_admin_user: str,
    grafana_admin_password: Output[str],
    prometheus_storage_spec: dict,
    grafana_persistence: dict,
    opts: ResourceOptions,
) -> Release:
    return Release(
        "monitoring",
        ReleaseArgs(
            chart="kube-prometheus-stack",
            namespace=namespace,
            repository_opts=RepositoryOptsArgs(
                repo="https://prometheus-community.github.io/helm-charts",
            ),
            values={
                "grafana": {
                    "adminUser": grafana_admin_user,
                    "adminPassword": grafana_admin_password,
                    "service": {
                        "type": "ClusterIP",
                    },
                    "persistence": grafana_persistence,
                    "sidecar": {
                        "dashboards": {
                            "enabled": True,
                            "label": "grafana_dashboard",
                            "labelValue": "1",
                            "searchNamespace": "ALL",
                        },
                    },
                },
                "prometheus": {
                    "prometheusSpec": {
                        "serviceMonitorSelectorNilUsesHelmValues": False,
                        "serviceMonitorNamespaceSelector": {},
                        "podMonitorSelectorNilUsesHelmValues": False,
                        "probeSelectorNilUsesHelmValues": False,
                        "storageSpec": prometheus_storage_spec,
                    },
                },
            },
        ),
        opts=opts,
    )
