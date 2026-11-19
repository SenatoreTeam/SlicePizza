# Fase 6 — Visão geral

**Pedido do Zé:** _"O servidor morreu e perdemos os pedidos."_

:::info Situação
Esta fase está **concluída** (19/11/2026), pelo dono do servidor. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que aconteceu com esta fase

O plano era Terraform e Ansible para reconstruir um servidor na nuvem, e S3 para os backups. O
sistema real é uma **VPS com Docker e Dokploy**, então:

- **Sem Terraform e sem Ansible**: não há API de nuvem para criar recursos, e o Docker e o Dokploy
  já administram a máquina ([ADR 0017](/adr/0017-docker-only-infrastructure)).
- **Os backups são do dono do servidor**: a VPS inteira tem backup, incluindo os dados do Postgres
  e do RabbitMQ, assim como o monitoramento é trabalho do servidor
  ([ADR 0018](/adr/0018-server-backups)).

O que este repositório deve é continuar **reproduzível**: o arquivo do compose, os arquivos do
Caddy e o `.env.example` ficam no Git, e os segredos ficam só no `.env` do servidor.
