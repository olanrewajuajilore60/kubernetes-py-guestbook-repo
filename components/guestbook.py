from pulumi_kubernetes.core.v1 import ContainerArgs, ContainerPortArgs, EnvVarArgs

from frontend_monitoring import (
    FRONTEND_METRICS_PORT,
    FRONTEND_METRICS_PORT_NAME,
    frontend_exporter,
    frontend_service_annotations,
)
from service_deployment import ServiceDeployment


def create_guestbook(is_minikube: bool) -> ServiceDeployment:
    redis_service_ports = {
        6379: "redis",
        9121: "metrics",
    }

    ServiceDeployment(
        "redis-leader",
        image="redis",
        ports=[6379, 9121],
        service_port_names=redis_service_ports,
        extra_containers=[redis_exporter()],
    )
    ServiceDeployment(
        "redis-replica",
        image="pulumi/guestbook-redis-replica",
        ports=[6379, 9121],
        service_port_names=redis_service_ports,
        extra_containers=[redis_exporter()],
    )
    return ServiceDeployment(
        "frontend",
        image="pulumi/guestbook-php-redis",
        replicas=3,
        ports=[80, FRONTEND_METRICS_PORT],
        service_port_names={
            80: "http",
            FRONTEND_METRICS_PORT: FRONTEND_METRICS_PORT_NAME,
        },
        extra_containers=[frontend_exporter()],
        service_annotations=frontend_service_annotations(),
        allocate_ip_address=True,
        is_minikube=is_minikube,
    )


def redis_exporter() -> ContainerArgs:
    return ContainerArgs(
        name="redis-exporter",
        image="oliver006/redis_exporter:v1.62.0",
        env=[
            EnvVarArgs(
                name="REDIS_ADDR",
                value="redis://localhost:6379",
            )
        ],
        ports=[
            ContainerPortArgs(
                name="metrics",
                container_port=9121,
            )
        ],
    )
