# Infra, deploy, banco, backup e CI

Lentes: **CIS Benchmarks** (Docker, PostgreSQL, nginx) para a infra; **NIST
SSDF** (SP 800-218) para o processo de construir e liberar.

## 1. Superfície de rede

| Verificar | Bom | Red flag |
|---|---|---|
| Porta do banco e do Redis | sem `ports:` no compose; só a rede interna do Docker | `5432:5432` ou `6379:6379` publicados |
| Redis | com senha (`--requirepass`) | sem senha; `redis-cli ping` responde `PONG` sem autenticar |
| Backend | atrás do proxy, ou em `127.0.0.1:porta` | `0.0.0.0:8000` direto |
| Frontend | build de produção servido por nginx ou caddy | `npm run dev`, `vite`, `flask run`, `--reload` em produção |
| TLS | HTTPS com redirecionamento da porta 80 | HTTP puro com login (a senha trafega em claro) |
| CORS | lista explícita de origens | `*` ou regex que libera uma rede inteira |
| Cabeçalhos | HSTS, CSP, `X-Frame-Options: DENY`, `nosniff`, Referrer-Policy | nenhum |

A ordem de gravidade costuma ser: **TLS > limite de tentativas no login > build
de produção > cabeçalhos**.

## 2. Docker e a rede de gerência

**Uma rede do Docker pode colidir com a rede real.** O Docker escolhe uma
sub-rede privada sozinho; se ela cair dentro da faixa de gerência ou da frota
(por exemplo, um bridge `/16` criado em cima da faixa de gerência), a rota do
host muda e o SSH do servidor cai, inclusive para quem está tentando consertar.

- Compare `docker network inspect` e `ip route` com as faixas reais da empresa.
- Fixe `default-address-pools` em `/etc/docker/daemon.json` numa faixa que não
  existe na rede (por exemplo, os blocos de documentação da RFC 5737) e com
  máscara pequena.
- Nunca declare `subnet:` no compose dentro das faixas da empresa.
- **Nunca valide mudança de rede ou hardening na máquina de produção.** Use uma
  VM descartável.

Outros pontos de Docker:
- Imagem base fixada por digest (`FROM python:3.12-slim@sha256:...`), e não só
  por tag.
- Container rodando como root sem necessidade; `privileged: true`;
  `/var/run/docker.sock` montado (equivale a root no host).
- **Imagem não é código-fonte.** Reverter o código não reverte a imagem já
  construída, e um `docker compose up -d` recria o container a partir da
  imagem. Confira o que está rodando, não o que está no git.
- `restart: unless-stopped`: sem isso, um reboot do host deixa tudo fora do ar.

## 3. Banco de dados (PostgreSQL)

Três padrões herdados da imagem oficial que ninguém revisa porque "já funciona":

1. **App conectando como superusuário.** Se a role da aplicação é superusuária,
   qualquer SQL injection futura vira execução de comando no servidor do banco
   (`COPY ... TO PROGRAM`). Confira com:
   `SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles;`
   Direção: uma role que **migra** (dona do schema) e outra que **serve** (só
   SELECT, INSERT, UPDATE e DELETE).
2. **`trust` no `pg_hba.conf`** para conexão local: quem chega ao container vira
   qualquer role sem senha.
3. **Sem log de conexão** (`log_connections = off`): não há como responder "quem
   conectou, de onde e quando".

E também:
- Senha do banco real, e não `postgres`/`postgres` ou o nome do projeto.
- Testes rodando só em SQLite quando a produção é PostgreSQL: o teste passa e o
  SQL quebra em produção. Tenha pelo menos um subconjunto rodando contra
  PostgreSQL real.

## 4. Backup do próprio sistema

O banco deste sistema é **o cofre de credenciais da rede**. O backup dele é tão
sensível quanto o banco.

- Existe backup agendado (cron, timer do systemd), ou só um comando manual na
  documentação?
- **Cifrado** antes de gravar (por exemplo, GPG com chave pública; a privada fica
  com o dono, fora do servidor). Assim, quem invade o servidor não lê os backups.
- A chave que cifra os segredos da aplicação (`SECRET_KEY` ou equivalente)
  precisa ser recuperável junto. Sem ela, o backup restaura um banco com todas
  as credenciais ilegíveis.
- **Restauração ensaiada**, de verdade, num ambiente separado. Backup nunca
  restaurado é hipótese.
- Procure dumps esquecidos: `find / -name "*.sql" -o -name "*.dump"`, pastas
  `backups/` dentro do projeto, permissão `0644` (todo usuário do host lê).
- `.env` com permissão `0644` é outro clássico.
- Cópia fora do mesmo storage (offsite). Backup no mesmo disco ou cluster não
  protege contra a perda do disco ou do cluster.

## 5. Cadeia de suprimentos e CI

| Portão | Ferramenta típica | Observação |
|---|---|---|
| Dependências Python com CVE | `pip-audit` | `pip check` mede compatibilidade, **não** vulnerabilidade |
| Dependências JS com CVE | `npm audit` | |
| Análise estática | Bandit (Python), Semgrep, CodeQL | comece reprovando só severidade alta com confiança alta |
| Segredo commitado | Gitleaks, TruffleHog | rode uma vez no histórico inteiro, depois só nos commits novos |
| Imagem Docker | Trivy, Grype | use `--ignore-unfixed`, senão o portão nasce vermelho para sempre |
| Versões travadas | lockfile com hash (`pip install --require-hashes`, `package-lock.json`) | |
| Actions do GitHub | fixadas por SHA completo, e não por `@v4` | |

**O que faz um portão apodrecer:** portão sem válvula de escape vira portão
desligado. Toda exceção precisa ser **nomeada, justificada e datada** (por
exemplo, `.trivyignore` com comentário dizendo por quê e até quando). "Desligar
a regra" globalmente, nunca.

Vale também perguntar **em que camada** cada componente roda: um CVE no Node só
importa em produção se o Node roda em produção, e não só no build.

## 6. Continuidade (seção separada no laudo)

Não é defeito de segurança, mas é risco real:
- Sistema rodando da pasta pessoal ou na conta de um usuário nominal (morre
  quando a conta for desativada).
- Um único dono de senha, token ou chave, sem custódia combinada.
- Nenhuma documentação de como subir de novo num servidor novo.
- Ninguém recebe alerta quando o backup ou a automação falham.
