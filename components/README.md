# Kubernetes Guestbook with Prometheus and Grafana

This Pulumi program deploys the Kubernetes Guestbook application and an
observability stack based on the `kube-prometheus-stack` Helm chart.

The application includes:

- Redis leader and replica `Deployment` and `Service` resources.
- A replicated Guestbook frontend exposed with `LoadBalancer` or `ClusterIP`
  depending on the `isMinikube` setting.
- Redis exporter sidecars for backend metrics.
- A blackbox exporter sidecar on the frontend pods for direct frontend service
  scraping.
- Prometheus, Grafana, kube-state-metrics, node-exporter, and the Prometheus
  Operator from the Helm chart.
- Persistent storage for Prometheus and Grafana using Pulumi-managed
  persistent volumes and persistent volume claims.
- `ServiceMonitor` resources that scrape Redis exporter metrics from the
  backend services and blackbox probe metrics from the frontend service.
- An ingress-nginx controller with Prometheus metrics enabled.
- A Kubernetes `Ingress` that routes external HTTP traffic to the Guestbook
  frontend service.
- A Grafana dashboard for real frontend request rate, frontend error rate,
  frontend pod CPU, memory, network receive rate, pod restarts, Redis command
  rate, and Redis connected clients.

Frontend request and error-rate panels use ingress-nginx metrics. Generate
traffic through the exported `guestbook_ingress_url`; traffic sent directly to
the frontend `Service` bypasses ingress-nginx and will not appear in those
request/error panels.

## File Structure

The Pulumi resources are split by responsibility:

- `__main__.py` reads stack configuration, composes the Guestbook and
  observability components, and exports stack outputs.
- `guestbook.py` creates the Redis leader, Redis replica, frontend service, and
  wires in frontend monitoring settings.
- `frontend_monitoring.py` defines the frontend blackbox exporter sidecar,
  frontend Prometheus scrape annotations, and frontend `ServiceMonitor`.
- `service_deployment.py` defines the reusable `ServiceDeployment` component
  used by the Guestbook workloads.
- `observability.py` orchestrates the monitoring, Grafana, ingress, dashboard,
  and ServiceMonitor modules.
- `monitoring.py` creates the `monitoring` namespace and the
  `kube-prometheus-stack` Helm release.
- `storage.py` composes the monitoring persistent storage resources.
- `prometheus_storage.py` creates the Prometheus persistent volume and provides
  the Helm `storageSpec` used by the Prometheus Operator.
- `grafana_storage.py` creates the Grafana persistent volume and persistent
  volume claim and provides the Helm persistence values used by Grafana.
- `ingress.py` creates the `ingress-nginx` namespace, ingress-nginx Helm
  release, Guestbook `Ingress`, and external ingress service.
- `grafana.py` creates the external Grafana service and dashboard `ConfigMap`.
- `dashboards.py` contains the Grafana dashboard JSON definition.
- `service_monitor.py` defines the Prometheus Operator `ServiceMonitor`
  resource used to scrape Redis exporter and frontend blackbox metrics.
- `outputs.py` contains shared helpers for deriving service URLs from
  LoadBalancer status.

## Prerequisites

- Pulumi CLI
- Python 3
- A working Kubernetes context
- Network access to pull container images and Helm charts from
  `https://prometheus-community.github.io/helm-charts`

## Configure

The default persistent storage uses static `hostPath` persistent volumes:

- Prometheus PV: `guestbook-prometheus-pv`, `20Gi`,
  `/mnt/data/guestbook-prometheus`
- Grafana PV: `guestbook-grafana-pv`, `10Gi`, `/mnt/data/guestbook-grafana`
- Grafana PVC: `grafana-storage` in the `monitoring` namespace
- Prometheus PVC: created from the `prometheus.prometheusSpec.storageSpec`
  volume claim template and bound to `guestbook-prometheus-pv`

This is suitable for local or single-node clusters such as minikube. For a
multi-node or cloud cluster, adapt `prometheus_storage.py` and
`grafana_storage.py` to use your cluster's storage class, CSI provisioner, NFS,
cloud disk, or another production storage backend.

Create and select a stack:

```sh
pulumi stack init dev
```

For minikube, use `NodePort` for Grafana:

```sh
pulumi config set isMinikube true
pulumi config set grafanaServiceType NodePort
pulumi config set ingressServiceType NodePort
```

For a cloud Kubernetes cluster, use `LoadBalancer` for Grafana:

```sh
pulumi config set isMinikube false
pulumi config set grafanaServiceType LoadBalancer
pulumi config set ingressServiceType LoadBalancer
```

Optional Grafana credentials:

```sh
pulumi config set grafanaAdminUser admin
pulumi config set --secret grafanaAdminPassword admin
```

If you deploy the Guestbook app into a namespace other than `default`, set the
namespace used by the `ServiceMonitor`:

```sh
pulumi config set appNamespace default
```

## Deploy

Install dependencies and deploy:

```sh
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pulumi up
```

Pulumi exports:

- `frontend_ip`
- `grafana_namespace`
- `grafana_service_type`
- `grafana_url`
- `grafana_node_port`
- `grafana_admin_user`
- `grafana_admin_password`
- `guestbook_ingress_url`
- `guestbook_ingress_node_port`

Read the Grafana access details:

```sh
pulumi stack output grafana_url
pulumi stack output grafana_admin_user
pulumi stack output grafana_admin_password --show-secrets
pulumi stack output guestbook_ingress_url
```

For `LoadBalancer`, `grafana_url` is populated after the cloud provider assigns
an external IP or hostname. If it is initially blank, wait a minute and run:

```sh
pulumi refresh
pulumi stack output grafana_url
```

For minikube `NodePort`, the exported URL uses `localhost` and the allocated
node port. You can also ask minikube for the exact URL:

```sh
minikube service grafana-external -n monitoring --url
minikube service guestbook-ingress-external -n ingress-nginx --url
```

Open the Guestbook through the ingress URL so ingress-nginx emits request and
error metrics:

```sh
pulumi stack output guestbook_ingress_url
```

## Verify Prometheus Scraping

Confirm the monitoring stack is running:

```sh
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Confirm Prometheus and Grafana persistent storage exists:

```sh
kubectl get pv guestbook-prometheus-pv guestbook-grafana-pv
kubectl get pvc -n monitoring
```

Confirm the Guestbook services expose metrics ports:

```sh
kubectl get svc frontend redis-leader redis-replica -o wide
kubectl get endpoints frontend redis-leader redis-replica
```

Confirm the `ServiceMonitor` resources exist:

```sh
kubectl get servicemonitor -n monitoring guestbook-redis-exporters
kubectl get servicemonitor -n monitoring guestbook-frontend
kubectl get servicemonitor -n ingress-nginx
kubectl get ingress guestbook-frontend
```

Port-forward Prometheus:

```sh
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open `http://localhost:9090/targets` and look for the
`guestbook-frontend`, `guestbook-redis-exporters`, and ingress-nginx controller
targets. Useful Prometheus queries:

```promql
probe_success{service="frontend"}
probe_duration_seconds{service="frontend"}
sum(rate(nginx_ingress_controller_requests{ingress="guestbook-frontend"}[5m])) by (status)
sum(rate(nginx_ingress_controller_requests{ingress="guestbook-frontend",status=~"4..|5.."}[5m])) by (status)
redis_up
rate(redis_commands_processed_total[5m])
redis_connected_clients
sum(rate(container_cpu_usage_seconds_total{namespace="default",pod=~"frontend-.*",container!="",container!="POD"}[5m])) by (pod)
container_memory_working_set_bytes{namespace="default",pod=~"frontend-.*",container!="",container!="POD"}
```

If you changed `appNamespace`, replace `default` in the PromQL examples with
that namespace.

## Grafana Dashboard

Log in to Grafana with the Pulumi outputs:

```sh
pulumi stack output grafana_admin_user
pulumi stack output grafana_admin_password --show-secrets
```

The dashboard is provisioned automatically by Grafana's dashboard sidecar. In
Grafana, open:

```text
Dashboards > Guestbook Overview
```

The dashboard includes panels for:

- Frontend pod CPU usage
- Frontend pod memory usage
- Frontend request rate by HTTP status from ingress-nginx
- Frontend error rate by HTTP status from ingress-nginx
- Frontend direct probe success from the frontend `ServiceMonitor`
- Frontend direct probe latency from the frontend `ServiceMonitor`
- Frontend network receive rate
- Pod restarts
- Redis command rate
- Redis connected clients

## Destroy

```sh
pulumi destroy
pulumi stack rm
```
