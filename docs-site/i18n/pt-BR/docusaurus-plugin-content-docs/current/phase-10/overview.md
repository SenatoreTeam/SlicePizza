# Fase 10 — Visão geral

**Pedido do Zé:** _"Mudamos o banco de dados e doeu."_

:::info Situação
**Em andamento** (desde 21/11/2026). Veja o [roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 10 entrega

- **A cobertura de testes é medida em toda mudança** (feito). O pipeline falha se os testes
  passarem a cobrir menos do código do que antes: hoje, pelo menos 85% da API e 70% do worker.
  A regra: subir o mínimo quando entram testes, nunca baixá-lo para uma mudança passar.

## Planejado

- **Migrações do banco** ([#95](https://github.com/SenatoreTeam/SlicePizza/issues/95)): hoje a
  API só cria tabelas que faltam, então pôr uma coluna numa tabela existente exige trabalho
  manual no servidor. As migrações vão mudar o banco passo a passo quando uma versão nova
  sobe. Antes, o banco real do servidor é conferido, para a versão 1 bater com ele.
- **Um relatório em toda mudança que mexe no banco**
  ([#96](https://github.com/SenatoreTeam/SlicePizza/issues/96)): o SQL, e um aviso quando algo
  apagaria dados.
- **Uma regra para voltar atrás** ([#97](https://github.com/SenatoreTeam/SlicePizza/issues/97)):
  voltar à versão anterior nunca desfaz uma migração, então cada migração também precisa
  funcionar com a versão anterior.
