# Juridico.Code

> **The "COBOL of Law": A collaborative, auditable, and deterministic domain-specific language powered by Finite State Machines (FSM) for legal contracts.**

---

Traditional legal contracts written as static text are prone to ambiguities, logical contradictions, untracked defaults, and a lack of operational determinism. **Juridico.Code** bridges this gap by introducing a declarative domain-specific language (`.jur`), a static legal/financial compliance engine, and an interactive environment (CLI + Web Dashboard) to simulate state transitions, audit contract clauses, and cryptographically certify legal documents.

---

## 🌐 Languages

- [English](README_en.md)
- [Português (Brasil)](../../README.md)

---

## 🏷️ Badges

[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=flat-square)](https://github.com/Juridicode/Juridicode/releases)
[![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](../../LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)

---

## 🧭 Navigation

- [Quick start](#-quick-start)
- [How it works](#-how-it-works)
- [Features](#-features)
- [Showcases](#-showcases)
- [FAQ](#-faq)
- [Documentation](#-documentation)

---

## 🚀 Quick start

### Prerequisites
- **Python**: `>= 3.10`
- **Node.js**: `>= 18.x` (for the web visualizer)
- **Git** and Windows environment (or bash/cmd compatible terminal)

### Installation
Clone the repository, install dependencies, and register the `juris` global command:

```bash
git clone https://github.com/Juridicode/Juridicode.git
cd Juridicode
pip install -r requirements.txt
python build_installer.py
```
*(On Windows, you can also run `Instalar.bat` or the graphical installer via `python installer_gui.py`)*

### Usage Example
> **What is the primary task you want to automate or investigate?**  
> *Parse, validate legal/logical contradictions, and inspect the Finite State Machine transitions of a real estate sale agreement.*

```bash
juris examples/compra_imovel.jur
```

---

## ⚙️ How it works

1. **Lexical and Syntactic Analysis (`Lexer` & `Parser`)**: The `.jur` code is converted into an Abstract Syntax Tree (AST), checking grammar and legal syntax rules.
2. **Semantic and Anti-Contradiction Engine (`Evaluator`)**: Validates financial consistency and legal rules (such as Art. 381 of the Civil Code prohibiting confusion between creditor and debtor).
3. **Finite State Machine (FSM)**: Enforces contract lifecycles (`RASCUNHO`, `ATIVO`, `FINALIZADO`, `VENCIDO`) based on verified prerequisites and signatures.
4. **Interactive Dashboard**: The CLI boots the FastAPI backend and launches the browser to view the contract dashboard, test real-time conditions, and export certified signed documents.

---

## 📋 Features

| Target / Component | Output | Requirements |
| :--- | :--- | :--- |
| **Legal Interpreter Engine** | Lexer, Parser with AST generation and legal type evaluation | Python 3.10+ |
| **Contradiction Detector** | Static warnings and blocks for legal conflicts (e.g. debtor == creditor) | Python runtime, Civil Code rule checks |
| **Contract FSM** | Deterministic lifecycle execution governed by transitions and requirements | `.jur` contracts declaring `TRANSIÇÃO` and `REQUER` |
| **Backend Services** | REST API for compilation, dynamic clause checks, and PDF certification | FastAPI, Uvicorn, ReportLab |
| **Global CLI (`juris`)** | Single command to parse files and launch the visual web dashboard | Windows PATH / shell environment |
| **Interactive Web UI** | Real-time state simulator, code editor (REPL), and audit trail dashboard | React, Vite, Node.js 18+ |

---

## 💡 Showcases

- **Deterministic Real Estate Contract**: Down payment, monthly installments, late penalty rules, and automated status transitions.  
  *Reference:* [`examples/compra_imovel.jur`](../../examples/compra_imovel.jur)
- **Legal Conflict & Nullity Detection**: Static detection and blocking of prohibited or contradictory contractual clauses.  
  *Reference:* [`examples/contrato_com_contradicao.jur`](../../examples/contrato_com_contradicao.jur)
- **Service Agreement Workflow**: Stage-based payments and milestone-driven completions.  
  *Reference:* [`examples/prestacao_servicos.jur`](../../examples/prestacao_servicos.jur)

---

## ❓ FAQ

**1. Which platforms are supported?**  
The core Python engine and FastAPI backend are cross-platform (Windows, Linux, macOS). The automated PATH installer scripts (`.bat` / `.cmd`) are natively tuned for Windows.

**2. What happens when a legal contradiction is detected?**  
The engine halts compilation with a diagnostic message detailing the conflicting clauses, parties, or statutory legal provisions violated.

**3. How do I report a bug or contribute?**  
Open an issue or submit a pull request on GitHub following standard contribution practices and maintaining test coverage for the AST parser and evaluator.

---

## 📚 Documentation

- [Language Specification & Manual (Portuguese)](../../MANUAL_DA_LINGUAGEM.md)
- [CLI Reference](cli.py)
- [Visual Installer Guide](installer_gui.py)
- [Example Contracts](../../examples/compra_imovel.jur)

