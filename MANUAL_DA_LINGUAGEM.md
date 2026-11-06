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

Quando o modelo PDF contém os rótulos `CONTRATANTE` e `CONTRATADO`, os nomes
podem ser definidos no código `.jur` com `CONTRATANTE.NOME` e
`CONTRATADO.NOME`. O gerador substitui automaticamente esses rótulos pelos
nomes informados; se `PARTES` usar outros identificadores, a primeira e a
segunda parte são usadas como contratante e contratado.

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

### 3.3 Modelos jurídicos e geração por preenchimento

Na aba **Modelos jurídicos**, envie um modelo em PDF, TXT, MD ou JUR, atribua um nome
e informe o tipo do instrumento, como `Divórcio`, `Partilha de bens` ou `Locação`.
O cadastro ocorre em duas etapas: clique em **Analisar arquivo** para extrair o texto,
identificar o tipo e listar as variáveis obrigatórias na área de revisão. Depois de
conferir a prévia e os campos, clique em **Adicionar modelo após revisão** para salvar
o arquivo e o objeto no sistema.
A análise também reconhece arquivos sem marcadores: rótulos como `Nome:`,
`CPF:`, `Cidade:` e linhas com sublinhados ou pontilhados são convertidos em campos.
Modelos PDF, DOCX, TXT, JUR e MD são aceitos.
Para que os dados sejam preenchíveis, marque os campos no modelo com chaves duplas:

```text
REQUERENTE: {{nome_requerente}}
REQUERIDO: {{nome_requerido}}
COMARCA: {{comarca}}
```

Depois de selecionar o modelo no catálogo, o sistema exibe os campos para preenchimento,
permite adicionar informações ou cláusulas e gera um novo PDF jurídico sem alterar o arquivo
original.

Um arquivo `.jur` pode indicar o modelo no cabeçalho:

```jur
MODELO: Divórcio consensual
TIPO: Divórcio
```

O nome usado em `MODELO` deve ser o mesmo nome cadastrado na aba de modelos jurídicos.
O sistema cadastra automaticamente o arquivo `Contrato Padrão.pdf` da raiz como modelo
fallback. Se o usuário não selecionar outro modelo, esse arquivo será usado como base.
Quando um modelo PDF próprio é enviado, ele fica armazenado e passa a ser a base daquele
modelo; o PDF final preserva as páginas originais e acrescenta o conteúdo preenchido.
As variáveis obrigatórias de um modelo enviado são lidas do próprio arquivo. Use
`{{nome_completo}}`, `[[cpf]]` ou `${objeto_demanda}` para marcar uma variável;
esses nomes são salvos no objeto do modelo e aparecem na área de preenchimento.
O sistema não adiciona campos jurídicos heurísticos aos modelos enviados.
No modelo padrão, os campos são identificados automaticamente pelo conteúdo do contrato,
incluindo nome, nacionalidade, estado civil, profissão, CPF, identidade, endereço, CEP,
objeto da demanda, honorários, parcelas, banco, agência e conta. O preenchimento é
sobreposto nas páginas originais para manter a formatação do PDF.
Na área de formatação é possível escolher a tipografia (Helvetica, Times New Roman ou
Courier) e o tamanho da fonte do texto gerado e dos valores sobrepostos no PDF.

As imagens institucionais (logo, rodapé ou assinatura visual) são enviadas pela aba
**Contrato & Estilo**, armazenadas exclusivamente em `backend/storage/company_images/`
e registradas na tabela `company_images` do SQLite. A referência da imagem é salva junto
com o rascunho e é aplicada automaticamente na geração do PDF.

## 6. Assinatura online e cláusulas específicas

Na aba **Contrato & Estilo**, salve o rascunho, informe o nome e documento do signatário,
confirme o consentimento e clique em **Assinar documento**. O sistema registra a assinatura
no SQLite com data, e-mail opcional, hash SHA-256 do documento e um serial de certificado
interno. O botão **Baixar PDF certificado** gera o documento com a tabela de evidências
das assinaturas. Esse certificado interno não substitui, por si só, uma certificação ICP-Brasil
ou outro requisito legal aplicável.

No mesmo painel, use **Adicionar cláusula** para criar título e texto próprios ou
**Remover cláusula** para retirar uma cláusula antes de salvar e gerar o PDF.

## 7. Inicialização do backend e frontend

A interface principal é uma tela única de preenchimento e exportação. Ela mostra o objeto
do modelo, os campos já preenchidos, os campos pendentes e o botão de exportação. As abas
**Criar modelo** e **Modelos cadastrados** ficam disponíveis no mesmo ambiente.

Se `frontend/dist` existir, iniciar o backend já serve o frontend compilado em
`http://localhost:8000`:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Para desenvolvimento com atualização automática da interface, são necessários dois
processos separados:

```bash
python -m uvicorn backend.main:app --reload
cd frontend
npm run dev
```

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

Acesse em: `http://localhost:8000`
