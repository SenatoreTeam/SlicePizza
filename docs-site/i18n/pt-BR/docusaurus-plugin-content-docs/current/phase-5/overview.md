# Fase 5 — Visão geral

**Pedido do Zé:** _"O site caiu na sexta à noite e ninguém percebeu."_

Depois da Fase 4, uma mudança chega à produção com segurança, mas ninguém observava o que o
sistema faz depois de no ar. A Fase 5 garante que **alguém seja avisado quando algo quebra**.

:::info Situação
Esta fase está **concluída** (19/11/2026). O repositório primeiro construiu o próprio monitoramento
(métricas, Prometheus, Grafana, Loki, alertas) e depois **o removeu** na versão 1.2.1
([ADR 0016](/adr/0016-server-monitoring)): o monitoramento pertence ao servidor onde o SlicePizza
roda, não a este repositório. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que ficou neste repositório

- **Verificações de saúde** em todos os serviços (`/health`, `/api/health`, `/version` e as
  verificações dos próprios contêineres), para o Docker, o deploy e qualquer monitor externo
  saberem o que está vivo.

## Por que o monitoramento foi para o servidor

O SlicePizza é convidado em um servidor compartilhado por vários projetos. Esse servidor já tem
um monitoramento para a máquina toda, mantido no repositório do próprio dono do servidor. Ele já
vigia o SlicePizza de fora da rede: contêineres, a fila de notificações e mensagens mortas, a
fila de eventos, contagem de pedidos, backups, a versão no ar e os sites públicos. Um segundo
Prometheus e Grafana para um só projeto repetiria tudo isso, traria mais versões para revisar e
poria um proxy do socket do Docker e um segundo domínio público do Grafana em um convidado.

Os ADRs [0012](/adr/0012-api-metrics) a [0015](/adr/0015-grafana-telegram-alerts) ficam como
registro do que foi construído e testado (inclusive um teste de derrubar de propósito em que o
alerta disparou 56 segundos depois da queda da API) e de por que foi removido.
