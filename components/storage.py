from pulumi import ComponentResource, ResourceOptions
from pulumi_kubernetes.core.v1 import PersistentVolume, PersistentVolumeClaim

from grafana_storage import (
    create_grafana_persistent_volume,
    create_grafana_persistent_volume_claim,
    grafana_persistence_values,
)
from prometheus_storage import (
    create_prometheus_persistent_volume,
    prometheus_storage_spec,
)


class MonitoringStorage(ComponentResource):
    prometheus_pv: PersistentVolume
    grafana_pv: PersistentVolume
    grafana_pvc: PersistentVolumeClaim

    def __init__(
        self,
        name: str,
        namespace: str,
        opts: ResourceOptions = None,
    ):
        super().__init__("guestbook:component:MonitoringStorage", name, {}, opts)

        self.prometheus_pv = create_prometheus_persistent_volume(
            ResourceOptions(parent=self),
        )
        self.grafana_pv = create_grafana_persistent_volume(
            ResourceOptions(parent=self),
        )
        self.grafana_pvc = create_grafana_persistent_volume_claim(
            namespace,
            self.grafana_pv,
            ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "prometheus_pv": self.prometheus_pv,
                "grafana_pv": self.grafana_pv,
                "grafana_pvc": self.grafana_pvc,
            }
        )
