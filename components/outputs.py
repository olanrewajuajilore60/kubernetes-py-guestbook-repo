def load_balancer_url(status) -> str:
    if not status or not status.load_balancer or not status.load_balancer.ingress:
        return ""

    ingress = status.load_balancer.ingress[0]
    host = ingress.ip or ingress.hostname
    return f"http://{host}" if host else ""
