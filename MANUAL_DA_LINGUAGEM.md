# Manual da Linguagem Jurídica Declarativa (.jur / .juridico)
*O "COBOL do Direito": Linguagem colaborativa, auditável e interpretada com Máquinas de Estados Finitos (FSM)*

---

## 1. Visão Geral e Arquitetura

O ecossistema **Juridico.Code** é uma plataforma completa orientada ao meio jurídico para formalização, auditoria e execução determinística de instrumentos legais.

O sistema é dividido em três camadas:
1. **Linguagem & Interpretador (Engine)**: Lexer, Parser e Evaluator em Python com suporte a AST, inferência de tipos jurídicos e verificação de contradições (ex: Art. 381 do Código Civil).
2. **Backend de Serviços (FastAPI)**: Servidor de compilação, verificação de contradições lógicas, banco de dados semântico de documentos PDF e geração de PDFs assinados e certificados.
3. **Frontend Interativo (React + Vite)**: Dashboard jurídico com alternância entre interface moderna e o wireframe original, simulador de transições em tempo real, editor IDE com REPL e visualização gráfica de status contratual.

---

## 2. Sintaxe e Gramática da Linguagem

### 2.1 Declaração de Contrato
```jur
CONTRATO CompraImovel
ESTADO = RASCUNHO
PARTES: COMPRADOR, VENDEDOR
```

### 2.2 Declaração de Obrigações
```jur
OBRIGAÇÃO pagamento
DEVEDOR: COMPRADOR
CREDOR: VENDEDOR
VALOR: R$ 500.000
VENCIMENTO: 10/12/2026

SE não_pago até VENCIMENTO
ENTÃO
    APLICAR multa 2%
    E juros 1% ao mês
```

### 2.3 Máquina de Estados e Transições
```jur
TRANSIÇÃO ASSINADO:
    REQUER comprador.assinatura
    REQUER vendedor.assinatura
    ENTÃO
        estado = ATIVO

TRANSIÇÃO PAGO:
    REQUER estado = ATIVO
    REQUER comprovante.pagamento
    ENTÃO
        obrigação.pagamento = CUMPRIDO
        estado = FINALIZADO

TRANSIÇÃO VENCIDO:
    SE data.hoje > vencimento
    E obrigacao.pagamento != CUMPRIDO
    ENTÃO
        APLICAR multa
        APLICAR juros
        NOTIFICAR vendedor
```

### 2.4 Auditoria e Prova Criptográfica
```jur
AUDITORIA DOCUMENTO:
    Criado em: 12/01/1992
    Criador: advogado.numero1
    Editado pela última vez: 13/05/2005
    Último editor: advogado.numero2
    Histórico de Modificações: 235 adições, 12 deleções
    UUID: 123e4567-e89b-12d3-a456-426614174000
```

## 3. Instalador de Aplicativo no PATH do Windows & Comando CLI `juris`

O ecossistema possui um instalador integrado que registra o comando global `juris` nas variáveis de ambiente do Windows.

### 3.1 Instalação Automática no PATH:
Execute uma única vez:
```bash
python install_cli.py
```

### 3.2 Executando qualquer arquivo `.jur`:
Em qualquer terminal (PowerShell / CMD), basta rodar:
```bash
juris examples\compra_imovel.jur
```
**O que o comando faz automaticamente:**
1. Valida estaticamente o arquivo (tokens, AST, contradições lógicas e patrimoniais).
2. Sobe o backend FastAPI (se ainda não estiver rodando).
3. Transmite o código do contrato para a sessão ativa.
4. Abre automaticamente o navegador padrão na página visual do contrato com todos os dados e o dashboard interativo.

---

## 4. Avaliação de Condicionais em Tempo Real

A interface visual conta com um painel dinâmico dedicado para avaliação booleana de cláusulas condicionais:
- **`SE não_pago até VENCIMENTO`**: Mostra se a condição de inadimplência está ativa ou inativa com base no comprovante de pagamento, exibindo as penalidades incidentes (multa 2% e juros 1%).
- **Requisitos de Transição**: Mostra em tempo real a validação de assinaturas de comprador, vendedor e autorizações de órgãos públicos.

---

## 5. Verificador de Contradições Jurídicas

O motor executa análises estáticas e dinâmicas para detectar:
- **Confusão Patrimonial**: Quando credor e devedor são a mesma pessoa ou entidade (Art. 381 CC).
- **Indeterminação de Objeto**: Obrigações sem quantificação ou valor fixado.
- **Inexigibilidade / Prazos**: Ausência de prazos ou contradições de datas.
- **Incoerência de Estados (Deadlocks)**: Estados inalcançáveis na máquina de estados.

---

## 4. Banco de Precedentes e Consulta em PDF

A linguagem permite indexação direta de arquivos PDF. É possível consultar termos nos contratos físicos ou digitalizados:
```jur
CONSULTAR_PDF "multa rescisória"
```
O sistema busca em tempo real nos documentos indexados em `backend/storage/` e retorna linhas e trechos correspondentes.

---

## 5. Como Executar

### Backend:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend:
```bash
cd frontend
npm run dev
```

Acesse em: `http://localhost:5173`
