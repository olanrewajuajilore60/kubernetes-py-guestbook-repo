from typing import Sequence

from pulumi import ResourceOptions
from pulumi_kubernetes.apiextensions import CustomResource


class ServiceMonitor(CustomResource):
    def __init__(
        self,
        name: str,
        monitor_namespace: str,
        app_namespace: str,
        app_names: Sequence[str],
        service_port_name: str,
        path: str = "/metrics",
        params: dict = None,
        opts: ResourceOptions = None,
    ):
        endpoint = {
            "port": service_port_name,
            "path": path,
            "interval": "30s",
        }
        if params:
            endpoint["params"] = params

        super().__init__(
            name,
            api_version="monitoring.coreos.com/v1",
            kind="ServiceMonitor",
            metadata={
                "name": name,
                "namespace": monitor_namespace,
                "labels": {
                    "app.kubernetes.io/name": "guestbook",
                },
            },
            spec={
                "namespaceSelector": {
                    "matchNames": [app_namespace],
                },
                "selector": {
                    "matchExpressions": [
                        {
                            "key": "app",
                            "operator": "In",
                            "values": list(app_names),
                        }
                    ],
                },
                "endpoints": [endpoint],
            },
            opts=opts,
        )
