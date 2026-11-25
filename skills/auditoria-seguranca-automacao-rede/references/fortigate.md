# FortiGate: como o sistema alcança e altera o equipamento

É o eixo de maior estrago. Os exemplos são em Python (`requests`, `paramiko`,
`netmiko`), mas a ideia vale para qualquer linguagem.

> Confira os detalhes de CLI e API contra a versão de FortiOS em uso: nomes de
> opção e comportamento mudam entre versões. Onde houver dúvida, o laudo marca
> "a verificar".

## 1. Usuário de API no FortiGate (lado do equipamento)

O código pode estar perfeito e o token ainda dar poder demais. Peça ao autor a
saída (sem o token) de `show system api-user` e `show system accprofile`.

Desde o FortiOS 7.0.13, a Fortinet indica o **REST API admin** (token) como a
forma suportada e recomendada de autenticar na API. Código que faz login por
usuário e senha de administrador e guarda cookie de sessão está no caminho
antigo.

| Verificar | Bom | Red flag |
|---|---|---|
| Perfil (`accprofile`) | um perfil por função; coleta e backup com **somente leitura** | `super_admin` ou `prof_admin` para tudo |
| Trusted hosts (`config trusthost`) | só o IP do servidor da automação | `0.0.0.0 0.0.0.0` ou ausente |
| VDOM | só os VDOMs necessários | todos, sem motivo |
| Um usuário por sistema | cada integração com seu próprio api-user | um token compartilhado por tudo e todos |
| Interface de gerência | HTTPS de admin só na rede de gerência | admin HTTPS ou SSH aberto na WAN |

**Por que trusted host importa tanto:** já houve falha de bypass de autenticação
justamente na interface administrativa do FortiOS. O CVE-2022-40684 (FortiOS
7.0.0 a 7.0.6 e 7.2.0 a 7.2.1) foi explorado ativamente, e restringir o acesso a
IPs confiáveis estava entre as mitigações. Com trusted host restrito e gerência
fora da WAN, uma falha dessas não alcança o equipamento. Um token vazado de um
api-user com trusted host restrito também vale muito menos.

## 2. Token de API (lado do código)

O FortiOS aceita o token no cabeçalho e na URL. Use o cabeçalho.

```python
# RUIM: token na URL -- fica em log de proxy, de nginx, de exceção, no histórico
requests.get(f"https://{fw}/api/v2/cmdb/firewall/address?access_token={token}")

# BOM: token no cabeçalho
requests.get(f"https://{fw}/api/v2/cmdb/firewall/address",
             headers={"Authorization": f"Bearer {token}"}, timeout=30)
```

Verifique também:
- Token cifrado em repouso no banco, e não em texto puro numa coluna `api_key`.
- Token **nunca** devolvido pela API do próprio sistema depois de salvo (a tela
  mostra `••••`, e editar significa substituir).
- Token fora de log: procure `logger.*(headers`, `print(response.request`,
  `repr(session)` e logs de exceção que despejam a requisição inteira.
- Existe procedimento para **rotacionar** (gerar novo, trocar, revogar o antigo)
  sem parar o sistema? Se não existe, um vazamento não tem resposta.

## 3. TLS e host key: com quem o sistema está falando?

O FortiGate costuma vir com certificado autoassinado, e o atalho clássico é:

```python
requests.get(url, verify=False)          # RED FLAG
urllib3.disable_warnings()               # quase sempre anda junto
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())   # idem, no SSH
```

Isso aceita **qualquer** servidor do outro lado. Quem estiver no meio do caminho
recebe o token (ou a senha SSH) e pode devolver respostas falsas.

O meio-termo que funciona na prática é **TOFU com pinning** (confiar no primeiro
uso e fixar):
- No primeiro contato bem-sucedido, gravar a impressão digital (SHA-256) do
  certificado ou da host key daquele equipamento.
- Nas conexões seguintes, comparar. Se divergir: registrar evento, avisar alguém
  e exigir aceite humano explícito (com quem aceitou e quando).
- Decisão consciente: bloquear ou só avisar na divergência? Bloquear tudo para
  numa troca legítima de equipamento; só avisar deixa passar ataque. Para quem
  **escreve** no firewall, bloquear a escrita e avisar costuma ser o equilíbrio.
- Melhor ainda, quando possível: certificado emitido por uma CA interna e
  `verify` apontando para ela.

## 4. Injeção de comando no CLI

É o vetor de maior estrago. Todo texto que vira comando de FortiOS é suspeito,
inclusive o que vem de planilha, de inventário e **do próprio equipamento** (o
campo `comment` de um objeto pode ter sido escrito por outra pessoa).

```python
# RUIM: input do operador concatenado num script de CLI
cmd = f"""config firewall address
edit "{nome}"
set subnet {ip} {mascara}
set comment "{comentario}"
next
end"""
```

Se `comentario` vier como `x"\nend\nconfig system admin\nedit invasor\n...`, a
quebra de linha encerra o bloco e o resto vira comando, com o privilégio do
usuário da automação.

Defesa, em ordem de preferência:
1. **Usar a REST API com corpo JSON** em vez de montar texto de CLI. O JSON
   separa dado de comando por construção.
2. Se tiver que usar CLI, **validar cada campo pelo tipo**, com lista do que é
   permitido (nunca com lista do que é proibido):
   - IP ou rede: `ipaddress.ip_network(valor, strict=True)`, nunca regex caseira.
   - Nome de objeto: `^[A-Za-z0-9_.-]{1,63}$` (ajuste ao limite do FortiOS).
   - Texto livre (comentário): recusar `\r`, `\n`, `"` e caracteres de controle;
     limitar o tamanho.
   - Porta: inteiro entre 1 e 65535.
3. **Nunca** permitir que o usuário escolha o verbo (`execute`, `diagnose`,
   `config system ...`). O sistema escolhe o comando; o usuário só preenche
   valores validados.
4. Testar com o texto hostil real (quebra de linha, aspas, `end`, unicode) como
   caso de teste automatizado.

A mesma lógica vale para `shell=True`, `os.system`, `subprocess` com string
montada e SQL concatenado (`f"SELECT ... WHERE nome = '{x}'"` → use ORM ou
parâmetro).

## 5. Segurança da mudança (o sistema como ameaça)

Aqui o risco não é o invasor: é a automação fazendo estrago sozinha.

| Pergunta | O que procurar no código |
|---|---|
| **É o firewall certo?** | Antes de escrever, consultar `/api/v2/monitor/system/status` e comparar o **número de série** (e o hostname) com o cadastro. IP muda, e equipamento troca de lugar. Sem essa conferência, o sistema empurra a regra para quem estiver naquele IP. |
| **O que muda?** | Gera diff ou prévia e mostra para um humano aprovar? Ou aplica direto? |
| **Dá para voltar?** | Snapshot da configuração **antes** de cada mudança, guardado (cifrado) e associado à mudança. |
| **Pode trancar a gerência?** | Mexe em interface, rota, política que cobre a gerência, admin ou trusted host? Isso exige proteção extra: `cfg-save revert` (abaixo) ou, pelo FortiManager, a reversão da instalação (`fortimanager.md`, item 5). |
| **Em lote?** | Empurra para N firewalls de uma vez? Precisa de rollout em ondas (um, depois poucos, depois o resto) e **parar no primeiro erro**, em vez de "continuar e relatar no fim". |
| **Quem fez?** | Cada mudança registra o **usuário do sistema** que pediu, o alvo, o diff e o resultado. No FortiGate o log só mostra o api-user da automação; a trilha de quem foi de verdade tem que estar no sistema. |
| **Testado onde?** | Existe FortiGate VM de laboratório ou mock? "Testei no firewall do cliente" não é ambiente de teste. |

### `cfg-save revert`: o "commit confirmed" do FortiOS

É o mecanismo do FortiOS mais próximo do `commit confirmed` do Junos: a mudança
vale na hora, mas só fica gravada depois de confirmada. Se ninguém confirmar a
tempo, o equipamento volta para a última configuração salva.

```
config system global
    set cfg-save revert
    set cfg-revert-timeout 600
end
```

- Modos de `cfg-save`: `automatic` (padrão: grava ao executar), `manual` (vale,
  mas só grava com `execute cfg save`) e `revert` (manual, e volta sozinho quando
  o tempo acaba). Desde o 7.0.2 aparece na GUI como "Configuration save mode".
- Confirmar é rodar `execute cfg save` dentro do prazo (`cfg-revert-timeout`,
  padrão de 600 s).
- **A volta é por reinício.** O Junos só desfaz o commit; o FortiGate recarrega a
  configuração salva **reiniciando**. Em HA, todos os membros reiniciam, e o
  secundário não assume no lugar. O rollback derruba o site, ou o cluster, por
  alguns minutos: é rede de segurança para não perder o equipamento, não um
  desfazer barato.
- **A opção é global.** Vale para todo administrador, inclusive para quem mexe
  pela GUI: quem altera e esquece de salvar provoca um reinício. Ligar isso é
  decisão de operação, combinada com a equipe, e não detalhe do código.
- Em `manual` e `revert`, mudança não salva também se perde em qualquer
  reinício, inclusive numa queda de energia.

O que verificar no código:
- A automação que mexe em interface, rota, política de gerência, admin ou
  trusted host usa esse mecanismo ou um equivalente?
- Se usa, o fluxo certo é: aplicar → **testar o acesso por uma conexão nova**
  (não pela sessão que já estava aberta) → só então `execute cfg save`. Salvar
  logo depois de aplicar, sem testar, anula a proteção.
- Por qual caminho? A documentação descreve o prazo pela sessão administrativa
  ociosa e a confirmação pelo CLI. Não há na documentação um endpoint da REST API
  para confirmar, nem o que conta como "sessão" numa chamada com token. Se a
  automação usa REST, o comportamento é **a verificar em laboratório**: aplicar
  por REST, não confirmar e ver se volta.
- Equipamento gerenciado pelo FortiManager tem outra rede de segurança, a da
  instalação (`fortimanager.md`, item 5). Combinar as duas é coisa para testar em
  laboratório antes.

## 6. Backup de configuração e segredo

O backup do FortiGate contém segredo: senhas de usuários, PSK de VPN,
passphrases de chaves privadas, senha de HA, communities SNMP, segredos de
RADIUS e LDAP.

As senhas aparecem como `ENC ...`, e **`ENC` não é uma cifra em que se possa
confiar**. O CVE-2019-6693 (aviso FG-IR-19-007, na lista de vulnerabilidades
exploradas da CISA) mostrou que o FortiOS cifrava esses campos com uma **chave
fixa no firmware**: quem tem o arquivo de backup decifra. A própria Fortinet
recomenda proteger o backup com senha.

O FortiOS tem `set private-data-encryption enable` (em `config system global`)
para usar uma chave por equipamento. Cuidados medidos na documentação:
- A partir do 7.6.1 a chave é gerada aleatoriamente; antes, era digitada
  (32 dígitos hexadecimais).
- **Um backup feito com uma chave não restaura depois que a chave muda.**
  Desligar e religar a opção gera chave nova.
- Em cluster HA, a chave não é sincronizada para as unidades secundárias.

O que verificar no sistema:
- **Não "conserte" removendo os segredos do backup.** Backup sem segredo não é
  restaurável: devolver aquela configuração ao equipamento deixa VPN e admins
  quebrados. O remédio é proteger o **acervo** (cifra em repouso, quem alcança a
  tabela ou a pasta), não empobrecer o backup.
- Arquivo de backup no disco com permissão `0600`, pasta `0700`, fora da pasta
  servida pelo servidor web e fora do git.
- Backup enviado por e-mail, Telegram ou Slack em texto: red flag.

## 7. Se o sistema usa LLM (Claude, ChatGPT etc.)

- **O LLM é índice, não canal.** Configuração completa, com segredo, não vai
  para o contexto de um modelo externo. Mande só o necessário, com segredo
  redigido por fabricante (`set password ENC ...` → `set password <REDIGIDO>`).
- **A saída de um LLM nunca vira comando direto no firewall.** Ela passa pela
  mesma validação do item 4 e por aprovação humana. Texto vindo do equipamento
  (`comment`, `description`, nome de objeto) pode conter instrução maliciosa para
  o modelo (injeção de prompt).
- Escada segura de autonomia: **ler → propor → executar com confirmação**.
  Pular um degrau é decisão explícita, registrada.
