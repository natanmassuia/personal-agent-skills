---
name: auditoria-seguranca-automacao-rede
description: Auditoria de segurança de código-fonte de sistema que automatiza equipamento de rede (FortiGate e FortiManager em especial, mas vale para MikroTik, Cisco e afins). Use quando pedirem para revisar, auditar ou avaliar a segurança do código, antes de colocar em produção, antes de dar acesso a mais gente, ou quando o sistema passar a empurrar configuração para firewall. Cobre token de API, credenciais, injeção de comando no CLI, risco de trancar o próprio acesso, identidade do alvo, autenticação e sessão, segredos, banco, deploy e CI.
---

# Auditoria de segurança de automação de rede

## A lente que orienta tudo

Um sistema que guarda credencial de firewall e empurra configuração **não guarda
"dados": guarda as chaves da rede**. Comprometer o sistema não é vazar um banco.
É ganhar acesso administrativo a todos os firewalls que ele alcança e, dali, à
rede inteira atrás deles.

Três consequências:

1. **Confidencialidade vale mais que disponibilidade.** O sistema cair por umas
   horas é incidente operacional; vazar token de API ou backup de configuração é
   incidente de todos os clientes e sites ao mesmo tempo.
2. **Desenhe para o atacante que já tem algum acesso.** "Pegou um dump do banco",
   "pegou o `.env`", "pegou um backup do servidor", "é um usuário comum logado",
   e não só "atacante anônimo na internet".
3. **O erro do próprio sistema também é ameaça.** Automação que empurra regra
   errada, para o firewall errado, ou que corta o próprio acesso de gerência,
   causa o mesmo estrago que um invasor, e sem ninguém perceber na hora.

## Quando usar

- Revisar o código antes de ir para produção ou antes de abrir para mais usuários.
- Antes de ligar qualquer função que **escreve** no equipamento (até então só lia).
- Depois de uma leva grande de código gerado por IA sem revisão linha a linha.
- Quando alguém perguntar "isso está seguro?": a resposta tem que vir com evidência.

## Como conduzir a auditoria

Siga nesta ordem. Não pule o passo 1: sem mapa, a revisão vira opinião.

1. **Mapear antes de julgar.** Liste como o sistema autentica usuários; onde
   ficam as credenciais e tokens dos firewalls; todos os pontos que falam com o
   equipamento (REST API, SSH, Telnet, FortiManager); como o comando ou a
   requisição é montado; onde estão banco, fila, logs e backups; como o sistema
   sobe (Docker, systemd, `npm run dev`?). Anote arquivo e linha de cada um.
   Se o material não tem git, registre o hash da árvore (ver o modelo de
   laudo): sem ele, o próximo laudo não tem com o que se comparar.
2. **Percorrer os eixos** da seção abaixo, cada um com evidência.
3. **Aprofundar nos arquivos de referência** conforme o que o mapa mostrou:
   - `references/fortigate.md`: **sempre**, porque é o eixo de maior estrago.
   - `references/fortimanager.md`: quando o sistema fala com a frota pelo
     FortiManager (JSON-RPC, ADOM, `/sys/proxy/json`).
   - `references/aplicacao.md`: login, sessão, senha, papéis, segredos, cripto.
   - `references/infra-e-ci.md`: banco, Docker, deploy, backup, CI.
4. **Executar o que der para executar**, sem tocar equipamento real (ver
   "Disciplina"). Ler o código não prova que ele se comporta como parece.
5. **Escrever o laudo** no formato de `references/modelo-de-laudo.md`.

## Os 7 eixos (sempre cobrir todos)

1. **Como o sistema alcança o firewall.** Token em cabeçalho ou na URL? TLS
   verificado ou `verify=False`? Host key SSH fixada ou `AutoAddPolicy`? O
   usuário de API no FortiGate ou no FortiManager tem perfil mínimo, só os ADOMs
   necessários e trusted hosts? → `fortigate.md`, `fortimanager.md`
2. **Injeção de comando.** Algum texto vindo de usuário, planilha, inventário ou
   até do próprio equipamento vira comando de CLI ou corpo de requisição sem
   validação estrita? Quebra de linha, aspas, `end`, `execute`? → `fortigate.md`
3. **Segurança da mudança.** Antes de escrever, o sistema confere que o alvo é o
   firewall certo (número de série)? Tira snapshot? Mostra diff? Tem rollback?
   Pode trancar a própria gerência? Em lote, para no primeiro erro?
   → `fortigate.md`, `fortimanager.md`
4. **Autorização por papel no servidor.** Cada rota que lê ou escreve confere o
   papel no backend, ou só "está logado"? Botão escondido no frontend não conta.
   Quem pode empurrar mudança e quem só pode ver? Se o sistema opera vários
   clientes, sites ou ADOMs, cada usuário só alcança os seus? → `aplicacao.md`
5. **Segredos.** Token, senha ou chave no código, no git (inclusive no
   histórico), no bundle do frontend, em log, em mensagem de erro? Cifrados em
   repouso no banco? A chave que cifra tem caminho de rotação? → `aplicacao.md`
6. **Autenticação e sessão.** Hash de senha forte, limite de tentativas, sessão
   que se revoga, troca de senha pedindo a senha atual, MFA que não é contornado
   pelo "esqueci a senha". → `aplicacao.md`
7. **Infra e cadeia de suprimentos.** Banco e Redis sem porta aberta, app que não
   roda como superusuário do banco, build de produção (não dev server), TLS,
   backup cifrado e restaurável, dependências com versão travada, varredura no
   CI. → `infra-e-ci.md`

## Disciplina (vale mais que o checklist)

- **Não destrutivo.** Nunca disparar automação contra firewall de produção para
  "testar". Nunca validar mudança de rede na máquina de produção. Se precisar
  exercitar, use FortiGate VM de laboratório ou um mock da API.
- **Validar executando, não lendo.** "A rota existe" e "os testes passam" não são
  evidência. Se o teste roda em SQLite e a produção é PostgreSQL, o teste não
  prova o SQL. Se der para chamar o endpoint num ambiente de teste, chame.
- **Não chamar design de bug.** Antes de escrever "defeito", pergunte: *para que
  condição este caminho foi desenhado?* Guardas e fallbacks costumam ser
  estreitos de propósito. Se a intenção não está no código nem na documentação,
  **pergunte ao autor** em vez de "consertar": consertar uma guarda pode virar
  regressão.
- **Perguntar em que camada a proteção existiria** antes de dizer que ela não
  existe. "Não tem backup", visto de dentro da VM, pode ser falso se o
  hypervisor faz snapshot. Registre o que você mediu e de onde.
- **Separar o ambiente da auditoria do sistema auditado.** Se uma instalação ou
  um teste falha só onde você está rodando (outro sistema operacional, outra
  versão da linguagem, sem rede), isso é limite da auditoria, não achado. Antes
  de classificar, confira o marcador de plataforma da dependência
  (`; platform_system == "Windows"`, `sys_platform`), os módulos que só existem
  num sistema (`fcntl`, `winreg`) e onde a CI roda (`runs-on`). Exemplo: o
  Bandit só exige `colorama` no Windows, então um lock gerado em Linux sem
  `colorama` está certo e só falha quando instalado no Windows. Registre como
  "a verificar" no ambiente da CI ou da produção, e não como defeito.
- **O material que você recebeu também é exposição.** Se o pacote auditado traz
  segredo vivo (chave privada, token, senha, `.env`, backup, histórico de
  conversa com IA contendo credencial), diga isso **no topo do laudo**: o
  material já foi compartilhado com quem audita, inclusive com o provedor da IA
  que está lendo agora. Recomende rotacionar, porque apagar o arquivo não
  desfaz o envio. Não abra nem reproduza o valor.
- **Mascarar segredo no laudo.** Descreva pelo comportamento ("token de API em
  texto no arquivo X, linha N"); nunca copie o valor, hash, e-mail ou IP real.
- **Veredito por evidência**, um por item: **atende / atende com ressalva / não
  atende / não se aplica / a verificar**, cada um com o arquivo:linha ou o
  comando que prova. "Atende com ressalva" exige a ressalva escrita na mesma
  linha. Não invente outros ("atende parcialmente", "não atende
  parcialmente"): se o item não se decide, é "a verificar" ou são dois itens.
  "A verificar" nunca vira "atende" por falta de tempo.
- **Ordenar por risco, não por esforço.** O conserto barato vai primeiro na
  execução, mas o laudo é lido de cima para baixo: o pior tem que estar em cima.
- **Separar segurança de continuidade.** Processo rodando na conta pessoal de
  alguém, um único dono da senha, nenhum backup: é risco real, mas de outra
  natureza. Vai numa seção própria.
- **Explicar o porquê.** Quem lê pode estar aprendendo. Cada achado diz o que um
  atacante (ou o próprio sistema) consegue fazer, em português claro, e não só o
  nome da CWE.

## O que esta skill não é

Não é pentest. É revisão de caixa branca feita por quem lê o código, com o viés
de quem vê o desenho por dentro. Quando o sistema for exposto fora da rede
interna, ou quando um cliente exigir, o caminho é teste independente, e este
laudo vira a entrada do escopo dele.
