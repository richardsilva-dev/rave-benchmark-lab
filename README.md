# RAVE Benchmark Lab

Laboratório para preparar uma comparação controlada entre o RAVE/Hive, um agente individual implementado aqui (Comparação A) e uma referência externa de pesquisa individual (Comparação B). Nesta etapa estamos preparando e protegendo os executores; **não estamos conduzindo o benchmark oficial**.

## Estado atual

RAVE permanece congelado em richardsilva-dev/project_RAVE, branch independent_research, commit d5a7b2397bc50796ab83ee22ed326fdc087b84b2. O repositório RAVE não foi modificado.

A Comparação A está implementada como agente sequencial e foi endurecida na branch sami-token-guard-searchclaw-audit: reserva prévia de tokens por tentativa, orçamento separado para pesquisas lógicas e chamadas HTTP, retries limitados, validação de saída, deduplicação de URLs, proveniência das citações e modelos fixos. O checkpoint 7c25f6d passou no CI: 58 testes, 10 verificações smoke offline e três JSON Schemas.

Open Deep Research permanece bloqueado pela auditoria do lock e por sua arquitetura supervisor/subagentes. SearchClaw também não foi aprovado após revisão de SSRF e falta de lock. Local Deep Research é o candidato externo mais promissor para a próxima rodada de hardening, mas ainda tem pontos pendentes e não foi instalado. Veja [revisão de referências externas](docs/EXTERNAL_REFERENCE_REVIEW.md) e [estado de implementação](docs/IMPLEMENTATION_STATUS.md).

## Estrutura

- [Comparação A — agente solo próprio](comparison_a/README.md)
- [Comparação B — referência externa sob revisão](comparison_b/README.md)
- [Arquitetura do laboratório](docs/ARCHITECTURE.md)
- [Protocolo de A](docs/COMPARISON_A_PROTOCOL.md) e [protocolo atual de B](docs/COMPARISON_B_PROTOCOL.md)
- [Mapeamento de modelos e ferramentas](docs/MODEL_AND_TOOL_MAPPING.md)
- [Política de segurança](docs/SECURITY_POLICY.md)
- [Revisão externa de ODR, SearchClaw e LDR](docs/EXTERNAL_REFERENCE_REVIEW.md)

## Segredos e execução

Cada candidato deve usar ambiente isolado e dependências fixadas. Copie o .env.example pertinente para .env e configure segredos localmente. Nunca registre ou envie chaves para o chat, GitHub, logs ou arquivos de execução versionados. Testes automatizados não fazem chamadas pagas; execução real exige ação explícita e limites declarados.
