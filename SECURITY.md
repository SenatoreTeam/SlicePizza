# Security policy / Política de segurança

## English

SlicePizza handles customers' names, phones and addresses, so security reports get priority.

**Supported versions.** Only the newest version ([`releases.toml`](releases.toml)) receives fixes. Production runs it.

**Reporting a vulnerability.** Please **do not open a public issue**. Report it privately through [GitHub's private vulnerability reporting](https://github.com/SenatoreTeam/SlicePizza/security/advisories/new): say what you found, how to reproduce it, and the version (shown in the footer of the site and in `/api/health`). You will get an answer within 7 days. Once a fix is released, the advisory is published with credit to you, unless you prefer otherwise.

**Scope.** The code in this repository: the API, the worker, the site and the kitchen board, the Docker images and the pipeline. The server they run on is the server owner's: see [docs/SECRETS.md](docs/SECRETS.md) and [docs/adr/0016-server-monitoring.md](docs/adr/0016-server-monitoring.md).

**What we already do.** Images are scanned for known vulnerabilities and for secrets before they are published, the whole Git history is scanned for secrets, dependencies are pinned with hashes and updated through Dependabot, actions and base images are pinned by commit or digest, and orders are rate-limited ([ADR 0021](docs/adr/0021-hardening.md)). Personal data is replaced after 12 months ([ADR 0023](docs/adr/0023-retention-of-personal-data.md)).

**A customer's question about their data** is not a vulnerability: see [docs/PRIVACY-REQUESTS.md](docs/PRIVACY-REQUESTS.md).

## Português

O SlicePizza guarda nomes, telefones e endereços de clientes, então relatos de segurança têm prioridade.

**Versões com suporte.** Só a versão mais nova ([`releases.toml`](releases.toml)) recebe correções. A produção roda ela.

**Como relatar uma vulnerabilidade.** Por favor, **não abra uma issue pública**. Relate em particular pelo [relato privado de vulnerabilidades do GitHub](https://github.com/SenatoreTeam/SlicePizza/security/advisories/new): diga o que achou, como reproduzir e a versão (aparece no rodapé do site e em `/api/health`). Você terá uma resposta em até 7 dias. Quando a correção sair, o aviso é publicado com o seu crédito, a menos que prefira o contrário.

**Escopo.** O código deste repositório: a API, o worker, o site e o painel da cozinha, as imagens Docker e a pipeline. O servidor onde rodam é do dono do servidor: veja [docs/SECRETS.md](docs/SECRETS.md) e [docs/adr/0016-server-monitoring.md](docs/adr/0016-server-monitoring.md).

**O que já fazemos.** As imagens são varridas atrás de vulnerabilidades conhecidas e segredos antes de publicar, todo o histórico do Git é varrido atrás de segredos, as dependências têm versão e hash fixos e são atualizadas pelo Dependabot, ações e imagens base são fixadas por commit ou digest, e os pedidos têm limite por endereço ([ADR 0021](docs/adr/0021-hardening.md)). Os dados pessoais são trocados depois de 12 meses ([ADR 0023](docs/adr/0023-retention-of-personal-data.md)).

**Uma dúvida de cliente sobre os próprios dados** não é uma vulnerabilidade: veja [docs/PRIVACY-REQUESTS.pt-BR.md](docs/PRIVACY-REQUESTS.pt-BR.md).
