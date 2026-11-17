# The Loki container: the official image with SlicePizza's configuration inside
# it (ADR 0014), the same pattern as Prometheus. Logs are kept 7 days; the data
# folder is a volume (docker-compose.yml) and survives a new image.
FROM grafana/loki:3.7.9

COPY loki.yml /etc/loki/loki.yml

CMD ["-config.file=/etc/loki/loki.yml"]
