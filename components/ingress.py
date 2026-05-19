from pulumi import ResourceOptions
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.core.v1 import Namespace, Service, ServicePortArgs, ServiceSpecArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs


def create_ingress_namespace(
    namespace: str,
    opts: ResourceOptions,
) -> Namespace:
    return Namespace(
        namespace,
        metadata=ObjectMetaArgs(name=namespace),
        opts=opts,
    )


def create_ingress_nginx(
    namespace: str,
    opts: ResourceOptions,
) -> Release:
    return Release(
        "ingress-nginx",
        ReleaseArgs(
            chart="ingress-nginx",
            namespace=namespace,
            repository_opts=RepositoryOptsArgs(
                repo="https://kubernetes.github.io/ingress-nginx",
            ),
            values={
                "controller": {
                    "metrics": {
                        "enabled": True,
                        "serviceMonitor": {
                            "enabled": True,
                        },
                    },
                    "service": {
                        "type": "ClusterIP",
                    },
                },
            },
        ),
        opts=opts,
    )


def create_guestbook_ingress(
    app_namespace: str,
    opts: ResourceOptions,
) -> CustomResource:
    return CustomResource(
        "guestbook-frontend-ingress",
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata={
            "name": "guestbook-frontend",
            "namespace": app_namespace,
            "annotations": {
                "nginx.ingress.kubernetes.io/backend-protocol": "HTTP",
            },
        },
        spec={
            "ingressClassName": "nginx",
            "rules": [
                {
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "frontend",
                                        "port": {
                                            "number": 80,
                                        },
                                    }
                                },
                            }
                        ]
                    }
                }
            ],
        },
        opts=opts,
    )


def create_guestbook_ingress_external_service(
    namespace: str,
    service_type: str,
    opts: ResourceOptions,
) -> Service:
    return Service(
        "guestbook-ingress-external",
        metadata=ObjectMetaArgs(
            name="guestbook-ingress-external",
            namespace=namespace,
            labels={
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/component": "controller",
            },
        ),
        spec=ServiceSpecArgs(
            type=service_type,
            selector={
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/component": "controller",
            },
            ports=[
                ServicePortArgs(
                    name="http",
                    port=80,
                    target_port="http",
                )
            ],
        ),
        opts=opts,
    )
