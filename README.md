# RAVE Benchmark Lab

Laboratório experimental para comparar o RAVE com um agente individual controlado (Comparação A) e com o Open Deep Research da LangChain (Comparação B). Esta preparação não define perguntas oficiais, rubrica, avaliador nem executa benchmark.

## Estado

Estrutura, contratos e adaptadores iniciais preparados. A versão congelada do RAVE é `richardsilva-dev/project_RAVE`, branch `independent_research`, commit `d5a7b2397bc50796ab83ee22ed326fdc087b84b2` (12/11/2026). A documentação de implementação marca as execuções v3 anteriores como exploratórias; não reutilizá-las como resultados deste laboratório.

O repositório remoto privado foi criado e os commits de preparação estão publicados na branch `main`. A branch `sami-review-budget-guards` contém ajustes adicionais de orçamento, ainda pendentes de CI e revisão. O projeto não está pronto para bateria experimental. A Comparação A possui lockfile, ambiente isolado, auditoria sem achados conhecidos e 21 testes aprovados na revisão anterior. A auditoria do lock upstream da Comparação B apontou 89 vulnerabilidades conhecidas e dois status de pacotes arquivados; por segurança, esse ambiente não foi instalado nem executado. Consulte [status](docs/IMPLEMENTATION_STATUS.md) e [auditoria](docs/DEPENDENCY_AUDIT.md).

## Preparação

- [Comparação A](comparison_a/README.md)
- [Comparação B](comparison_b/README.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Protocolos](docs/COMPARISON_A_PROTOCOL.md) · [B](docs/COMPARISON_B_PROTOCOL.md)
- [Mapeamento](docs/MODEL_AND_TOOL_MAPPING.md)
- [Segurança](SECURITY.md) · [Política](docs/SECURITY_POLICY.md)
- [Status detalhado](docs/IMPLEMENTATION_STATUS.md)

Cada comparação deve usar seu próprio ambiente virtual. A Comparação B usa o `pyproject.toml` e `uv.lock` upstream dentro do submódulo. Não instale dependências no ambiente do RAVE.

## Segredos

Copie o `.env.example` da comparação desejada para `.env` e preencha localmente. Nunca registre chaves, resultados reais ou dados pessoais. O laboratório não inicia chamadas de API automaticamente.
