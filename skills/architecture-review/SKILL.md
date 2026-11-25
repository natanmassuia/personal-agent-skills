---
name: architecture-review
description: Review a codebase or change for architecture problems — overlapping responsibilities, wrong layering, tight coupling, leaky boundaries, and modules doing too much. Trigger with "architecture review", "revisão de arquitetura", "problemas de arquitetura", "acoplamento", "responsabilidades sobrepostas".
compatibility: opencode, claude, codex
---

# Architecture Review

## Propósito

Avaliar a **estrutura** do código (não bugs linha-a-linha): como as responsabilidades estão divididas, como as camadas conversam e onde o acoplamento vai doer na próxima mudança. Produz um relatório priorizado com evidência por arquivo e uma recomendação concreta para cada achado. Só reporta — não refatora sem o usuário pedir.

## Gatilhos

- "architecture review", "revisão de arquitetura"
- "problemas de arquitetura", "isso está bem arquitetado?"
- "acoplamento", "responsabilidades sobrepostas", "está acoplado demais?"

## Regras

- Reportar, não refatorar. Nenhuma edição de código sem pedido explícito.
- Cada achado aponta `arquivo:linha` que o comprova — sem "cheiro genérico".
- Separar **defeito de arquitetura** (vai custar caro adiante) de **preferência de estilo** (opinião). São decisões diferentes para quem lê.
- Respeitar as convenções que o projeto já tem (camadas, nomes, pastas). A régua é a coerência interna, não um padrão ideal externo.
- Não propor reescrita grande quando um ajuste localizado resolve.

## Eixos (sempre cobrir)

1. **Responsabilidades** — cada módulo/classe/arquivo tem um motivo único para mudar? Procurar o "God module" (faz I/O + regra de negócio + formatação), lógica de negócio vazando para controller/view, e a mesma responsabilidade espalhada em 3 lugares.
2. **Camadas e direção das dependências** — controller → service → repositório (ou equivalente do projeto) respeitado? Camada de baixo importando a de cima? Regra de negócio dependendo de framework/HTTP/ORM diretamente?
3. **Acoplamento** — módulos que só mudam juntos; import cruzado/ciclos; conhecimento de detalhe interno de outro módulo; "shotgun surgery" (uma mudança exige tocar N arquivos).
4. **Fronteiras e contratos** — tipos/DTOs do banco vazando até a UI; ausência de uma borda clara entre domínio e mundo externo (API, fila, equipamento); validação no lugar errado.
5. **Estado e fluxo de dados** — estado global/singleton escondido, fonte de verdade duplicada, dado que trafega mutável por várias camadas.
6. **Duplicação estrutural** — o mesmo fluxo reimplementado em módulos diferentes (sinal de abstração faltando — diferente de código copiado, que é o `codebase-audit`).

## Severidade

| Nível | Significado |
|---|---|
| Alto | Vai bloquear ou arriscar quebrar a próxima feature/manutenção; acoplamento que obriga mudança em cascata |
| Médio | Atrito real e recorrente, mas contornável; dívida que cresce |
| Baixo | Inconsistência pontual; melhora a clareza mas não trava nada |
| Info | Observação/alternativa de design, sem ação obrigatória |

## Processo

1. Delimitar o escopo (módulo, feature ou o projeto todo) com o usuário.
2. Mapear a estrutura real: pastas, camadas, pontos de entrada, quem importa quem.
3. Passar os 6 eixos acima, anotando evidência `arquivo:linha`.
4. Classificar por severidade e por "defeito vs preferência".
5. Ordenar por risco (não por facilidade de corrigir) e escrever o relatório.

## Saída

Relatório em `.dev-reports/architecture-review-<YYYY-MM-DD>.md`:

- **Resumo executivo**: total por severidade + o diagnóstico em 2–3 linhas.
- **Mapa da estrutura**: camadas/módulos e a direção das dependências (texto ou ascii).
- **Achados**: ordenados por risco, cada um com evidência `arquivo:linha`, o custo concreto ("na próxima vez que mexer em X, vai ter que…") e a recomendação (o que mudar, não só o que está errado).
- **Defeito vs preferência**: seções separadas.
- **Fora de escopo**: o que não foi avaliado e por quê.
