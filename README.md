# RAVE Benchmark Lab

Laboratório experimental para preparar comparações entre o RAVE, um agente individual controlado (Comparação A) e uma referência externa de pesquisa (Comparação B). Esta etapa prepara os executores; não define perguntas oficiais, rubrica, avaliador nem executa benchmark.

## Estado

Repositório privado. A versão congelada do RAVE é `richardsilva-dev/project_RAVE`, branch `independent_research`, commit `d5a7b2397bc50796ab83ee22ed326fdc087b84b2`.

A Comparação A tem projeto/ambiente Python isolado e agente sequencial sem subagentes. A branch `sami-token-guard-searchclaw-audit` está adicionando reserva de tokens pré-chamada e avaliação de uma referência externa alternativa. Essas alterações ainda precisam passar pelo CI.

O Open Deep Research está pinado como submódulo, mas sua auditoria de lock reportou 89 advisories em 242 pacotes e dois status adversos de pacotes arquivados. Não foi instalado nem executado. SearchClaw está em avaliação preliminar, ainda sem lock/auditoria; não é uma referência aprovada. Consulte [estado](docs/IMPLEMENTATION_STATUS.md) e [auditoria ODR](docs/DEPENDENCY_AUDIT.md).

## Preparação

- [Comparação A](comparison_a/README.md)
- [Comparação B / Open Deep Research](comparison_b/README.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Protocolos A](docs/COMPARISON_A_PROTOCOL.md) e [B](docs/COMPARISON_B_PROTOCOL.md)
- [Mapeamento de modelos/ferramentas](docs/MODEL_AND_TOOL_MAPPING.md)
- [Política de segurança](docs/SECURITY_POLICY.md)

Cada comparação deve usar seu próprio ambiente virtual. A Comparação B só poderá ser instalada depois de passar por uma auditoria de dependências e revisão de segurança. Não instale dependências externas na Comparação A ou no ambiente do RAVE.

## Segredos

Copie o `.env.example` da comparação desejada para `.env` e preencha localmente. Nunca registre chaves, resultados reais ou dados pessoais. O laboratório não inicia chamadas de API automaticamente.
