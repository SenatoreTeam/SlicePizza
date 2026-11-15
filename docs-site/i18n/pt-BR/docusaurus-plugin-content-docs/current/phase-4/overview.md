# Fase 4 — Visão geral

**Pedido do Zé:** _"Toda vez que vocês mudam alguma coisa, algo quebra."_

No fim da Fase 3 eram quatro serviços e vários segredos, todos atualizados com um merge na
`main`. Os testes rodavam em todo Pull Request, mas nada impedia um merge com testes vermelhos,
e as imagens eram publicadas ao mesmo tempo em que os testes rodavam, e não depois. A Fase 4
torna o caminho do merge até a produção automático **e** seguro.

:::info Situação
Esta fase está **em andamento**: o pipeline e o deploy estão prontos, e entram no ar quando o
ambiente de staging for configurado no servidor. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 4 entrega

- **Um pipeline** para toda mudança: lint, depois os testes, depois as imagens. Uma imagem só é
  publicada quando tudo antes dela passou. Veja [O pipeline](/docs/phase-4/pipeline).
- **Imagens versionadas**: cada imagem diz de qual commit foi gerada.
- Um ambiente de **staging** em `staging.slicepizza.senatore.tech`, e um deploy que o pipeline
  dispara e confere, primeiro no staging e depois em produção, com os segredos no GitHub. Veja
  [O deploy](/docs/phase-4/deploy).

## Por que automatizar

Conferir à mão funciona enquanto uma pessoa muda uma coisa por vez. Com várias pessoas, vários
serviços e o Dependabot abrindo Pull Requests toda semana, alguém acaba esquecendo um passo. Um
pipeline faz as mesmas verificações toda vez, na mesma ordem, e se recusa a entregar o que
falha nelas.
