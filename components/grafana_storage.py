from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import PersistentVolume, PersistentVolumeClaim

GRAFANA_STORAGE_CLASS = "guestbook-grafana-static"
GRAFANA_STORAGE_LABELS = {
    "app.kubernetes.io/name": "guestbook-grafana-storage",
}
GRAFANA_STORAGE_SIZE = "10Gi"
GRAFANA_CLAIM_NAME = "grafana-storage"


def create_grafana_persistent_volume(opts: ResourceOptions) -> PersistentVolume:
    return PersistentVolume(
        "grafana-pv",
        metadata={
            "name": "guestbook-grafana-pv",
            "labels": GRAFANA_STORAGE_LABELS,
        },
        spec={
            "capacity": {
                "storage": GRAFANA_STORAGE_SIZE,
            },
            "accessModes": ["ReadWriteOnce"],
            "persistentVolumeReclaimPolicy": "Retain",
            "storageClassName": GRAFANA_STORAGE_CLASS,
            "hostPath": {
                "path": "/mnt/data/guestbook-grafana",
                "type": "DirectoryOrCreate",
            },
        },
        opts=opts,
    )


def create_grafana_persistent_volume_claim(
    namespace: str,
    grafana_pv: PersistentVolume,
    opts: ResourceOptions,
) -> PersistentVolumeClaim:
    return PersistentVolumeClaim(
        "grafana-pvc",
        metadata={
            "name": GRAFANA_CLAIM_NAME,
            "namespace": namespace,
        },
        spec={
            "accessModes": ["ReadWriteOnce"],
            "storageClassName": GRAFANA_STORAGE_CLASS,
            "selector": {
                "matchLabels": GRAFANA_STORAGE_LABELS,
            },
            "resources": {
                "requests": {
                    "storage": GRAFANA_STORAGE_SIZE,
                },
            },
        },
        opts=ResourceOptions.merge(opts, ResourceOptions(depends_on=[grafana_pv])),
    )


def grafana_persistence_values() -> dict:
    return {
        "enabled": True,
        "type": "pvc",
        "existingClaim": GRAFANA_CLAIM_NAME,
        "accessModes": ["ReadWriteOnce"],
        "size": GRAFANA_STORAGE_SIZE,
    }
