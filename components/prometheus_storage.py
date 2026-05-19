from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import PersistentVolume

PROMETHEUS_STORAGE_CLASS = "guestbook-prometheus-static"
PROMETHEUS_STORAGE_LABELS = {
    "app.kubernetes.io/name": "guestbook-prometheus-storage",
}
PROMETHEUS_STORAGE_SIZE = "20Gi"


def create_prometheus_persistent_volume(opts: ResourceOptions) -> PersistentVolume:
    return PersistentVolume(
        "prometheus-pv",
        metadata={
            "name": "guestbook-prometheus-pv",
            "labels": PROMETHEUS_STORAGE_LABELS,
        },
        spec={
            "capacity": {
                "storage": PROMETHEUS_STORAGE_SIZE,
            },
            "accessModes": ["ReadWriteOnce"],
            "persistentVolumeReclaimPolicy": "Retain",
            "storageClassName": PROMETHEUS_STORAGE_CLASS,
            "hostPath": {
                "path": "/mnt/data/guestbook-prometheus",
                "type": "DirectoryOrCreate",
            },
        },
        opts=opts,
    )


def prometheus_storage_spec() -> dict:
    return {
        "volumeClaimTemplate": {
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "storageClassName": PROMETHEUS_STORAGE_CLASS,
                "selector": {
                    "matchLabels": PROMETHEUS_STORAGE_LABELS,
                },
                "resources": {
                    "requests": {
                        "storage": PROMETHEUS_STORAGE_SIZE,
                    },
                },
            },
        },
    }
