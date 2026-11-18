# Fase 5 — Visão geral

**Pedido do Zé:** _"O site caiu na sexta à noite e ninguém percebeu."_

Depois da Fase 4, uma mudança chega à produção com segurança, mas ninguém observava o que o
sistema faz depois de no ar. A Fase 5 faz o sistema **avisar o que está errado antes do
cliente**.

:::info Situação
Esta fase está **em andamento**. Feito e integrado: verificações de saúde, métricas, painéis,
logs e alertas no Telegram. Falta: o teste de derrubar de propósito, a verificação externa de
disponibilidade e colocar o monitoramento no servidor. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 5 entrega

- **Verificações de saúde** em todos os serviços, para o Docker e o deploy saberem o que está
  vivo.
- **Métricas** ([ADR 0012](/adr/0012-api-metrics)): a API informa pedidos,
  latência, erros e a fila de eventos em um `/metrics` privado.
- **Painéis** ([ADR 0013](/adr/0013-prometheus-and-grafana)): o Prometheus
  guarda os números e o Grafana mostra uma visão geral do SlicePizza que mora no Git.
- **Logs** ([ADR 0014](/adr/0014-loki-and-alloy)): o Loki guarda 7 dias de logs
  de cada contêiner, o Alloy os coleta por um proxy do Docker somente leitura, e dá para
  pesquisar no mesmo Grafana.
- **Alertas** ([ADR 0015](/adr/0015-grafana-telegram-alerts)): o Grafana manda
  mensagem em um chat do Telegram quando a API cai, mais de 5% das requisições falham, um pedido
  demora mais de 5 minutos para chegar à cozinha, uma fila acumula ou a API registra muitos
  erros. Cada regra precisa persistir por alguns minutos, então um solavanco passa em silêncio.
  O token do bot e o id do chat nunca ficam no repositório.

## Bom saber

- O Prometheus e o Loki não têm login próprio e **nunca recebem domínio**; só o Grafana é
  público, atrás do login dele.
- Os alertas moram no mesmo servidor: se o servidor sumir, não chega mensagem. Por isso a
  verificação externa de disponibilidade é o próximo passo.
- Os logs podem conter dados pessoais; ficam no servidor e são guardados por 7 dias.
