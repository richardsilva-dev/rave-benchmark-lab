# RAVE Benchmark Lab

Laboratório experimental para comparar o RAVE com um agente individual controlado (Comparação A) e com o Open Deep Research da LangChain (Comparação B). Esta preparação não define perguntas oficiais, rubrica, avaliador nem executa benchmark.

## Estado

Estrutura, contratos e adaptadores iniciais preparados. A versão congelada do RAVE é `richardsilva-dev/project_RAVE`, branch `independent_research`, commit `d5a7b2397bc50796ab83ee22ed326fdc087b84b2` (12/11/2026). A documentação de implementação marca as execuções v3 anteriores como exploratórias; não reutilizá-las como resultados deste laboratório.

O projeto não está pronto para bateria experimental: ambientes/lockfiles, instalação e integração real do Open Deep Research, auditoria de dependências e ensaios de fumaça ainda precisam ser concluídos. Os limites de custo/tempo/tokens permanecem intencionalmente indefinidos até um piloto.

## Preparação

- [Comparação A](comparison_a/README.md)
- [Comparação B](comparison_b/README.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Protocolos](docs/COMPARISON_A_PROTOCOL.md) · [B](docs/COMPARISON_B_PROTOCOL.md)
- [Mapeamento](docs/MODEL_AND_TOOL_MAPPING.md)
- [Segurança](SECURITY.md) · [Política](docs/SECURITY_POLICY.md)
- [Status detalhado](docs/IMPLEMENTATION_STATUS.md)

Cada comparação possui `pyproject.toml` próprio e deve usar seu próprio ambiente virtual. Não instale dependências no ambiente do RAVE.

## Segredos

Copie o `.env.example` da comparação desejada para `.env` e preencha localmente. Nunca registre chaves, resultados reais ou dados pessoais. O laboratório não inicia chamadas de API automaticamente.

## Status GitHub

Este diretório é o checkout local de preparação. A criação do repositório remoto privado requer uma operação GitHub que não está disponível na integração conectada nesta sessão; nenhuma publicação foi feita.
