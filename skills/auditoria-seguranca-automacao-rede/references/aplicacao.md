# Aplicação: usuários, papéis, sessão, segredos e cripto

Vocabulário de referência: **OWASP ASVS 5.0, nível 2** (lista verificável,
requisito por requisito). Os capítulos mais úteis aqui são V6 autenticação, V7
sessão, V8 autorização, V9 tokens, V11 criptografia, V14 proteção de dados e V16
log. O OWASP Top 10 e o CWE Top 25 servem de lente de triagem por cima.

## 1. Autorização por papel (V8)

- Cada rota do backend confere o papel **no servidor**. Procure rotas que só
  dependem de "usuário logado" e não do papel.
- Red flag: `if (user.role === "admin")` no React ou no Vue decidindo acesso.
  Isso só esconde o botão; a chamada direta à API continua passando.
- No mínimo: quem **lê**, quem **opera** (empurra mudança) e quem **administra**
  (usuários, tokens, integrações). Cadastro de token ou credencial de firewall é
  só para admin.
- Teste concreto: logar como usuário comum e chamar direto (curl, Postman) a
  rota de admin e a de "aplicar mudança". O esperado é 403.
- Recurso de um cliente ou site é visível ou alterável por usuário de outro?
  (BOLA: trocar o `id` na URL e ver o que volta.)

## 2. Senha de usuário (V6, V11)

| Verificar | Bom | Red flag |
|---|---|---|
| Algoritmo | argon2id, bcrypt, ou PBKDF2-HMAC-SHA256 com **pelo menos 600.000** iterações, com sal aleatório | MD5, SHA-1 ou SHA-256 puro, sem sal, texto puro, cifra reversível |
| Comparação | tempo constante (`hmac.compare_digest`) | `==` em hash ou token |
| Usuário inexistente | mesmo tempo e mesma mensagem de "senha errada" (hash fictício) | "usuário não encontrado", que entrega a lista de logins |
| Tentativas | limite no login, no reset e no MFA | ilimitado |

**Bloqueio de conta é decisão, não detalhe:** "5 erros travam por 5 minutos"
permite a qualquer um manter o admin trancado errando de propósito uma vez por
minuto. Atraso progressivo é uma alternativa. Qualquer que seja a escolha, ela
deve estar escrita, e alguém tem que ser **avisado** de uma rajada de falhas.

## 3. Sessão (V7, V9)

- O logout invalida a sessão no servidor? A troca de senha derruba as outras
  sessões? Se o token só expira pelo relógio, um token roubado vale até expirar
  e não há como derrubá-lo.
- Expiração por **inatividade**, além da absoluta.
- Cookie de sessão com `HttpOnly`, `Secure` e `SameSite`. Token em
  `localStorage` fica exposto a qualquer XSS.
- JWT: algoritmo fixo no servidor (nunca aceitar o `alg` que vem no token, nunca
  `none`).

## 4. Fluxos que viram tomada de conta

Três falhas comuns que, juntas, fecham uma cadeia:
- **Troca de senha ou de e-mail sem pedir a senha atual.** Quem rouba a sessão
  troca a senha e o e-mail, e o dono legítimo fica de fora.
- **"Esqueci a senha" que pula o MFA.** Quem controla a caixa de e-mail entra
  sem o segundo fator.
- **Token de reset na query string** (`?token=...`). Fica no log do nginx, no
  histórico do navegador e em proxies. Mande no corpo do POST.

E mais uma: token de uso único (reset, convite, OTP) guardado em claro no banco.
Guarde só o hash SHA-256.

## 5. Segredos no código e no repositório (V13, V14)

- Procure `password=`, `token`, `api_key`, `secret`, `Bearer `, IPs de
  equipamento, URL com usuário e senha. Rode `gitleaks detect` no repositório
  **e no histórico** (um segredo apagado no commit seguinte continua no git).
- O `.env` está no `.gitignore`? Existe um `.env.example` sem valores reais?
- Variável `VITE_*`, `NEXT_PUBLIC_*` ou `REACT_APP_*` vai para o **navegador**.
  Token ali é token público.
- **Migration ou seed que cria usuário real**: uma conta de admin com senha fixa
  no código nasce igual em toda instalação. O primeiro admin deve ser criado por
  comando, com senha digitada, e o comando recusa se já houver admin.
- Senha padrão do tipo `admin/admin`, `changeme` ou a "senha da casa" ainda
  ativa em algum lugar.
- **Histórico de conversa com IA.** Conversas exportadas, prompts salvos,
  `HISTORICO*.md`, notas de sessão de agente: é comum colar token ou senha no
  chat "para a IA testar", e o arquivo vai junto no pacote ou no commit. Trate
  como qualquer outro segredo no repositório.
- **Pacote de entrega ou de migração** com chave privada, credencial temporária
  ou a chave de cifra **ao lado** do backup cifrado. A chave junto do cofre
  anula o cofre.

## 6. Cifra de segredo em repouso (V11, V14)

Para token de API e senha de firewall que o sistema precisa **usar** (não dá
para guardar só o hash, tem que ser reversível):
- Cifra autenticada: Fernet, AES-GCM, ChaCha20-Poly1305. Nunca AES-ECB, nunca
  base64 "como cifra", nunca XOR caseiro.
- **De onde vem a chave?** Se é `sha256(SECRET_KEY)` de uma frase escolhida por
  uma pessoa, a derivação é fraca. A chave deve ser material aleatório (32 bytes)
  ou derivada com uma KDF de verdade.
- **A mesma chave assina a sessão e cifra a credencial?** Então não dá para
  trocar uma sem perder a outra, e trocar a chave torna ilegível todo segredo
  salvo. Resultado: **se a chave vazar, não há resposta a incidente** além de
  recadastrar tudo. Pergunta para o laudo: "existe procedimento de rotação? já
  foi ensaiado?". Direção boa: envelope encryption com `key_version` na linha.
- **Cifrar a coluna de senha e deixar o backup de configuração em claro na
  tabela ao lado anula metade da proteção**: quem tem o dump lê a mesma classe
  de segredo.

## 7. Log e alerta (V16)

- Existe log de evento de segurança? Login, falha, MFA, troca de senha, mudança
  de papel, criação de token e **cada mudança empurrada para firewall**.
- **Registrar não é avisar.** O ASVS pede registrar; não pede alertar. Um sistema
  pode registrar tudo e ninguém saber de uma rajada de falhas de login ou de uma
  conta promovida a admin. Pergunte: quem recebe aviso de quê?
- O log não pode conter segredo: token, senha, corpo de requisição com PSK,
  configuração completa.
- A trilha resiste ao próprio admin? Se é uma tabela comum, quem tem o banco
  reescreve o histórico. Exportação append-only ou encadeamento por hash resolvem.
- A retenção está definida? (O log cresce para sempre, ou some cedo demais?)

## 8. Frontend e erros

- `dangerouslySetInnerHTML`, `v-html` ou `innerHTML` com dado de usuário ou **de
  equipamento** (descrição de interface é texto controlado por terceiros).
- Resposta de erro com stack trace, caminho absoluto ou SQL: sinal de modo debug
  ou dev server em produção.
- `/docs`, `/openapi.json`, `/swagger` ou o `/admin` do framework acessíveis de
  fora.
