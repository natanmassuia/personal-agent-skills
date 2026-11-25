# Modelo de laudo

Escreva em português claro. Quem lê pode estar aprendendo: cada achado explica o
que dá para fazer com ele, e não só o nome técnico.

```markdown
# Laudo de segurança: <nome do sistema>

Data: <AAAA-MM-DD> · Commit ou versão auditada: <hash ou tag; sem git, o hash da árvore>
Escopo: <o que foi lido; o que ficou de fora e por quê>
Método: leitura de código + <o que foi executado, e onde>. Nenhuma chamada a
equipamento de produção.

> **Segredo vivo no material auditado** (só se houver): <o que foi achado, por
> localização, sem o valor>. Este material já foi enviado para a auditoria,
> inclusive para o provedor da IA. Rotacione: apagar o arquivo não desfaz o envio.

## Resumo

<3 a 5 linhas: o tamanho do risco hoje, os 2 ou 3 achados que importam e por
onde começar. Sem jargão.>

## Mapa do sistema

| Componente | Onde (arquivo:linha) | Observação |
|---|---|---|
| Autenticação de usuário | | |
| Credenciais e tokens de firewall | | |
| Pontos que falam com o equipamento | | |
| Montagem de comando ou requisição | | |
| Banco, fila, logs, backups | | |
| Como sobe em produção | | |

## Achados (ordenados por risco)

### A1: <título curto> · Gravidade: Crítica | Alta | Média | Baixa

- **Onde:** `caminho/arquivo.py:123`
- **O que acontece:** <o vetor concreto: quem, fazendo o quê, consegue o quê>
- **Por que importa aqui:** <ligação com "guardar as chaves da rede">
- **Correção:** <acionável, com um exemplo curto se ajudar; o mecanismo pelo nome, com o custo>
- **Referência:** <ASVS Vx / CWE-nnn / documento ou aviso do fabricante; nunca a própria skill>
- **Esforço:** pequeno | médio | grande

<... um bloco por achado ...>

## Os 7 eixos

| Eixo | Veredito | Evidência |
|---|---|---|
| 1. Alcance do firewall (token, TLS, api-user) | atende / atende com ressalva / não atende / não se aplica / a verificar | arquivo:linha |
| 2. Injeção de comando | | |
| 3. Segurança da mudança | | |
| 4. Autorização por papel | | |
| 5. Segredos | | |
| 6. Autenticação e sessão | | |
| 7. Infra e cadeia de suprimentos | | |

## A verificar

<o que não deu para concluir só com o código, e o que a pessoa precisa rodar ou
mostrar para fechar; por exemplo, a saída de `show system api-user` sem o token.>

## Continuidade (não é segurança, mas é risco)

<conta pessoal, dono único de segredo, backup não ensaiado, nenhum alerta...>

## Por onde começar

<ordem sugerida de execução: primeiro o que é barato E grave, depois o caro e
grave, depois o resto. No máximo 5 itens: lista longa não se executa.>

## O que já está bom

<reconhecer o que está certo, com evidência. Ajuda a não desfazer sem querer.>
```

## Regras do laudo

- Nenhum segredo, token, hash, e-mail ou IP real copiado. Descreva pelo
  comportamento e pela localização.
- Gravidade pelo estrago possível neste sistema, e não pela nota genérica da
  CWE. Um `verify=False` num script de laboratório e um `verify=False` no caminho
  que empurra regra para 200 firewalls não são a mesma coisa.
- "A verificar" é honesto; "atende" sem evidência não é.
- Só os cinco vereditos da tabela. "Atende com ressalva" nomeia a ressalva.
- Sem git, identifique a versão pelo hash da árvore, rodado na raiz do que foi
  auditado, e anote quantos arquivos entraram:
  `find . -type f ! -path './.git/*' -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum`
- Se o achado depende de uma intenção que você não conhece, escreva a pergunta
  para o autor em vez de presumir defeito.
- **Correção que não diz qual mecanismo não é acionável.** "Implementar um fluxo
  de reversão" não diz o que fazer. Se os arquivos de referência trazem o
  mecanismo, ele vai pelo nome, com o custo e o limite. No FortiGate, por
  exemplo, `cfg-save revert` volta por reinício e vale para todos os
  administradores; a reversão da instalação do FortiManager não cobre escrita
  pelo `/sys/proxy/json`. Se nenhum mecanismo serve, diga isso e por quê.
- **A referência é a fonte, não esta skill.** Quem lê o laudo não tem a skill.
  Cite a ASVS, a CWE ou o documento do fabricante de onde o fato veio.
