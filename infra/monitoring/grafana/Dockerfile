# The Grafana container: the official image with the datasource and the
# SlicePizza dashboards inside it (ADR 0013). Secrets are not here: the admin
# password comes from GF_SECURITY_ADMIN_PASSWORD on the server.
FROM grafana/grafana:13.2.6

ENV GF_USERS_ALLOW_SIGN_UP=false \
    GF_AUTH_ANONYMOUS_ENABLED=false \
    GF_ANALYTICS_REPORTING_ENABLED=false \
    GF_ANALYTICS_CHECK_FOR_UPDATES=false

# Grafana runs as uid 472 (group 0).
COPY --chown=472:0 provisioning /etc/grafana/provisioning
COPY --chown=472:0 dashboards /var/lib/grafana/dashboards
