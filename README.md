# RAVE Benchmark Lab

Laboratório experimental para comparar o RAVE com um agente individual controlado (Comparação A) e com o Open Deep Research da LangChain (Comparação B). Esta preparação não define perguntas oficiais, rubrica, avaliador nem executa benchmark.

## Estado

Estrutura, contratos e adaptadores iniciais preparados. A versão congelada do RAVE é `richardsilva-dev/project_RAVE`, branch `independent_research`, commit `d5a7b2397bc50796ab83ee22ed326fdc087b84b2` (12/11/2026). A documentação de implementação marca as execuções v3 anteriores como exploratórias; não reutilizá-las como resultados deste laboratório.

A execução preservada da Comparação A (`solo-5b3dc0590dfc`) foi concluída e permanece intacta como piloto de integração. Uma branch candidata do RAVE agora inclui orçamento global por execução, correções de parsing JSON, telemetria para falhas de leitura e limite de saída separado para síntese final; a suíte do GitHub Actions passou em 26 testes. O laboratório contém um executor protegido que reutiliza o resultado A e executa somente o RAVE após uma verificação de autenticação sem custo de pesquisa. Nenhuma nova chamada de pesquisa do RAVE foi feita. A Comparação B continua bloqueada: a auditoria do lock upstream apontou 89 vulnerabilidades conhecidas e dois status de pacotes arquivados; esse ambiente não foi instalado nem executado. Consulte [status](docs/IMPLEMENTATION_STATUS.md) e [auditoria](docs/DEPENDENCY_AUDIT.md).

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

## Primeiro piloto pareado A × RAVE

Com o artefato local `artifacts/runs/solo-5b3dc0590dfc` presente e `comparison_a/.env` preenchido com uma chave válida e os preços configurados, execute uma única vez:

```powershell
python scripts/run_rave_pilot.py --live
```

O executor preserva e reutiliza a execução A existente; não a executa novamente. Antes de qualquer pesquisa paga, faz uma chamada `GET /models` para validar a autenticação. Em caso de HTTP 401/403, encerra sem iniciar a pesquisa. O código RAVE é clonado para `.cache/project_RAVE` e fixado no commit documentado; o checkout local existente do usuário não é alterado. Os novos artefatos do par ficam em `artifacts/pairs/` e não são enviados ao Git.

## Status GitHub

Repositório remoto privado ativo. A branch `comparison-a-budget-and-methodology-hardening` contém as correções e o executor do piloto; os artefatos de execução permanecem locais e são ignorados pelo Git.
