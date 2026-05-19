#  Copyright 2016-2020, Pulumi Corporation.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pulumi
from guestbook import create_guestbook
from observability import ObservabilityStack

# Minikube does not implement services of type `LoadBalancer`; require the user to specify if we're
# running on minikube, and if so, create only services of type ClusterIP.
config = pulumi.Config()
isMinikube = config.get_bool("isMinikube")
app_namespace = config.get("appNamespace") or "default"
grafana_service_type = config.get("grafanaServiceType") or (
    "NodePort" if isMinikube else "LoadBalancer"
)
ingress_service_type = config.get("ingressServiceType") or (
    "NodePort" if isMinikube else "LoadBalancer"
)
grafana_admin_user = config.get("grafanaAdminUser") or "admin"
grafana_admin_password = config.get_secret("grafanaAdminPassword") or pulumi.Output.secret(
    "admin"
)

frontend = create_guestbook(isMinikube)
observability = ObservabilityStack(
    "observability",
    app_namespace=app_namespace,
    monitored_apps=["redis-leader", "redis-replica"],
    grafana_service_type=grafana_service_type,
    ingress_service_type=ingress_service_type,
    grafana_admin_user=grafana_admin_user,
    grafana_admin_password=grafana_admin_password,
)

pulumi.export("frontend_ip", frontend.ip_address)
pulumi.export("grafana_namespace", observability.namespace)
pulumi.export("grafana_service_type", grafana_service_type)
pulumi.export("grafana_url", observability.grafana_url)
pulumi.export("grafana_node_port", observability.grafana_node_port)
pulumi.export("grafana_admin_user", grafana_admin_user)
pulumi.export("grafana_admin_password", grafana_admin_password)
pulumi.export("guestbook_ingress_url", observability.guestbook_ingress_url)
pulumi.export("guestbook_ingress_node_port", observability.guestbook_ingress_node_port)
