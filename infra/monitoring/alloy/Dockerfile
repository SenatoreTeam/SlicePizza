# The Alloy container: the official image with the log collection config inside
# it (ADR 0014). It reads logs through the socket proxy and pushes to Loki.
FROM grafana/alloy:v1.21.3

# The image starts as root; with all capabilities dropped (docker-compose.yml) root
# cannot open the data folder that belongs to the alloy user, so run as that user.
USER alloy

COPY config.alloy /etc/alloy/config.alloy

CMD ["run", "--server.http.listen-addr=0.0.0.0:12345", "--storage.path=/var/lib/alloy/data", "/etc/alloy/config.alloy"]
