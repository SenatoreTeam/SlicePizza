# Fase 2 — O site e o proxy

Esta página explica **como as peças se encaixam**. Para os arquivos, as configurações e os
comandos, veja o [README do frontend](https://github.com/SenatoreTeam/SlicePizza/blob/main/frontend/README.md) e o
[DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md).

## Um domínio, dois tipos de requisição

```
https://slicepizza.senatore.tech
        │   (o proxy do servidor cuida do HTTPS)
        ▼
   contêiner web: Caddy, porta 8080
        ├── /api/*  ──►  contêiner api (a API de pedidos), sem o prefixo "/api"
        └── qualquer outro caminho  ──►  os arquivos do site de cardápio
```

O roadmap sugeria uma CDN para o site e subdomínios separados para `api` e `admin`. O
SlicePizza roda em um servidor compartilhado que já tem domínio, Docker e um proxy HTTPS, então
usa um formato mais simples: **um domínio, com o Caddy decidindo pelo caminho**. Os motivos e
as alternativas estão no [ADR 0003](/adr/0003-one-domain-caddy-in-front).

Um efeito colateral útil: o site e a API compartilham a mesma origem, então o navegador nunca
precisa de CORS para chamar a API, e o CORS fica desligado.

## O site de cardápio

O site não tem framework nem etapa de build: `index.html`, `app.js`, `styles.css` e um
pequeno `config.js`. A jornada do cliente:

1. O cardápio é carregado de `GET /api/menu`.
2. O cliente escolhe as pizzas e preenche nome, telefone e endereço.
3. `POST /api/orders` cria o pedido, e a página passa para a página de status do pedido.
4. A página de status consulta o pedido a cada 10 segundos até que ele seja entregue ou
   cancelado, e pausa enquanto a aba está em segundo plano.

O texto vindo da API só é inserido na página como **texto**, nunca como HTML, e uma
Content-Security-Policy definida pelo Caddy só permite que a página carregue os próprios
scripts.

## O que a API precisa saber

Duas configurações pequenas fazem a API se comportar corretamente atrás do proxy:

- `UVICORN_ROOT_PATH=/api`, para que a página `/docs` da própria API encontre o schema em
  `/api`.
- `UVICORN_FORWARDED_ALLOW_IPS`, para que a API só confie nos cabeçalhos `X-Forwarded-*`
  quando eles vierem da rede privada onde o proxy está.

## Do merge à produção

```
merge na main ──► o GitHub Actions gera as imagens ──► registro de contêineres do GitHub
                                                         │
                        o servidor procura imagens novas a cada 5 minutos
```

Nada é copiado para o servidor à mão. Os passos da primeira configuração e da migração do
formato anterior (só a API) estão no [DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md).
