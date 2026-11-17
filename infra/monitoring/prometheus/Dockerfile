# The Prometheus container: the official image with SlicePizza's scrape
# configuration inside it (ADR 0013), the same way the web image carries the
# site. The server's compose then needs no copy of this repository's files.
FROM prom/prometheus:v3.15.1

COPY prometheus.yml /etc/prometheus/prometheus.yml

# The base image's own command, plus the retention limits: 15 days and at most
# 2 GB, because a full disk would take the whole server down with it. The data
# folder is a volume (docker-compose.yml): it survives a new image.
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--storage.tsdb.retention.time=15d", \
     "--storage.tsdb.retention.size=2GB"]
