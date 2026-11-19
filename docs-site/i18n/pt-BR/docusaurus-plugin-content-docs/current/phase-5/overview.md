# Fase 5 — Visão geral

**Pedido do Zé:** _"O site caiu na sexta à noite e ninguém percebeu."_

Depois da Fase 4, uma mudança chega à produção com segurança, mas ninguém observava o que o
sistema faz depois de no ar. A Fase 5 faz o sistema **avisar o que está errado antes do
cliente**.

:::info Situação
Esta fase está **em andamento**. Feito e integrado: verificações de saúde. As métricas, painéis,
logs e alertas construídos aqui primeiro foram removidos: o monitoramento é do servidor, que
acompanha todos os projetos nele ([ADR 0016](/adr/0016-server-monitoring)). Falta: a
verificação externa de disponibilidade. Veja o [roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 5 entrega

- **Verificações de saúde** em todos os serviços, para o Docker e o deploy saberem o que está
  vivo.
- **O monitoramento do servidor** ([ADR 0016](/adr/0016-server-monitoring)): o servidor onde o
  SlicePizza roda tem um só monitoramento para todos os projetos dele. Ele mostra os contêineres
  do SlicePizza (rodando, saudáveis, memória, processador), a fila de notificações, a fila de
  eventos, as contagens de pedidos, os backups, a versão no ar e os sites públicos. Por enquanto
  os painéis são gerais, nenhum de um serviço só. Este repositório não implementa monitoramento
  próprio.

## Tentado e removido

Este repositório teve primeiro um monitoramento próprio ([ADR 0012](/adr/0012-api-metrics),
[0013](/adr/0013-prometheus-and-grafana), [0014](/adr/0014-loki-and-alloy) e
[0015](/adr/0015-grafana-telegram-alerts)): as métricas da própria API em um `/metrics` privado,
Prometheus, Grafana com um painel do SlicePizza, Loki e Alloy para os logs, e alertas no
Telegram. Ele rodou localmente e no CI, nunca no servidor, e foi removido quando o
monitoramento do servidor assumiu esse papel (a versão 1.2.1 tira o `/metrics` da API). Os
arquivos estão no histórico do Git.

## Bom saber

- Um monitoramento que roda no servidor não consegue avisar que o servidor sumiu. Por isso uma
  verificação externa de disponibilidade, de um serviço hospedado, é o próximo passo
  ([DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md#external-uptime-check)).
