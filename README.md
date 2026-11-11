# Juridico.Code

> **O "COBOL do Direito": Linguagem colaborativa, auditável e interpretada com Máquinas de Estados Finitos (FSM) para contratos e instrumentos legais.**

---

Instrumentos contratuais tradicionais em formato de texto estático são propensos a ambiguidades, contradições lógicas, inadimplências não monitoradas e falta de determinismo operacional. O **Juridico.Code** soluciona esse gargalo ao introduzir uma linguagem declarativa (`.jur`), um motor de verificação estática de conformidade legal/patrimonial e um ambiente interativo (CLI + Dashboard Web) para simular transições de estado, auditar cláusulas e certificar contratos digitalmente.

---

## 🌐 Idiomas / Languages

- [Português (Brasil)](README.md)
- [English](docs/readme/README_en.md)

---

## 🏷️ Badges

[![Versão](https://img.shields.io/badge/versão-1.0.0-blue?style=flat-square)](https://github.com/Juridicode/Juridicode/releases)
[![Licença](https://img.shields.io/badge/licença-MIT-yellow?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)

---

## 🧭 Sumário

- [Início Rápido](#-início-rápido)
- [Como Funciona](#-como-funciona)
- [Recursos e Capacidades](#-recursos-e-capacidades)
- [Casos de Uso e Demonstrações](#-casos-de-uso-e-demonstrações)
- [Perguntas Frequentes (FAQ)](#-perguntas-frequentes-faq)
- [Documentação](#-documentação)

---

## 🚀 Início Rápido

### Pré-requisitos
- **Python**: versão `>= 3.10`
- **Node.js**: versão `>= 18.x` (para o dashboard web)
- **Git** e ambiente Windows (ou compatível com terminal bash/cmd)

### Instalação
Clone o repositório, instale as dependências e configure o comando `juris` no sistema:

```bash
git clone https://github.com/Juridicode/Juridicode.git
cd Juridicode
pip install -r requirements.txt
python build_installer.py
```
*(No Windows, você também pode executar diretamente o `Instalar.bat` ou utilizar a interface visual através de `python installer_gui.py`)*

### Exemplo de Uso
> **Qual é a principal tarefa que você deseja automatizar ou investigar?**  
> *Interpretar, validar contradições lógicas e visualizar a Máquina de Estados de um contrato de compra e venda imobiliária.*

```bash
juris examples/compra_imovel.jur
```

---

## ⚙️ Como Funciona

1. **Análise Léxica e Sintática (`Lexer` & `Parser`)**: O código `.jur` é transformado em uma Árvore Sintática Abstrata (AST) validando a gramática declarativa jurídica.
2. **Avaliação Semântica e Anti-Contradição (`Evaluator`)**: O motor analisa regras patrimoniais e artigos de lei (como o Art. 381 do Código Civil sobre confusão entre credor e devedor).
3. **Máquina de Estados Finitos (FSM)**: Os ciclos de vida contratuais (`RASCUNHO`, `ATIVO`, `FINALIZADO`, `VENCIDO`) transitam apenas mediante satisfação rigorosa de requisitos e assinaturas.
4. **Interface e Dashboard em Tempo Real**: O comando CLI inicializa o servidor de serviços FastAPI e direciona o usuário ao visualizador React com REPL, simulação de eventos e exportação certificada.

---

## 📋 Recursos e Capacidades

| Categoria / Componente | O que a ferramenta produz ou entrega | Pré-requisitos ou Dependências |
| :--- | :--- | :--- |
| **Engine do Interpretador Jurídico** | Lexer, Parser com geração de AST e Avaliador de Tipos Jurídicos | Python 3.10+ |
| **Detector de Contradições e Conformidade** | Alertas e bloqueios contra violações de preceitos legais (ex: credor igual a devedor) | Python, Regras do Código Civil integradas |
| **Máquina de Estados Contratual (FSM)** | Ciclo de vida determinístico do contrato orientado por eventos e transições | Definições `TRANSIÇÃO` e `REQUER` no arquivo `.jur` |
| **Serviços Backend & Compilação** | API REST para compilação, validação de cláusulas e geração de PDF assinado/certificado | FastAPI, Uvicorn, ReportLab |
| **CLI Global (`juris`)** | Comando de terminal para validação estática e abertura automática no navegador | Windows PATH ou shell configurado |
| **Dashboard e Visualizador Web** | Interface interativa com simulador de transições, REPL e painel de status do contrato | React, Vite, Node.js 18+ |

---

## 💡 Casos de Uso e Demonstrações

- **Compra e Venda Imobiliária Determinística**: Modelagem de entrada, parcelamento, quitação e cláusulas moratórias de atraso com validação condicional automática.  
  *Arquivo:* [`examples/compra_imovel.jur`](examples/compra_imovel.jur)
- **Detecção de Nulidades e Contradições**: Bloqueio de termos contratuais inválidos, como autofinanciamento nulo ou sobreposições incompatíveis de obrigações.  
  *Arquivo:* [`examples/contrato_com_contradicao.jur`](examples/contrato_com_contradicao.jur)
- **Contrato de Prestação de Serviços Continuados**: Gestão de entregas parciais e encerramento determinístico com base em milestones.  
  *Arquivo:* [`examples/prestacao_servicos.jur`](examples/prestacao_servicos.jur)

---

## ❓ Perguntas Frequentes (FAQ)

**1. Quais sistemas operacionais e plataformas são suportados?**  
O motor Python e a API FastAPI funcionam em qualquer ambiente multiplataforma (Windows, Linux, macOS). O instalador automático de atalhos e executáveis de sistema foi otimizado nativamente para ambiente Windows (`.bat` / `.cmd`).

**2. O que acontece quando uma contradição legal é encontrada?**  
O compilador estático acusa um erro formal no terminal/painel antes da execução do contrato, indicando qual artigo ou inconsistência lógica foi violada.

**3. Como reportar problemas ou contribuir com o projeto?**  
Abra uma *Issue* no repositório descrevendo o comportamento inesperado ou submeta um *Pull Request* seguindo o guia de contribuição e mantendo a cobertura de testes da AST e do motor.

---

## 📚 Documentação

- [Manual Completo da Linguagem Jurídica](MANUAL_DA_LINGUAGEM.md)
- [Referência da CLI `juris`](cli.py)
- [Guia do Instalador Visual e Configuração do PATH](installer_gui.py)
- [Contrato de Demonstração e Exemplos](examples/compra_imovel.jur)

