# ADT_PY Roadmap

## Objetivo

Este documento consolida:

- o que o ADT original em C# realmente faz
- o que o `ADT_PY` atual ja cobre
- o que ainda falta para chegarmos a uma versao Python melhor que a original
- a ordem recomendada de implementacao

As referencias tecnicas principais desta analise sao:

- `C:\Users\geral\Downloads\Antenna Design Tool (ADT) V1.5.3 Test version - Copia - Copia\Antenna Design Tool (ADT) V1.5.3 Test version\ADT.md`
- `C:\Users\geral\Downloads\Antenna Design Tool (ADT) V1.5.3 Test version - Copia - Copia\Antenna Design Tool (ADT) V1.5.3 Test version\ADT_PSEUDOCODE.md`
- os fontes recuperados em `.recovered\reactor-src`, `.recovered\reactor-funcs`, `.recovered\reactor-formfuncs` e `.recovered\reactor-hpat-vpat`

## 1. O ADT original, em termos de produto

O ADT original nao e apenas um viewer de HRP/VRP. Ele combina cinco camadas que se alimentam entre si:

1. cadastro do projeto e do sitio
2. biblioteca de paineis e padroes unitarios
3. geometria e excitacao do arranjo
4. solver 3D coerente no dominio complexo
5. pos-processamento de engenharia, comparacao, memoria, specs e exportacao

Os mecanismos centrais recuperados do produto original sao:

- composicao hierarquica de excitacao por painel, face e nivel
- configuracao HRP/VRP por painel com regras de `Config 0..5`
- tilt mecanico vertical projetado por azimute
- fusao complexa `HRP x VRP` por painel
- soma coerente de todos os paineis no dominio complexo
- diretividade 3D integrada sobre a esfera
- calculos de ERP, compensacao, field strength e power density
- exportacao para varios formatos de engenharia

## 2. O que o `ADT_PY` atual ja tem

Estado real da base Python:

- `main.py` ja reproduz a janela principal e a navegacao basica
- `models/antenna.py` ja tem um modelo inicial de painel e arranjo
- `parsers/patterns.py` ja le arquivos HRP e VRP
- `solver/pattern_synthesis.py` ja calcula:
  - padrao 3D de painel unico
  - soma do arranjo
  - diretividade 3D
  - um deslocamento de fase espacial simplificado
- `solver/system_metrics.py` ja calcula:
  - diretividade
  - angulos de maximo
  - system gain simplificado
  - ERP simplificado
- `widgets/` ja cobre a maior parte da casca funcional da UI
- exportadores iniciais ja existem para `TXT`, `CSV`, `PRN` e `ATDI`
- o fluxo de `Calculate 3D Pattern` ja roda ponta a ponta com arquivos reais

Em outras palavras: o `ADT_PY` ja tem uma espinha dorsal funcional, mas ainda nao tem a fidelidade de engenharia do ADT original.

## 3. Comparacao direta: original vs Python

### 3.1 Solver e modelo de dominio

O original possui:

- `LibraryPanel` com selecao de painel padrao por banda/polarizacao/frequencia
- `AntPanel` completo com `Config`, `Level`, `Face`, `Input`, `Libpanelnumber`
- `Pattern3D` com campo complexo por amostra angular
- regras de excitacao hierarquicas:
  - potencia individual
  - potencia por face
  - fase individual
  - fase por face
  - fase por nivel
- regras `Config 0..5` para inversao e referencia de fase
- tilt mecanico projetado por azimute
- perda de feeder por tipo, comprimento e frequencia

O Python atual possui:

- `AntennaPanel` simples com `power`, `phase`, `tilt`, `face_angle`, `x/y/z`
- `ArrayDesign` com uma lista plana de paineis
- leitura direta de arquivos HRP/VRP
- deslocamento espacial simplificado com `apply_panel_phase_shifts`
- solver 3D simplificado sem modelo explicito de biblioteca

Gap principal:

- o Python hoje resolve a matematica base do arranjo, mas ainda nao modela corretamente a semantica de engenharia do ADT.

### 3.2 Geometria do arranjo

O original possui:

- Geometry Builder
- coordenadas polares e cartesianas
- rotacao global do arranjo
- cogging
- tilt mecanico com reprojecao fisica
- niveis, faces, inputs e face letters

O Python atual possui:

- tabela de arranjo com colunas compatveis com a UI
- parsing basico da tabela para uma lista de paineis
- preview 3D de torre ainda ilustrativo

Gap principal:

- a UI existe, mas a geometria nao esta ligada a um motor de dominio equivalente ao original.

### 3.3 Biblioteca de paineis e padroes

O original possui:

- ate 4 slots de biblioteca
- painel padrao ou custom
- escolha de HRP/VRP por banda, polarizacao e frequencia
- dimensoes fisicas e espacamento por tipo de painel
- relacao de potencia por diretividade horizontal

O Python atual possui:

- 4 grupos visuais de pattern library
- caminho de HRP/VRP por pattern
- propriedades ainda tratadas como inputs simples

Gap principal:

- falta o catalogo real de paineis e a logica de configuracao automatica do padrao unitario.

### 3.4 Pos-processamento e engenharia

O original possui:

- HRP/VRP com cortes reais do padrao 3D
- memoria de traces
- specs de HRP/VRP
- beam shaping com sintese de fases
- compensation sweep
- field strength / exposure
- blackspot viewer
- video de animacao VRP

O Python atual possui:

- plots basicos de HRP e VRP
- dialogos iniciais para exposure, blackspot e distance/bearing
- widget visual para beam shape
- widget visual para compensation

Gap principal:

- varios modulos existem apenas como shell de UI, sem a matematica original por baixo.

### 3.5 Persistencia e interoperabilidade

O original possui:

- persistencia completa de projeto `.ant`
- specs `.spc`, `.spcsv`, `.antr`
- exportacao multipla para ecossistemas externos
- geracao de PDF/doc/layout

O Python atual possui:

- exportacao tabular inicial
- sem projeto salvo estruturado
- sem formatacao de intercambio de alta fidelidade

Gap principal:

- ainda nao existe um contrato de dados forte nem uma camada de persistencia robusta.

## 4. Diagnostico: onde o `ADT_PY` esta mais fraco hoje

As maiores lacunas, em ordem de risco tecnico, sao:

1. modelo de dominio simplificado demais
2. solver ainda sem fidelidade completa ao original
3. UI muito mais avancada que a camada de negocio
4. ausencia de persistencia formal de projeto
5. falta de testes de regressao fisica e numerica

Traduzindo: hoje o projeto corre o risco de parecer pronto visualmente antes de estar certo do ponto de vista de engenharia.

## 5. Como fazer o app Python ficar melhor que o original

Nao devemos apenas "copiar o WinForms". A oportunidade e usar o conhecimento recuperado para construir uma arquitetura superior.

### 5.1 Melhorias de arquitetura

Objetivo:

- separar claramente `domain`, `application`, `infrastructure` e `ui`

Melhor que o original porque:

- o ADT antigo concentra estado demais no `MainForm`
- no Python podemos ter um nucleo testavel sem UI
- a UI deixa de ser dona da regra de negocio

### 5.2 Melhorias de modelo de dados

Objetivo:

- introduzir modelos tipados para:
  - `Project`
  - `Site`
  - `LibraryPanel`
  - `ArrayPanel`
  - `GroupExcitation`
  - `Pattern1D`
  - `Pattern3D`
  - `ExportRequest`

Melhor que o original porque:

- reduz acoplamento por grids
- melhora serializacao
- facilita batch processing e API futura

### 5.3 Melhorias de solver

Objetivo:

- portar o solver original com fidelidade matematica
- encapsular cada etapa em funcoes puras

Melhor que o original porque:

- o solver fica testavel por unidade
- abre caminho para vetorizacao pesada com `numpy`
- permite usar `numba` ou GPU no futuro se necessario

### 5.4 Melhorias de usabilidade

Objetivo:

- refazer a experiencia de projeto com menos friccao

Melhor que o original porque:

- podemos ter:
  - autosave
  - undo/redo
  - validacao inline
  - presets
  - diff entre projetos
  - wizard de geometria
  - graficos mais claros

### 5.5 Melhorias operacionais

Objetivo:

- tornar o app auditavel e confiavel

Melhor que o original porque:

- teremos:
  - testes automatizados
  - snapshots numericos
  - CI
  - empacotamento moderno
  - logs estruturados
  - modo headless para calculo em lote

## 6. Arquitetura alvo recomendada

Estrutura sugerida:

```text
adt_py/
  app/
    services/
    use_cases/
  domain/
    models/
    enums/
    formulas/
    validation/
  infra/
    io/
    persistence/
    exporters/
    catalogs/
  ui/
    main_window/
    widgets/
    viewmodels/
  tests/
    unit/
    integration/
    regression/
    golden/
```

### Regras da arquitetura

- UI nao calcula formula de engenharia
- parser nao decide regra de dominio
- exportador nao busca estado da UI
- solver recebe modelos completos e devolve resultados completos
- toda etapa de calculo relevante precisa ter teste numerico

## 7. Roadmap recomendado

### Fase 0. Estabilizacao da base

Objetivo:

- preparar o projeto para crescer sem caos

Entregas:

- remover restos de estrutura antiga (`core/`, `ui/` legados no disco)
- introduzir `tests/` de verdade
- configurar `pytest`, `ruff`, `black` e `mypy`
- separar dados de exemplo e fixtures
- definir convencoes de nomes e unidades

Critico porque:

- sem isso, qualquer port do solver vira manutencao cara.

### Fase 1. Modelo de dominio correto

Objetivo:

- substituir os dicionarios e tabelas soltas por modelos claros

Entregas:

- `Project`
- `SiteConfig`
- `LibraryPanel`
- `ArrayPanel`
- `HorizontalGroup`
- `VerticalGroup`
- `PatternSample1D`
- `PatternField3D`

Critico porque:

- e a base para tudo o que vem depois.

### Fase 2. Persistencia de projeto

Objetivo:

- ter um formato moderno de projeto antes de expandir funcionalidades

Entregas:

- `project.json` versionado
- importador do estado atual da UI
- exportador/importador de projeto
- migration system por versao de schema

Melhor que o original:

- usar `json` claro internamente, com opcao de importar/exportar formatos legados depois.

### Fase 3. Biblioteca de paineis real

Objetivo:

- reproduzir corretamente o comportamento de biblioteca do ADT

Entregas:

- catalogo local de paineis padrao
- indexacao por banda e polarizacao
- escolha automatica de arquivos por frequencia
- modelo de dimensoes, espacamento e power ratio

Critico porque:

- hoje o usuario ainda informa caminhos de arquivo de forma manual demais.

### Fase 4. Solver fiel ao original

Objetivo:

- portar o pipeline tecnico completo

Entregas:

- `find_library_power_ratio`
- `compose_panel_excitation`
- `configure_single_panel_hrp`
- `configure_single_panel_vrp`
- `project_mechanical_tilt_by_azimuth`
- `build_single_panel_3d`
- `sum_array_complex_field`
- `extract_hrp_cut`
- `extract_vrp_cut`
- `compute_3d_directivity`
- `compute_feeder_loss`
- `compute_result_summary`

Critico porque:

- esta e a fase que transforma o app em ferramenta de engenharia confiavel.

### Fase 5. Geometria e layout de arranjo

Objetivo:

- portar o comportamento mecanico do ADT, mas com UX melhor

Entregas:

- geometry builder real
- coordenadas polares/cartesianas
- rotacao global
- cogging
- tilt mecanico aplicado sobre a geometria
- vinculacao do layout 3D com os dados reais do arranjo

Melhor que o original:

- preview 3D interativo com selecao de painel e edicao direta.

### Fase 6. HRP/VRP e ferramentas de projeto

Objetivo:

- reconstruir o ambiente de analise do engenheiro

Entregas:

- plots HRP/VRP com cortes reais do padrao 3D
- marcadores de beam tilt e maximos
- normalizacao configuravel
- memory traces
- overlays de spec
- animacao VRP

Melhor que o original:

- comparacao lado a lado
- bookmarks
- exportacao direta do que esta na tela

### Fase 7. Modulos de engenharia complementar

Objetivo:

- portar os modulos que hoje ainda sao placeholders

Entregas:

- beam shaping real
- compensation sweep real
- field strength / exposure real
- blackspot heatmap com controles
- network/cable set

Critico porque:

- esses modulos sao parte do valor tecnico do produto, nao detalhes perifericos.

### Fase 8. Exportacao e interoperabilidade

Objetivo:

- atingir compatibilidade operacional

Entregas:

- exportadores fiis para `PAT`, `CSV`, `ATDI`, `PRN`, `NGW3D`, `EDX`
- relatorios PDF
- exportacao de layout
- pacote de resultados do projeto

Melhor que o original:

- exporters isolados, testados e reutilizaveis
- modo headless para lote e integracao CI

### Fase 9. Produto superior ao original

Objetivo:

- ir alem do port

Entregas:

- autosave e recovery
- undo/redo
- validacao forte de entradas
- calculo em lote por frequencia
- linha do tempo de cenarios
- comparacao entre projetos
- plugin system para exporters e catalogos
- interface mais limpa e menos dependente de grids

## 8. Ordem de implementacao de maior retorno

Se o objetivo e ganhar velocidade sem perder rigor, a ordem ideal e:

1. dominio e persistencia
2. solver fiel ao original
3. geometria real do arranjo
4. plots e ferramentas de projeto
5. modulos complementares
6. exportacao completa
7. refinamentos de produto

Essa ordem evita o erro de investir em UI sofisticada em cima de um nucleo ainda incompleto.

## 9. Backlog inicial concreto

Sprint 1:

- criar modelos tipados de projeto
- mover calculo para um servico de dominio
- criar fixtures de padroes conhecidos
- criar testes de regressao numerica para diretividade e ERP

Sprint 2:

- portar `Power_final_i` e `Phase_final_i` com grupos horizontal/vertical
- portar `Config 0..5`
- portar `FindPowerRatio`
- validar contra casos de referencia do ADT

Sprint 3:

- portar `ConfigHPattern`
- portar `ConfigVPattern_ADT`
- portar tilt mecanico por azimute
- validar cortes HRP/VRP contra a base C#

Sprint 4:

- geometry builder real
- rotacao, cogging e tilt
- vincular layout 3D aos dados do arranjo

Sprint 5:

- beam shape real
- compensation real
- specs e memory traces

Sprint 6:

- persistencia de projeto
- exportadores de engenharia
- pacote de release executavel

## 10. Criterios de pronto

Uma fase so deve ser considerada pronta quando tiver:

- comportamento conferido contra a base C# recuperada
- testes automatizados
- validacao numerica com tolerancia definida
- UI integrada ao caso de uso real
- documentacao curta e objetiva

## 11. Recomendacao final

O caminho certo nao e continuar expandindo widgets isolados.

O caminho certo e:

1. congelar a UI atual como casca provisoria
2. reconstruir o nucleo de dominio e solver com fidelidade
3. religar a UI modulo a modulo sobre esse nucleo
4. usar essa nova base para entregar um produto mais moderno, testavel e confiavel que o WinForms original

Se seguirmos essa ordem, o `ADT_PY` deixa de ser um port visual e vira uma plataforma de engenharia de arranjos de antena de fato.
