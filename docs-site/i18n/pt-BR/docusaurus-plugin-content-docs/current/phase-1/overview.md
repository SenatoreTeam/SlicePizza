# Fase 1 — Visão geral

**Pedido do Zé:** _"Quero ver isso rodando no seu computador."_

A Fase 1 consiste em colocar a API de pedidos e o banco de dados para rodar localmente com
Docker Compose, mantendo os pedidos entre reinicializações.

## O que a Fase 1 entrega

- Uma API de pedidos em FastAPI
- Um banco de dados PostgreSQL 16
- Uma stack `docker compose` com um volume nomeado para os dados
- Um cardápio inicial (seed)
- Uma suíte de testes pytest

## O problema que esta fase cria

Tudo roda em uma única máquina, sem URL pública e sem automação. Esse problema é exatamente
o que as próximas fases resolvem: na Fase 2, o Zé pede que o site fique no ar no domínio dele.

Continue com [a API](/docs/phase-1/api) ou [a configuração do Docker](/docs/phase-1/docker).
