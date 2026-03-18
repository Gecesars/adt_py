# ADT_PY

`ADT_PY` e a reimplementacao em Python do Antenna Design Tool.

O projeto usa `PyQt6` para a interface e organiza o nucleo tecnico em modulos Python separados para:

- leitura de padroes HRP e VRP
- sintese 3D por painel e por arranjo
- calculo de diretividade 3D
- exportacao de padroes
- replicacao gradual da interface do ADT original

## Estrutura

- `main.py`: janela principal e orquestracao da UI
- `core/antenna_models.py`: modelos de painel e arranjo, mais metricas do sistema
- `core/math_funcs.py`: sintese 3D, soma coerente do arranjo e diretividade
- `core/pattern_parser.py`: leitura de arquivos de padrao HRP e VRP
- `core/exporters.py`: exportacao em texto, CSV, PRN e ATDI
- `ui/`: widgets PyQt6 que reproduzem as areas funcionais do ADT
- `test_parsing.py`: smoke test do parser e da sintese basica

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

## Estado atual

Hoje o projeto ja contem:

- shell principal da interface em PyQt6
- widgets separados para Design Info, Pattern Library, Antenna Design, plots e resumo
- parser inicial de arquivos HRP/VRP
- sintese 3D simplificada baseada em arrays complexos `numpy`
- exportadores basicos para formatos tabulares

## Observacoes praticas

- o projeto nao versiona o `venv`
- os dados de padrao usados para testes podem ficar fora deste repo
- a pasta pai contem material de referencia da engenharia original, mas este repositorio descreve apenas o app Python
