# Tour do produto

Capturas de tela do sistema rodando localmente com `docker compose up`. Todos os nomes, telefones e endereços são dados de demonstração fictícios.

## O site do cardápio

Os clientes escolhem as pizzas no cardápio servido na raiz do site. A página conversa com a API por `/api` (mesmo domínio, [ADR 0003](/adr/0003-one-domain-caddy-in-front)).

![O cardápio com preços e seletores de quantidade](@site/static/img/screenshots/menu.png)

No celular, o layout vira uma única coluna, com o total e o botão de pedido fixos na parte de baixo:

![O cardápio no celular](@site/static/img/screenshots/menu-mobile.png)

## Fazendo um pedido

Depois de escolher as pizzas, o cliente informa nome, telefone e endereço de entrega. O pedido é validado pela API, então os preços sempre vêm do banco de dados e nunca do navegador.

![O formulário de entrega com o total do carrinho](@site/static/img/screenshots/menu-order-form.png)

## Acompanhando o pedido

Cada pedido tem a própria página, mostrando as quatro etapas: recebido, em preparo, a caminho e entregue. Com o Telegram configurado, um botão "Follow on Telegram" também aparece aqui.

![A página de status do pedido](@site/static/img/screenshots/order-status.png)

## O painel da cozinha

A pizzaria vê os pedidos em `/kitchen/`, atrás de um login ([ADR 0007](/adr/0007-kitchen-login)). Os pedidos passam de **New** para **In the oven** e depois **On the way** com um único botão, e podem ser cancelados enquanto são novos.

![O painel da cozinha com pedidos em três colunas](@site/static/img/screenshots/kitchen-board.png)

*A interface do cardápio e do painel está em inglês, como no código.*

## A API

O FastAPI publica documentação interativa em `/api/docs` (e em `/docs` quando você roda a API sozinha).

![Swagger UI listando as rotas da API](@site/static/img/screenshots/api-docs.png)
