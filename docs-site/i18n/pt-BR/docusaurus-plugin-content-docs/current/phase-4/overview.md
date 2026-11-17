# Fase 4 — Visão geral

**Pedido do Zé:** _"Toda vez que vocês mudam alguma coisa, algo quebra."_

No fim da Fase 3 eram quatro serviços e vários segredos, todos atualizados com um merge na
`main`. Os testes rodavam em todo Pull Request, mas nada impedia um merge com testes vermelhos,
e as imagens eram publicadas ao mesmo tempo em que os testes rodavam, e não depois. A Fase 4
torna o caminho do merge até a produção automático **e** seguro.

:::info Situação
Esta fase está **concluída**: no ar desde 17/11/2026. Um merge que acrescenta uma versão no
`releases.toml` chega à produção sozinho, conferido, sem ninguém entrar no servidor. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 4 entrega

- **Um pipeline** para toda mudança: lint, depois os testes, depois as imagens. Uma imagem só é
  publicada quando tudo antes dela passou. Veja [O pipeline](/docs/phase-4/pipeline).
- **Versões numeradas**: a produção roda uma versão (`1.1.0`), escrita no `releases.toml` e
  publicada pelo pipeline quando um merge acrescenta uma, nunca "o que a `main` tiver agora".
  Cada imagem diz de qual commit foi gerada, e a versão e o que mudou aparecem no sistema. Veja
  [Versões e releases](/docs/phase-4/versions).
- **Um deploy conferido**: o servidor encontra sozinho cada versão nova no GHCR, faz o backup do
  banco, faz o deploy, confere e volta a versão anterior se as verificações falharem. O GitHub
  nunca acessa o servidor, então nenhum segredo de deploy fica no GitHub.
- Não foi feito: um ambiente de **staging**. As verificações e a volta automática protegem a
  produção; o staging continua sendo uma opção.

## Por que automatizar

Conferir à mão funciona enquanto uma pessoa muda uma coisa por vez. Com várias pessoas, vários
serviços e o Dependabot abrindo Pull Requests toda semana, alguém acaba esquecendo um passo. Um
pipeline faz as mesmas verificações toda vez, na mesma ordem, e se recusa a entregar o que
falha nelas.
