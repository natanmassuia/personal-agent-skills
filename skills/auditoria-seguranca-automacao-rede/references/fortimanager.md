# FortiManager: quando o sistema fala com a frota por ele

Use este arquivo quando a automação fala com os FortiGates **através do
FortiManager** (JSON-RPC em `/jsonrpc`, ADOM, pacote de política,
`/sys/proxy/json`). Ele complementa o `fortigate.md`, não o substitui: injeção
de comando, TLS, backup e segredo valem do mesmo jeito.

A lente muda de escala. O token do FortiManager **não abre um firewall: abre a
frota inteira** que ele gerencia. Um erro de alvo deixa de afetar um site e
passa a afetar um ADOM inteiro, ou todos.

> Confira contra a versão de FortiManager em uso. Os números de versão abaixo
> vêm da documentação e de avisos de segurança da Fortinet; onde houver dúvida,
> o laudo marca "a verificar".

## 1. Usuário de API no FortiManager (lado do equipamento)

Peça ao autor a saída, **sem a chave**, de `show system admin user <usuário>` e
do perfil associado.

Desde o FortiManager 7.2.2 existe usuário de API com chave fixa:
`config system admin user` → `set user_type api`, e a chave é gerada com
`execute api-user generate-key <usuário>`. Antes disso, só havia login por
sessão. O FortiManager Cloud não aceita chave e usa outro fluxo de login.

| Verificar | Bom | Red flag |
|---|---|---|
| Perfil | perfil próprio da integração, só com o que ela usa | `Super_User`, que **libera todos os ADOMs automaticamente** |
| ADOMs | só os ADOMs que a integração precisa ("Specify") | todos os ADOMs, sem motivo |
| `rpc-permit` | `read` para coleta e relatório; `read-write` só no usuário que escreve | `read-write` em tudo. Com `none`, o usuário nem entra na API |
| Trusted hosts | `trusthost1..10` só com o IP do servidor da automação | ausente ou `0.0.0.0/0` |
| Um usuário por sistema | cada integração com seu usuário e sua chave | uma chave para todos os scripts |

Desde o 7.2.1 o perfil pode variar por ADOM, o que permite, por exemplo,
leitura em todos e escrita em um.

**A chave não expira sozinha.** Ela só muda quando alguém gera outra. Pergunte:
existe procedimento de rotação? Quem gera, onde ela fica, como o sistema troca
sem parar?

## 2. Autenticação (lado do código)

- **Chave no cabeçalho**: `Authorization: Bearer <chave>`. A chave na URL
  (`?access_token=`) deixa de ser aceita a partir do 7.4.7 e do 7.6.2; antes
  disso funcionava, e o vazamento em log de proxy é o mesmo do FortiGate.
- **Login por sessão** (`sys/login/user`): a sessão devolvida vale até o
  `sys/logout`. Procure o logout num `finally`. Sem ele, cada execução deixa uma
  sessão administrativa viva no FortiManager.
- Se o sistema usa usuário e senha de **administrador humano** para a
  integração, a trilha do FortiManager mostra aquela pessoa fazendo tudo, e a
  senha dela vira segredo de máquina.

## 3. ADOM e o "delegado confuso"

Este é o achado típico de FortiManager e **não aparece lendo só o código**.

A integração costuma ter acesso a vários ADOMs (às vezes todos). Os usuários do
sistema, não. Se o sistema recebe o ADOM ou o dispositivo como parâmetro e só
confere que ele **existe**, qualquer usuário do sistema opera em qualquer ADOM
com o poder da integração. O FortiManager não vai barrar: quem pede é a
integração, que pode.

O que verificar:
- Existe, no sistema, a relação **usuário → ADOMs permitidos**, conferida no
  servidor a cada leitura e escrita? Ou o ADOM vem do frontend e é só validado
  contra a lista do FortiManager?
- Se os ADOMs separam **clientes**, a ausência dessa relação é falha de
  autorização por objeto (BOLA), gravidade alta. Se todos os usuários podem
  mesmo ver tudo, escreva a pergunta para o autor em vez de cravar o achado.
- Não trate grupo de dispositivos como fronteira de segurança sem testar na
  versão em uso: há relato documentado de usuário restrito a um grupo que
  conseguiu escrever fora dele.

## 4. `/sys/proxy/json`: o FortiManager como trampolim

O proxy repassa uma chamada da REST API do FortiOS para os FortiGates
gerenciados. O campo `target` aceita um dispositivo, um grupo, e o grupo
`All_FortiGate`, que pode alcançar **todos os dispositivos de todos os ADOMs**
numa chamada só. O tempo limite padrão é de 60 s.

- **Quem escolhe o `target`?** Se ele vem do usuário, ou é montado a partir de
  texto livre, um valor trocado vira fan-out para a frota. O alvo deve ser
  resolvido pelo servidor a partir do ID que o usuário pode operar (seção 3).
- **Escrita pelo proxy muda o FortiGate por fora do banco do FortiManager.** O
  equipamento passa a divergir do que o FortiManager tem, e o status vira "Out
  of sync" ou "Auto-updated", dependendo do auto-update. Pergunte ao autor:
  qual é a fonte da verdade, o FortiManager ou o FortiGate? Uma instalação
  seguinte pelo FortiManager pode desfazer o que a automação fez, ou o
  contrário.
- `resource` (o caminho da API do FortiOS) e `action` devem ser escolhidos pelo
  servidor, de uma lista fechada, como o verbo no CLI (`fortigate.md`, item 4).
- A reversão automática documentada pela Fortinet é a da **instalação** (seção 5).
  Uma escrita pelo proxy não é instalação: não conte com essa reversão ali sem
  testar em laboratório.

## 5. Segurança da mudança no FortiManager

O `fortigate.md`, item 5, continua valendo. No FortiManager há peças próprias:

| Pergunta | O que procurar |
|---|---|
| **Workspace** | Com workspace ligado, escrever exige travar o ADOM (lock), gravar (commit) e destravar (unlock). O unlock está num `finally`? Trava esquecida bloqueia os outros administradores. Commit sem revisão é aplicar direto. |
| **Prévia da instalação** | A API gera prévia do que vai ser instalado (install preview). O sistema mostra essa prévia a um humano antes do install, ou instala direto? |
| **Status antes de instalar** | O sistema confere o status de configuração do dispositivo antes? "Out of sync" quer dizer que alguém mexeu direto no FortiGate e o FortiManager não sabe; instalar por cima é decisão, não detalhe. "Conflict" quer dizer que a última instalação falhou. |
| **Dá para voltar?** | O histórico de revisões do FortiManager permite reverter para uma revisão anterior e reinstalar. O sistema registra a revisão de antes e de depois de cada mudança, ligada à execução? |
| **Pode trancar a gerência?** | A instalação tem rede de segurança própria. O FortiManager envia os comandos da mudança e os que a desfazem; o FortiGate aplica só em memória, testa o túnel FGFM e, se ele cair, aplica o desfazer. Se mesmo assim não reconectar, o FortiGate pode reiniciar para a configuração salva, mas só com `set rollback-allow-reboot enable` em `config system dm`, no FortiManager. No exemplo da Fortinet, o FortiGate tenta reconectar por 900 s antes de voltar. **Limite:** isso protege o caminho até o FortiManager. Uma mudança que derruba outra coisa (VPN do site, acesso dos usuários) com o FGFM de pé não volta sozinha. Plano fora de banda continua necessário. |
| **Em lote** | Instalar num grupo ou ADOM inteiro é rollout em lote: ondas e parada no primeiro erro real. |

## 6. O próprio FortiManager como alvo

O FortiManager guarda as configurações e as credenciais da frota. Ele é o alvo
de maior valor da rede, acima de qualquer firewall isolado.

- **Versão.** O CVE-2024-47575 ("FortiJump", aviso FG-IR-24-423) era falta de
  autenticação no daemon `fgfmd`, que fala com os FortiGates. Foi explorado
  ativamente e está na lista KEV da CISA. Afetava FortiManager 6.2.0–6.2.12,
  6.4.0–6.4.14, 7.0.0–7.0.12, 7.2.0–7.2.7, 7.4.0–7.4.4 e 7.6.0. Pergunte a
  versão e compare com os avisos atuais da Fortinet, não só com este.
- **Exposição.** A interface administrativa e a porta do FGFM (TCP 541) estão
  abertas para onde? Gerência só pela rede de gerência.
- **Backup do FortiManager** contém a frota inteira: mesmo tratamento do backup
  de configuração (`fortigate.md`, item 6), com cifra e restauração ensaiada.
