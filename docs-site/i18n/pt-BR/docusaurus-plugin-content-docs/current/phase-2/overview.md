# Fase 2 — Visão geral

**Pedido do Zé:** _"Quero o site no ar, no meu próprio domínio."_

A Fase 1 terminou com tudo rodando em um único notebook. Na Fase 2, o sistema ganha um
endereço público, **https://slicepizza.senatore.tech**, e um site de cardápio que os clientes
podem usar pelo celular.

:::info Situação
Esta fase está **concluída**. O sistema está no ar em https://slicepizza.senatore.tech desde
2026-11-15, e um pedido foi feito pelo site no ar. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 2 entrega

- Um **site de cardápio** em HTML, CSS e JavaScript puros (sem etapa de build): o cliente
  escolhe as pizzas, faz o pedido e acompanha pela página de status.
- Um contêiner **Caddy** na frente da API que serve o site em `/` e a API em `/api`, para que
  tudo fique em um só domínio.
- Imagens publicadas automaticamente no registro de contêineres do GitHub a cada merge, e
  baixadas pelo servidor em cerca de cinco minutos.
- Arquivos de lock com hashes para as dependências da API, para que os mesmos pacotes sejam
  instalados sempre.

## O problema que esta fase cria

O sistema agora é público, mas os pedidos são apenas **registrados**. Ninguém é avisado quando
um pedido chega, e o cliente precisa recarregar a página de status para saber que a pizza saiu
para entrega. Na Fase 3, o Zé pede que os clientes sejam avisados.

Continue com [o site e o proxy](/docs/phase-2/site-and-proxy).
