---
name: codebase-audit
description: Audit a codebase for duplicated code, dead code, unnecessary dependencies, and redundant/overlapping features. Produces a prioritized cleanup report with file/line evidence. Trigger with "codebase audit", "auditar o código", "código morto", "código duplicado", "dependências desnecessárias", "funcionalidade redundante".
compatibility: opencode, claude, codex
---

# Codebase Audit

## Propósito

Encontrar **peso morto e repetição** no código: o que dá pra apagar ou unificar sem perder função. Produz um relatório priorizado com evidência por arquivo/linha e, para cada item, o que fazer (remover, unificar, ou confirmar uso antes de remover). Só reporta — não apaga nada sem o usuário pedir.

## Gatilhos

- "codebase audit", "auditar o código", "audita a base"
- "código morto", "dead code", "código duplicado"
- "dependências desnecessárias", "pacote sem uso"
- "funcionalidade redundante", "tem coisa repetida?"

## Regras

- Reportar, não deletar. Remoção só com pedido explícito.
- Cada achado com evidência `arquivo:linha` e **como foi verificado** (ex.: "sem referências em `grep`/imports").
- **"Sem referência" ≠ "morto" com certeza**: marcar como *a confirmar* o que pode ser usado por reflexão, string dinâmica, rota, DI, entrypoint, teste, build ou consumidor externo. Nunca afirmar "morto" sem ter procurado os usos.
- Não contar como duplicação o que é coincidência rasa (duas linhas iguais triviais). Duplicação que conta é lógica repetida que muda junto.
- Preservar o que o projeto precisa: validação em borda, tratamento de erro, acessibilidade, calibração de hardware.

## Checklist

### Código duplicado
- [ ] Mesma lógica (branch/loop/parser/cálculo) copiada em 2+ lugares que mudam junto
- [ ] Helpers/utilitários equivalentes reinventados em módulos diferentes
- [ ] Blocos de UI/estilo repetidos que pediam um componente

### Código morto
- [ ] Funções/classes/constantes exportadas ou locais sem nenhum uso
- [ ] Imports não usados; variáveis atribuídas e nunca lidas
- [ ] Branches inalcançáveis; flags/feature-toggles sempre no mesmo valor
- [ ] Arquivos/assets órfãos (nenhum import/referência)
- [ ] Rotas/endpoints/handlers que ninguém chama

### Dependências desnecessárias
- [ ] Pacotes em `package.json` (ou equivalente) sem import real no código
- [ ] Dependência pesada usada por 1–2 linhas que a stdlib/plataforma já faz
- [ ] Duplicatas funcionais (duas libs para a mesma coisa)
- [ ] `devDependencies` vs `dependencies` trocadas

### Funcionalidade redundante
- [ ] Dois caminhos/telas/fluxos que fazem a mesma coisa
- [ ] Configuração/opção que nunca varia na prática
- [ ] Camada de abstração/wrapper com um único implementador que não agrega

## Severidade

| Nível | Significado |
|---|---|
| Alto | Peso/risco real: dep sem uso que amplia superfície, duplicação que já causou divergência de comportamento |
| Médio | Limpeza que reduz atrito e confusão de manutenção |
| Baixo | Cosmético; remover melhora clareza |
| Info | Candidato *a confirmar* (possível uso dinâmico/externo) |

## Processo

1. Delimitar escopo com o usuário (repo todo, um pacote, uma pasta).
2. Levantar entrypoints, rotas, exports públicos e consumidores externos — a fronteira do que "pode ser chamado de fora".
3. Rodar o checklist com buscas reais (imports, referências, `grep`), registrando como cada item foi verificado.
4. Classificar por severidade; separar o que é **seguro remover** do que é **a confirmar**.
5. Ordenar por valor da limpeza e escrever o relatório.

## Saída

Relatório em `.dev-reports/codebase-audit-<YYYY-MM-DD>.md`:

- **Resumo executivo**: total por categoria/severidade + estimativa grosseira do que dá pra apagar.
- **Seguro remover**: itens com evidência `arquivo:linha` e a verificação que prova o não-uso.
- **A confirmar antes de remover**: itens que parecem mortos mas têm caminho dinâmico/externo possível — com a pergunta a responder.
- **Duplicação para unificar**: pares/grupos, com a sugestão de onde centralizar.
- **Dependências**: tabela pacote → usado? → ação.
- **Fora de escopo**: o que não foi varrido e por quê.
