# ADT_PY

`ADT_PY` e a reimplementacao em Python do Antenna Design Tool.

O projeto usa `PyQt6` para a interface e organiza o nucleo tecnico em modulos Python separados para:

- leitura de padroes HRP e VRP
- sintese 3D por painel e por arranjo
- calculo de diretividade 3D
- exportacao de padroes
- persistencia estruturada de projeto
- replicacao gradual da interface do ADT original

## Estrutura

- `main.py`: janela principal e orquestracao da UI
- `domain/`: modelos tipados de projeto, paineis, perdas e grupos de excitacao
- `app/`: servicos de montagem do projeto e integracao entre UI e solver
- `infra/`: persistencia e IO de projeto
- `models/antenna.py`: modelos de painel e arranjo
- `parsers/patterns.py`: leitura de arquivos de padrao HRP e VRP
- `solver/pattern_synthesis.py`: sintese 3D, soma coerente do arranjo e diretividade
- `solver/system_metrics.py`: metricas de sistema derivadas do padrao sintetizado
- `exports/pattern_exporters.py`: exportacao em texto, CSV, PRN e ATDI
- `widgets/`: widgets PyQt6 que reproduzem as areas funcionais do ADT
- `tests/`: testes automatizados de regressao e persistencia
- `test_parsing.py`: smoke test legado do parser e da sintese basica

## Dependencias

As dependencias Python estao em `requirements.txt`.

Instalacao recomendada:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execucao

Para abrir a interface:

```powershell
python main.py
```

Para rodar o teste basico de parsing e sintese:

```powershell
python test_parsing.py
```

Para rodar a suite automatizada:

```powershell
python -m unittest discover -s tests -v
```

## Estado atual

Hoje o projeto ja contem:

- shell principal da interface em PyQt6
- widgets separados para Design Info, Pattern Library, Antenna Design, plots e resumo
- pacotes separados para `domain`, `app`, `infra`, `models`, `parsers`, `solver`, `exports` e `widgets`
- parser inicial de arquivos HRP/VRP
- sintese 3D simplificada baseada em arrays complexos `numpy`
- exportadores basicos para formatos tabulares
- composicao de excitacao por painel, face e nivel na camada de projeto
- salvamento e abertura de projeto em formato `.adpy.json`

## Observacoes praticas

- o projeto nao versiona o `venv`
- os dados de padrao usados para testes podem ficar fora deste repo
- a pasta pai contem material de referencia da engenharia original, mas este repositorio descreve apenas o app Python
