import React, { useState, useEffect } from 'react';
import { 
  Play, ShieldAlert, FileText, CheckCircle2, AlertTriangle, 
  Search, Upload, Download, RefreshCw, Key, Scale, History,
  Sparkles, BookOpen, Layers, Terminal, CheckCircle, XCircle, Zap, Save
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const DEFAULT_CODE = `CONTRATO CompraImovel

ESTADO = RASCUNHO

PARTES: COMPRADOR, VENDEDOR

COMPRADOR.NOME = "Comprador Principal"
COMPRADOR.DOCUMENTO = "CPF 000.000.000-00"
COMPRADOR.DOCUMENTO_VALIDADE = 31/12/2027
VENDEDOR.NOME = "Vendedor Principal"
VENDEDOR.DOCUMENTO = "CPF 111.111.111-11"
VENDEDOR.DOCUMENTO_VALIDADE = 31/12/2027

OBRIGAÇÃO pagamento
DEVEDOR: COMPRADOR
CREDOR: VENDEDOR
VALOR: R$ 500.000
VENCIMENTO: 10/12/2026

SE não_pago até VENCIMENTO
ENTÃO
    APLICAR multa 2%
    E juros 1% ao mês

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

AUDITORIA DOCUMENTO:
    Criado em: 12/01/1992
    Criador: advogado.numero1
    Editado pela última vez: 13/05/2005
    Último editor: advogado.numero2
    Histórico de Modificações: 235 adições, 12 deleções
    UUID: 123e4567-e89b-12d3-a456-426614174000`;

export default function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [activeTab, setActiveTab] = useState('workspace');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [isSaved, setIsSaved] = useState(true);

  // Runtime context state for interactive simulation
  const [runtimeState, setRuntimeState] = useState({
    'comprador.assinatura': false,
    'vendedor.assinatura': false,
    'comprovante.pagamento': false,
    'falta_vistoria': false,
    'detran.autorizacao': false
  });

  const [pdfQuery, setPdfQuery] = useState('');
  const [pdfResults, setPdfResults] = useState([]);
  const [pdfList, setPdfList] = useState([]);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [pdfMessage, setPdfMessage] = useState('');
  const [draftId, setDraftId] = useState(null);
  const [draftName, setDraftName] = useState('Meu contrato');
  const [formatting, setFormatting] = useState({
    margins: { top: 40, right: 40, bottom: 40, left: 40 },
    custom_clauses: [],
    font_family: 'Helvetica',
    font_size: 10
  });
  const [signer, setSigner] = useState({ name: '', document: '', email: '', consent: false });
  const [signatureMessage, setSignatureMessage] = useState('');
  const [footerImageName, setFooterImageName] = useState('');
  const [companyImages, setCompanyImages] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [databaseInfo, setDatabaseInfo] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(true);
  const [legalTemplates, setLegalTemplates] = useState([]);
  const [templateForm, setTemplateForm] = useState({ name: '', contractType: 'Divórcio', file: null });
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateFields, setTemplateFields] = useState({});
  const [fieldErrors, setFieldErrors] = useState({});
  const [templateAdditions, setTemplateAdditions] = useState([]);
  const [templateMessage, setTemplateMessage] = useState('');
  const [uploadingTemplate, setUploadingTemplate] = useState(false);
  const [templateFileKey, setTemplateFileKey] = useState(0);
  const [templateAnalysis, setTemplateAnalysis] = useState(null);

  useEffect(() => {
    const fetchInitialFile = async () => {
      try {
        const res = await fetch(`${API_BASE}/current-file`);
        const data = await res.json();
        if (data.code && data.code.trim().length > 0) {
          setCode(data.code);
          runJuridicoCode(data.code, runtimeState);
        } else {
          runJuridicoCode(DEFAULT_CODE, runtimeState);
        }
      } catch (e) {
        runJuridicoCode(DEFAULT_CODE, runtimeState);
      }
    };
    fetchInitialFile();
    fetchPdfList();
    fetchDrafts();
    fetchDatabaseInfo();
    fetchCompanyImages();
    fetchLegalTemplates();
  }, []);

  const runJuridicoCode = async (codeToRun = null, customState = null) => {
    setLoading(true);
    setError(null);
    try {
      const targetCode = codeToRun !== null ? codeToRun : code;
      const targetState = customState !== null ? customState : runtimeState;

      const res = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: targetCode,
          runtime_state: targetState
        })
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Erro na compilação do código jurídico.');
      }
      setResult(data);
      if (data.context) {
        setRuntimeState(prev => ({ ...prev, ...data.context }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPdfList = async () => {
    try {
      const res = await fetch(`${API_BASE}/pdf/list`);
      const data = await res.json();
      setPdfList(data.files || []);
    } catch (e) {}
  };

  const fetchDrafts = async () => {
    try {
      const res = await fetch(`${API_BASE}/contracts`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível carregar os modelos.');
      setDrafts(data.contracts || []);
    } catch (e) {
      setError(e.message);
    }
  };

  const fetchLegalTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE}/templates`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível carregar os modelos jurídicos.');
      setLegalTemplates(data.templates || []);
      if (!selectedTemplate) {
        const defaultTemplate = (data.templates || []).find(template => template.is_default) || data.templates?.[0];
        if (defaultTemplate) chooseTemplate(defaultTemplate.id);
      }
    } catch (e) {
      setError(e.message);
    }
  };

  const analyzeLegalTemplate = async () => {
    if (!templateForm.file) {
      setError('Selecione o arquivo do modelo para analisar.');
      return;
    }
    setUploadingTemplate(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', templateForm.file);
      const res = await fetch(`${API_BASE}/templates/analyze`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível analisar o modelo.');
      setTemplateAnalysis(data);
      setTemplateMessage(data.message);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploadingTemplate(false);
    }
  };

  const uploadLegalTemplate = async () => {
    if (!templateForm.name.trim() || !templateForm.contractType.trim() || !templateForm.file) {
      setError('Informe nome, tipo e arquivo do modelo.');
      return;
    }
    if (!templateAnalysis) {
      await analyzeLegalTemplate();
      return;
    }
    setUploadingTemplate(true);
    try {
      const form = new FormData();
      form.append('name', templateForm.name);
      form.append('contract_type', templateForm.contractType);
      form.append('file', templateForm.file);
      const res = await fetch(`${API_BASE}/templates/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível cadastrar o modelo.');
      setTemplateMessage(`Modelo "${data.name}" salvo no aplicativo com ${data.fields.length} campo(s). Agora ele está disponível para preenchimento e exportação.`);
      setTemplateForm({ name: '', contractType: 'Divórcio', file: null });
      setTemplateFileKey(value => value + 1);
      setTemplateAnalysis(null);
      await fetchLegalTemplates();
      await chooseTemplate(data.id);
      setActiveTab('workspace');
    } catch (e) {
      setError(e.message);
    } finally {
      setUploadingTemplate(false);
    }
  };

  const chooseTemplate = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/templates/${id}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível abrir o modelo.');
      setSelectedTemplate(data);
      const codeNames = {};
      const assignments = [...code.matchAll(/^\s*([A-Za-zÀ-ÿ0-9_]+)\.NOME\s*=\s*["']([^"']+)["']/gim)];
      assignments.forEach(([, party, name]) => {
        const normalized = party.toLowerCase();
        if (normalized === 'contratante' || normalized === 'contratado') codeNames[normalized] = name.trim();
      });
      const parties = code.match(/^\s*PARTES\s*:\s*(.+)$/im)?.[1]?.split(',').map(item => item.trim().toLowerCase()) || [];
      if (!codeNames.contratante && parties[0]) {
        const match = assignments.find(([, party]) => party.toLowerCase() === parties[0]);
        if (match) codeNames.contratante = match[2].trim();
      }
      if (!codeNames.contratado && parties[1]) {
        const match = assignments.find(([, party]) => party.toLowerCase() === parties[1]);
        if (match) codeNames.contratado = match[2].trim();
      }
      setTemplateFields(Object.fromEntries((data.fields || []).map(field => [field, codeNames[field] || ''])));
      setFieldErrors({});
      setTemplateAdditions([]);
      setTemplateMessage('');
    } catch (e) {
      setError(e.message);
    }
  };

  const generateFromTemplate = async () => {
    if (!selectedTemplate) return;
    const errors = {};
    selectedTemplate.fields.forEach(field => {
      const value = String(templateFields[field] || '').trim();
      if (!value) errors[field] = 'Campo obrigatório';
      if (field === 'cpf' && value && !/^[\d.\-/\s]+$/.test(value)) errors[field] = 'Informe um CPF válido';
      if (field === 'cep' && value && !/^[\d.\-/\s]+$/.test(value)) errors[field] = 'Informe um CEP válido';
      if (field === 'data_assinatura' && value && !/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(value)) errors[field] = 'Use DD/MM/AAAA';
    });
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      setTemplateMessage('Revise os campos destacados antes de exportar.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/templates/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplate.id,
          fields: templateFields,
          code,
          additions: templateAdditions,
          formatting
        })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (data.detail?.missing_fields) {
          setFieldErrors(Object.fromEntries(data.detail.missing_fields.map(field => [field, 'Campo obrigatório'])));
        }
        throw new Error(data.detail || 'Não foi possível gerar o PDF.');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Documento_${selectedTemplate.name}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      setTemplateMessage('PDF jurídico gerado com sucesso.');
    } catch (e) {
      setError(e.message);
    }
  };

  const clearTemplateFields = () => {
    if (!selectedTemplate) return;
    setTemplateFields(Object.fromEntries((selectedTemplate.fields || []).map(field => [field, ''])));
    setFieldErrors({});
    setTemplateMessage('Campos limpos. O modelo foi mantido.');
  };

  const fetchDatabaseInfo = async () => {
    try {
      const res = await fetch(`${API_BASE}/database/summary`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível carregar o banco.');
      setDatabaseInfo(data);
    } catch (e) {
      setError(e.message);
    }
  };

  const fetchCompanyImages = async () => {
    try {
      const res = await fetch(`${API_BASE}/company-images`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Não foi possível carregar as imagens da empresa.');
      setCompanyImages(data.images || []);
    } catch (e) {
      setError(e.message);
    }
  };

  const loadDraft = async (id) => {
    const res = await fetch(`${API_BASE}/contracts/${id}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Não foi possível abrir o modelo.');
    setDraftId(data.id);
    setDraftName(data.name);
    setCode(data.code);
    setFormatting(data.formatting || { margins: { top: 40, right: 40, bottom: 40, left: 40 }, custom_clauses: [], font_family: 'Helvetica', font_size: 10 });
    setFooterImageName(data.formatting?.footer_image || '');
    setIsSaved(true);
    setActiveTab('editor');
    runJuridicoCode(data.code, runtimeState);
  };

  const toggleRuntimeParam = async (key) => {
    const updatedValue = !runtimeState[key];
    const updatedState = { ...runtimeState, [key]: updatedValue };
    setRuntimeState(updatedState);

    const dataStr = new Date().toISOString().split('T')[0];
    const assignment = `${key} = ${updatedValue}`;
    const registration = `# [${dataStr}] REGISTRO: ${key} = ${updatedValue}`;
    const lines = code.split('\n');
    let replaced = false;
    for (let index = lines.length - 1; index >= 0; index -= 1) {
      if (lines[index].match(new RegExp(`^\\s*${key.replace('.', '\\.')}\\s*=`, 'i'))) {
        lines[index] = assignment;
        replaced = true;
        break;
      }
    }
    if (!replaced) {
      const insertionIndex = lines.findIndex(line =>
        /^\s*(OBRIGAÇÃO|OBRIGACAO|TRANSIÇÃO|TRANSICAO|AUDITORIA)\b/i.test(line)
      );
      const index = insertionIndex >= 0 ? insertionIndex : lines.length;
      lines.splice(index, 0, assignment, registration);
    }
    const newCode = lines.join('\n');
    setCode(newCode);

    try {
      const saveResponse = await fetch(`${API_BASE}/save-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: newCode })
      });
      await saveDraft(newCode);
      setIsSaved(true);
    } catch (e) {
      console.error("Erro ao salvar", e);
    }

    runJuridicoCode(newCode, updatedState);
  };

  const manualSave = async () => {
    try {
      await saveDraft();
      const response = await fetch(`${API_BASE}/save-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })
      });
      if (!response.ok) return;
      setIsSaved(true);
    } catch (e) {
      console.error("Erro ao salvar", e);
    }
  };

  const saveDraft = async (codeValue = code, formattingValue = formatting) => {
    const payload = { name: draftName, code: codeValue, formatting: formattingValue };
    const res = await fetch(draftId ? `${API_BASE}/contracts/${draftId}` : `${API_BASE}/contracts`, {
      method: draftId ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Não foi possível salvar o rascunho.');
    setDraftId(data.id);
    setIsSaved(true);
    fetchDrafts();
    fetchDatabaseInfo();
    return data.id;
  };

  const signDraft = async () => {
    const id = draftId || await saveDraft();
    const res = await fetch(`${API_BASE}/contracts/${id}/sign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        signer_name: signer.name,
        signer_document: signer.document,
        signer_email: signer.email || null,
        consent: signer.consent
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Não foi possível registrar a assinatura.');
    setSignatureMessage(`Certificado ${data.certificate_serial} emitido em ${new Date(data.signed_at).toLocaleString()} · hash ${data.document_sha256.slice(0, 16)}...`);
  };

  const addClause = () => {
    setFormatting(prev => ({
      ...prev,
      custom_clauses: [...prev.custom_clauses, { title: 'CLÁUSULA PERSONALIZADA', body: '' }]
    }));
  };

  const uploadFooterImage = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/company-images`, { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Não foi possível enviar a imagem.');
    setFooterImageName(data.filename);
    const nextFormatting = { ...formatting, footer_image: data.filename };
    setFormatting(nextFormatting);
    await saveDraft(code, nextFormatting);
    await fetchCompanyImages();
  };

  const updateClause = (index, field, value) => {
    setFormatting(prev => ({
      ...prev,
      custom_clauses: prev.custom_clauses.map((clause, clauseIndex) =>
        clauseIndex === index ? { ...clause, [field]: value } : clause
      )
    }));
  };

  const removeClause = (index) => {
    setFormatting(prev => ({
      ...prev,
      custom_clauses: prev.custom_clauses.filter((_, clauseIndex) => clauseIndex !== index)
    }));
    setIsSaved(false);
  };

  const exportSignedPdf = async () => {
    if (!draftId) {
      setError('Salve o documento antes de gerar o PDF assinado.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/contracts/${draftId}/signed-pdf`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.error || 'Não foi possível gerar o PDF assinado.');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Contrato_Assinado_${draftName}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    }
  };

  const exportPdfDocument = async () => {
    try {
      const res = await fetch(`${API_BASE}/export/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, runtime_state: runtimeState, formatting })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.error || 'O servidor não conseguiu gerar o PDF.');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Instrumento_Juridico_${Date.now()}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Erro ao exportar PDF: ' + e.message);
    }
  };

  const queryPdfs = async () => {
    const res = await fetch(`${API_BASE}/pdf/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: pdfQuery })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || 'Não foi possível consultar os PDFs.');
    setPdfResults(data.results || []);
  };

  const uploadPdf = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadingPdf(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${API_BASE}/pdf/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || 'Não foi possível enviar o PDF.');
      setPdfMessage(data.message || 'PDF indexado com sucesso.');
      fetchPdfList();
    } catch (e) {
      setError(e.message);
    } finally {
      setUploadingPdf(false);
    }
  };

  const primaryContract = result?.contracts?.[0] || null;
  const audit = result?.audit || {};

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8fafc', color: '#1e293b', fontFamily: 'Inter, sans-serif' }}>
      
      {/* PROFESSIONAL HEADER */}
      <header style={{
        background: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        padding: '14px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '20px',
        flexWrap: 'wrap',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: '#0f172a',
            padding: '8px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Scale size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: '700', fontSize: '18px', color: '#0f172a', letterSpacing: '-0.5px' }}>
                JURIDICO.CODE
              </span>
              <span style={{ fontSize: '10px', background: '#e2e8f0', color: '#475569', padding: '2px 6px', borderRadius: '4px', fontWeight: '600' }}>MOTOR DE INTERPRETAÇÃO</span>
            </div>
            <span style={{ fontSize: '11px', color: '#64748b' }}>Ambiente de Análise Estruturada e Compliance</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', background: '#f1f5f9', padding: '5px', borderRadius: '8px', flexWrap: 'wrap', justifyContent: 'center', flex: '0 1 auto' }}>
          {['workspace', 'templates', 'models'].map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)} 
              style={{ 
                background: activeTab === tab ? '#ffffff' : 'transparent',
                color: activeTab === tab ? '#0f172a' : '#64748b',
                boxShadow: activeTab === tab ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                border: 'none', borderRadius: '5px', fontSize: '12px', padding: '9px 16px', fontWeight: '600', cursor: 'pointer', whiteSpace: 'nowrap', lineHeight: '1.2'
              }}
            >
              {tab === 'workspace' ? 'Documento' : tab === 'templates' ? 'Criar modelo' : 'Modelos cadastrados'}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button 
            onClick={manualSave}
            style={{ display: 'flex', alignItems: 'center', gap: '7px', background: 'transparent', border: '1px solid #cbd5e1', color: '#475569', fontSize: '12px', padding: '9px 14px', borderRadius: '5px', cursor: 'pointer', whiteSpace: 'nowrap', lineHeight: '1.2' }}
          >
            <Save size={14} /> {isSaved ? 'Salvo' : 'Salvar Alterações'}
          </button>

          <button 
            onClick={() => runJuridicoCode()} 
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: '7px', background: '#0f172a', color: '#ffffff', border: 'none', fontSize: '12px', padding: '9px 16px', borderRadius: '5px', fontWeight: '600', cursor: 'pointer', whiteSpace: 'nowrap', lineHeight: '1.2' }}
          >
            {loading ? <RefreshCw className="spin" size={14} /> : <Play size={14} />}
            Compilar Código
          </button>
        </div>
      </header>

      <main style={{ flex: 1, padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', borderRadius: '8px', padding: '12px 16px', marginBottom: '18px', fontSize: '13px' }}>
            <strong>Erro:</strong> {error}
            <button onClick={() => setError(null)} style={{ float: 'right', border: 0, background: 'transparent', color: '#991b1b', cursor: 'pointer' }}>Fechar</button>
          </div>
        )}
        
        {/* Contradiction Alert Banner */}
        {result?.contradictions?.length > 0 && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <AlertTriangle size={24} color="#dc2626" style={{ flexShrink: 0 }} />
            <div>
              <h4 style={{ color: '#991b1b', fontSize: '14px', fontWeight: '700', margin: '0 0 6px 0' }}>
                INCOMPATIBILIDADE JURÍDICA DETECTADA
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {result.contradictions.map((c, idx) => (
                  <div key={idx} style={{ fontSize: '13px', color: '#b91c1c' }}>
                    <strong>[{c.severity}]</strong> {c.message}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'contract' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ marginTop: 0 }}>Rascunho editável</h3>
              <label style={{ display: 'block', fontSize: '12px', marginBottom: '8px' }}>Abrir modelo salvo
                <select defaultValue="" onChange={e => e.target.value && loadDraft(e.target.value).catch(err => setError(err.message))}
                  style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: '8px', marginTop: '4px' }}>
                  <option value="">Selecione um rascunho</option>
                  {drafts.map(draft => <option key={draft.id} value={draft.id}>{draft.name}</option>)}
                </select>
              </label>
              <input value={draftName} onChange={e => setDraftName(e.target.value)} placeholder="Nome do contrato"
                style={{ width: '100%', boxSizing: 'border-box', padding: '9px', marginBottom: '10px', border: '1px solid #cbd5e1', borderRadius: '4px' }} />
              <p style={{ fontSize: '12px', color: '#64748b' }}>O corpo abaixo é o mesmo texto editável do arquivo .jur. Você pode criar qualquer cláusula e manter sua própria formatação.</p>
              <textarea value={code} onChange={e => { setCode(e.target.value); setIsSaved(false); }}
                style={{ width: '100%', height: '360px', boxSizing: 'border-box', padding: '12px', resize: 'vertical', fontFamily: 'monospace', border: '1px solid #cbd5e1', borderRadius: '4px' }} />
              <button onClick={() => saveDraft().catch(e => setError(e.message))}
                style={{ marginTop: '10px', padding: '9px 14px', background: '#0f172a', color: '#fff', border: 0, borderRadius: '4px', cursor: 'pointer' }}>
                Salvar no SQLite
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <h3 style={{ marginTop: 0 }}>Formatação do PDF</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                  <label style={{ fontSize: '12px' }}>Tipografia
                    <select value={formatting.font_family || 'Helvetica'}
                      onChange={e => setFormatting(prev => ({ ...prev, font_family: e.target.value }))}
                      style={{ display: 'block', width: '100%', padding: '7px', marginTop: '3px' }}>
                      <option value="Helvetica">Helvetica</option>
                      <option value="Times-Roman">Times New Roman</option>
                      <option value="Courier">Courier</option>
                    </select>
                  </label>
                  <label style={{ fontSize: '12px' }}>Tamanho da fonte
                    <input type="number" min="6" max="24" step="1" value={formatting.font_size || 10}
                      onChange={e => setFormatting(prev => ({ ...prev, font_size: Number(e.target.value) }))}
                      style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: '7px', marginTop: '3px' }} />
                  </label>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  {Object.entries(formatting.margins).map(([side, value]) => (
                    <label key={side} style={{ fontSize: '12px' }}>{side}
                      <input type="number" min="0" value={value}
                        onChange={e => setFormatting(prev => ({ ...prev, margins: { ...prev.margins, [side]: Number(e.target.value) } }))}
                        style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: '7px', marginTop: '3px' }} />
                    </label>
                  ))}
                </div>
                <h4>Cláusulas específicas</h4>
                {formatting.custom_clauses.map((clause, index) => (
                  <div key={index} style={{ marginBottom: '10px' }}>
                    <input value={clause.title} onChange={e => updateClause(index, 'title', e.target.value)}
                      style={{ width: '100%', boxSizing: 'border-box', padding: '7px', marginBottom: '4px' }} />
                    <textarea value={clause.body} onChange={e => updateClause(index, 'body', e.target.value)}
                      placeholder="Escreva a cláusula do seu jeito..." style={{ width: '100%', boxSizing: 'border-box', minHeight: '65px', padding: '7px' }} />
                  <button onClick={() => removeClause(index)} style={{ marginTop: '4px', padding: '5px 8px', cursor: 'pointer' }}>
                    Remover cláusula
                  </button>
                </div>
                ))}
                <button onClick={addClause} style={{ padding: '7px 10px', cursor: 'pointer' }}>+ Adicionar cláusula</button>
                <label style={{ display: 'block', marginTop: '14px', fontSize: '12px' }}>
                  Imagem do rodapé (PNG/JPG)
                  <input type="file" accept=".png,.jpg,.jpeg" onChange={e => uploadFooterImage(e).catch(err => setError(err.message))}
                    style={{ display: 'block', marginTop: '5px' }} />
                </label>
                {footerImageName && <div style={{ fontSize: '11px', color: '#047857', marginTop: '5px' }}>Rodapé: {footerImageName}</div>}
                <div style={{ marginTop: '12px', fontSize: '12px', color: '#475569' }}>
                  <strong>Imagens da empresa salvas:</strong> {companyImages.length}
                  {companyImages.slice(0, 3).map(image => (
                    <div key={image.id} style={{ marginTop: '4px' }}>{image.original_name} ({image.size} bytes)</div>
                  ))}
                </div>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <h3 style={{ marginTop: 0 }}>Preview do estilo</h3>
                <div style={{ background: '#e5e7eb', padding: '16px', overflow: 'auto' }}>
                  <div style={{
                    background: '#ffffff',
                    minHeight: '300px',
                    padding: `${Math.max(12, formatting.margins.top / 2)}px ${Math.max(12, formatting.margins.right / 2)}px ${Math.max(24, formatting.margins.bottom / 2)}px ${Math.max(12, formatting.margins.left / 2)}px`,
                    boxSizing: 'border-box',
                    fontFamily: 'Georgia, serif',
                    color: '#1e293b',
                    boxShadow: '0 2px 8px rgba(15, 23, 42, .15)'
                  }}>
                    <div style={{ textAlign: 'center', fontWeight: 700, fontSize: '15px', marginBottom: '12px' }}>INSTRUMENTO PARTICULAR DE CONTRATO</div>
                    <div style={{ borderBottom: '2px solid #2563eb', marginBottom: '10px' }} />
                    <div style={{ fontSize: '10px', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{code.slice(0, 700)}</div>
                    {formatting.custom_clauses.map((clause, index) => (
                      <div key={index} style={{ marginTop: '10px', fontSize: '10px', lineHeight: 1.45 }}>
                        <strong>{clause.title || `CLÁUSULA ${index + 1}`}</strong>
                        <div>{clause.body}</div>
                      </div>
                    ))}
                    <div style={{ borderTop: '1px solid #cbd5e1', marginTop: '20px', paddingTop: '6px', fontSize: '8px', color: '#64748b' }}>
                      {footerImageName ? `Imagem do rodapé: ${footerImageName}` : 'Área reservada para imagem de rodapé'}
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <h3 style={{ marginTop: 0 }}>Assinatura eletrônica online</h3>
                <input placeholder="Nome completo" value={signer.name} onChange={e => setSigner({ ...signer, name: e.target.value })}
                  style={{ width: '100%', boxSizing: 'border-box', padding: '8px', marginBottom: '7px' }} />
                <input placeholder="CPF ou documento" value={signer.document} onChange={e => setSigner({ ...signer, document: e.target.value })}
                  style={{ width: '100%', boxSizing: 'border-box', padding: '8px', marginBottom: '7px' }} />
                <input placeholder="E-mail (opcional)" value={signer.email} onChange={e => setSigner({ ...signer, email: e.target.value })}
                  style={{ width: '100%', boxSizing: 'border-box', padding: '8px', marginBottom: '7px' }} />
                <label style={{ display: 'block', fontSize: '12px', marginBottom: '10px' }}>
                  <input type="checkbox" checked={signer.consent} onChange={e => setSigner({ ...signer, consent: e.target.checked })} />
                  Confirmo que li o documento e autorizo o registro desta assinatura eletrônica.
                </label>
                <button onClick={() => signDraft().catch(e => setError(e.message))}
                  style={{ padding: '9px 14px', background: '#059669', color: '#fff', border: 0, borderRadius: '4px', cursor: 'pointer' }}>
                  Assinar documento
                </button>
                <button onClick={exportSignedPdf}
                  style={{ marginLeft: '8px', padding: '9px 14px', background: '#1d4ed8', color: '#fff', border: 0, borderRadius: '4px', cursor: 'pointer' }}>
                  Baixar PDF certificado
                </button>
                <p style={{ fontSize: '11px', color: '#64748b' }}>O sistema registra identidade informada, consentimento, data e hash do conteúdo assinado.</p>
                {signatureMessage && <div style={{ color: '#047857', fontSize: '12px' }}>{signatureMessage}</div>}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'workspace' && (
          <div>
            <div style={{ background: '#0f172a', color: '#fff', borderRadius: '10px', padding: '22px', marginBottom: '18px' }}>
              <div style={{ fontSize: '12px', opacity: .7, textTransform: 'uppercase', letterSpacing: 1 }}>Documento jurídico</div>
              <h1 style={{ margin: '6px 0', fontSize: '25px' }}>{selectedTemplate?.name || 'Selecione um modelo'}</h1>
              <div style={{ opacity: .75, fontSize: '13px' }}>Objeto: {selectedTemplate?.contract_type || 'não definido'}</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 280px', gap: '16px', alignItems: 'start' }}>
              <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Modelo base</h3>
                <select value={selectedTemplate?.id || ''} onChange={e => chooseTemplate(e.target.value)}
                  style={{ width: '100%', padding: '9px', marginBottom: '16px' }}>
                  {legalTemplates.map(template => <option key={template.id} value={template.id}>{template.name}</option>)}
                </select>
                <label style={{ fontSize: '12px', color: '#475569' }}>Nome do documento
                  <input value={draftName} onChange={e => setDraftName(e.target.value)}
                    style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: '8px', marginTop: '4px' }} />
                </label>
                <button onClick={() => saveDraft().catch(e => setError(e.message))}
                  style={{ width: '100%', marginTop: '12px', padding: '10px', background: '#0f172a', color: '#fff', border: 0, borderRadius: '5px', cursor: 'pointer' }}>
                  {isSaved ? 'Salvar no SQLite' : 'Salvar alterações'}
                </button>
              </div>
              <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Campos do documento</h3>
                {!selectedTemplate && <p style={{ color: '#64748b' }}>Escolha um modelo para identificar os campos.</p>}
                {selectedTemplate?.fields?.map(field => {
                  const filled = Boolean((templateFields[field] || '').trim());
                  return (
                    <label key={field} style={{ display: 'block', fontSize: '12px', marginBottom: '10px' }}>
                      <span style={{ display: 'flex', justifyContent: 'space-between', color: filled ? '#047857' : '#b45309', fontWeight: 700 }}>
                        {field} <span>{filled ? 'Preenchido' : 'A preencher'}</span>
                      </span>
                      <input value={templateFields[field] || ''} onChange={e => {
                        setTemplateFields({ ...templateFields, [field]: e.target.value });
                        setFieldErrors({ ...fieldErrors, [field]: '' });
                      }}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px', marginTop: '3px', border: `1px solid ${fieldErrors[field] ? '#ef4444' : filled ? '#86efac' : '#fcd34d'}` }} />
                      {fieldErrors[field] && <span style={{ display: 'block', color: '#dc2626', marginTop: '3px' }}>{fieldErrors[field]}</span>}
                    </label>
                  );
                })}
                <div style={{ marginTop: '15px', paddingTop: '12px', borderTop: '1px solid #e2e8f0', fontSize: '12px' }}>
                  <strong>Resumo:</strong> {Object.values(templateFields).filter(value => String(value).trim()).length} preenchido(s) · {Object.values(templateFields).filter(value => !String(value).trim()).length} pendente(s)
                </div>
              </div>
              <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Exportação</h3>
                <p style={{ fontSize: '12px', color: '#64748b' }}>O PDF mantém o formato do modelo selecionado.</p>
                <button onClick={generateFromTemplate} disabled={!selectedTemplate}
                  style={{ width: '100%', padding: '11px', background: '#2563eb', color: '#fff', border: 0, borderRadius: '5px', cursor: 'pointer', fontWeight: 700 }}>
                  Exportar documento PDF
                </button>
                <button onClick={clearTemplateFields} disabled={!selectedTemplate}
                  style={{ width: '100%', marginTop: '8px', padding: '10px', background: '#fff', color: '#b91c1c', border: '1px solid #fca5a5', borderRadius: '5px', cursor: 'pointer', fontWeight: 600 }}>
                  Limpar campos
                </button>
                <h4 style={{ marginBottom: '8px' }}>Cláusulas específicas</h4>
                {formatting.custom_clauses.map((clause, index) => (
                  <div key={index} style={{ fontSize: '12px', borderBottom: '1px solid #e2e8f0', padding: '7px 0' }}>
                    <strong>{clause.title || `Cláusula ${index + 1}`}</strong>
                    <div style={{ color: '#64748b' }}>{clause.body}</div>
                  </div>
                ))}
                <button onClick={() => setActiveTab('templates')} style={{ marginTop: '10px', width: '100%', padding: '8px', cursor: 'pointer' }}>Gerenciar cláusulas</button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'templates' && (
          <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
              <h2 style={{ marginTop: 0 }}>Cadastrar modelo</h2>
              <p style={{ color: '#64748b', fontSize: '13px' }}>
                Selecione o arquivo. O sistema analisa o conteúdo, identifica as variáveis e só depois salva o modelo.
              </p>
              <input value={templateForm.name} onChange={e => setTemplateForm({ ...templateForm, name: e.target.value })}
                placeholder="Nome do modelo (ex.: Divórcio consensual)"
                style={{ width: '100%', boxSizing: 'border-box', padding: '9px', marginBottom: '8px' }} />
              <input value={templateForm.contractType} onChange={e => setTemplateForm({ ...templateForm, contractType: e.target.value })}
                placeholder="Tipo (ex.: Divórcio, Partilha, Locação)"
                style={{ width: '100%', boxSizing: 'border-box', padding: '9px', marginBottom: '8px' }} />
              <input key={templateFileKey} type="file" accept=".pdf,.docx,.txt,.jur,.md"
                onChange={e => setTemplateForm({ ...templateForm, file: e.target.files?.[0] || null })}
                style={{ width: '100%', marginBottom: '10px' }} />
              <button onClick={uploadLegalTemplate} disabled={uploadingTemplate || !templateForm.file}
                style={{ padding: '9px 14px', background: '#0f172a', color: '#fff', border: 0, borderRadius: '4px', cursor: 'pointer' }}>
                {uploadingTemplate ? 'Analisando...' : templateAnalysis ? 'Adicionar modelo após revisão' : 'Analisar arquivo'}
              </button>
              {templateAnalysis && (
                <button onClick={() => { setTemplateAnalysis(null); setTemplateMessage('Análise descartada.'); }}
                  style={{ marginLeft: '8px', padding: '9px 14px', background: '#fff', color: '#b91c1c', border: '1px solid #fca5a5', borderRadius: '4px', cursor: 'pointer' }}>
                  Refazer análise
                </button>
              )}
              {templateMessage && <p style={{ color: '#047857', fontSize: '12px' }}>{templateMessage}</p>}
              <h3>Modelos disponíveis</h3>
              {legalTemplates.length === 0 && <p style={{ color: '#64748b', fontSize: '13px' }}>Nenhum modelo cadastrado.</p>}
              {legalTemplates.map(template => (
                <button key={template.id} onClick={() => chooseTemplate(template.id).then(() => setActiveTab('workspace'))}
                  style={{ display: 'block', width: '100%', textAlign: 'left', background: selectedTemplate?.id === template.id ? '#eff6ff' : '#fff', border: '1px solid #e2e8f0', borderRadius: '5px', padding: '10px', marginBottom: '7px', cursor: 'pointer' }}>
                  <strong>{template.name}</strong>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>{template.contract_type} · {template.fields.length} campo(s)</div>
                </button>
              ))}
            </div>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
              {templateAnalysis ? (
                <>
                  <h2 style={{ marginTop: 0 }}>Revisão do arquivo analisado</h2>
                  <p style={{ color: '#64748b', fontSize: '13px' }}>
                    Arquivo: <strong>{templateAnalysis.filename}</strong> · Tipo detectado: <strong>{templateAnalysis.file_type}</strong>
                  </p>
                  <h3>Variáveis obrigatórias identificadas ({templateAnalysis.fields.length})</h3>
                  {templateAnalysis.fields.length ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '18px' }}>
                      {templateAnalysis.fields.map(field => (
                        <span key={field} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1d4ed8', borderRadius: '5px', padding: '6px 9px', fontSize: '12px' }}>{field}</span>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#92400e', background: '#fffbeb', padding: '10px', borderRadius: '5px', fontSize: '12px' }}>
                      Nenhuma variável foi identificada. Revise o arquivo antes de salvar.
                    </p>
                  )}
                  <h3>Prévia extraída do arquivo</h3>
                  <pre style={{ marginTop: '8px', padding: '14px', background: '#f8fafc', whiteSpace: 'pre-wrap', fontSize: '12px', maxHeight: '390px', overflow: 'auto' }}>{templateAnalysis.preview}</pre>
                </>
              ) : !selectedTemplate ? (
                <div style={{ color: '#64748b' }}>Selecione um modelo para preencher e gerar o documento.</div>
              ) : (
                <>
                  <h2 style={{ marginTop: 0 }}>Variáveis do modelo: {selectedTemplate.name}</h2>
                  <p style={{ color: '#64748b', fontSize: '13px' }}>
                    Variáveis obrigatórias identificadas e salvas neste objeto. Use <code>{'{{nome_da_variavel}}'}</code> no arquivo enviado para criar um campo.
                  </p>
                  {selectedTemplate.fields.length === 0 && (
                    <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', color: '#92400e', borderRadius: '6px', padding: '10px', marginBottom: '12px', fontSize: '12px' }}>
                      Este modelo não possui variáveis identificáveis. Edite o arquivo e marque os campos com <code>{'{{campo}}'}</code>, depois cadastre-o novamente.
                    </div>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    {selectedTemplate.fields.map(field => (
                      <label key={field} style={{ fontSize: '12px' }}>
                        {field}
                        <input value={templateFields[field] || ''} onChange={e => setTemplateFields({ ...templateFields, [field]: e.target.value })}
                          placeholder={`Informe ${field}`}
                          style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: '8px', marginTop: '3px' }} />
                      </label>
                    ))}
                  </div>
                  <h3>Informações adicionais</h3>
                  {templateAdditions.map((addition, index) => (
                    <div key={index} style={{ display: 'grid', gridTemplateColumns: '180px 1fr auto', gap: '6px', marginBottom: '7px' }}>
                      <input value={addition.title} placeholder="Título" onChange={e => setTemplateAdditions(templateAdditions.map((item, i) => i === index ? { ...item, title: e.target.value } : item))} />
                      <input value={addition.body} placeholder="Texto da informação ou cláusula" onChange={e => setTemplateAdditions(templateAdditions.map((item, i) => i === index ? { ...item, body: e.target.value } : item))} />
                      <button onClick={() => setTemplateAdditions(templateAdditions.filter((_, i) => i !== index))}>Remover</button>
                    </div>
                  ))}
                  <div style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
                    <button onClick={() => setTemplateAdditions([...templateAdditions, { title: '', body: '' }])} style={{ padding: '9px 12px', cursor: 'pointer' }}>+ Adicionar informação</button>
                    <button onClick={generateFromTemplate} style={{ padding: '9px 14px', background: '#2563eb', color: '#fff', border: 0, borderRadius: '4px', cursor: 'pointer' }}><Download size={14} style={{ verticalAlign: 'middle' }} /> Gerar PDF jurídico</button>
                  </div>
                  <pre style={{ marginTop: '20px', padding: '14px', background: '#f8fafc', whiteSpace: 'pre-wrap', fontSize: '12px', maxHeight: '360px', overflow: 'auto' }}>{selectedTemplate.content}</pre>
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'models' && (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
            <h2 style={{ marginTop: 0 }}>Modelos cadastrados</h2>
            <p style={{ color: '#64748b', fontSize: '13px' }}>Cada arquivo salvo é classificado pelo objeto jurídico informado no cadastro.</p>
            {legalTemplates.length === 0 && <p>Nenhum modelo cadastrado ainda.</p>}
            {legalTemplates.map(template => (
              <div key={template.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '1px solid #e2e8f0' }}>
                <div><strong>{template.name}</strong><div style={{ color: '#64748b', fontSize: '11px' }}>Objeto: {template.contract_type} · Campos: {template.fields.length}</div></div>
                <button onClick={() => chooseTemplate(template.id).then(() => setActiveTab('workspace'))} style={{ padding: '7px 12px', cursor: 'pointer' }}>Usar modelo</button>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'database' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
              <h2 style={{ marginTop: 0 }}>Banco SQLite</h2>
              <div style={{ fontSize: '12px', color: '#64748b', wordBreak: 'break-all' }}>{databaseInfo?.path || 'Carregando...'}</div>
              <div style={{ display: 'flex', gap: '14px', margin: '18px 0' }}><strong>Rascunhos: {databaseInfo?.tables?.contract_drafts ?? '-'}</strong><strong>Assinaturas: {databaseInfo?.tables?.contract_signatures ?? '-'}</strong></div>
              <button onClick={fetchDatabaseInfo} style={{ padding: '8px 12px', cursor: 'pointer' }}>Atualizar dados</button>
            </div>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
              <h3 style={{ marginTop: 0 }}>Assinaturas registradas</h3>
              {databaseInfo?.signatures?.length === 0 && <p style={{ fontSize: '13px' }}>Nenhuma assinatura registrada.</p>}
              {databaseInfo?.signatures?.map(signature => (
                <div key={signature.id} style={{ padding: '10px 0', borderBottom: '1px solid #e2e8f0', fontSize: '12px' }}>
                  <strong>{signature.signer_name}</strong> · {signature.signer_document}
                  <div style={{ color: '#64748b' }}>{new Date(signature.signed_at).toLocaleString()}</div>
                  <code>{signature.document_sha256.slice(0, 24)}...</code>
                </div>
              ))}
            </div>
            <div style={{ gridColumn: '1 / -1', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
              <h3 style={{ marginTop: 0 }}>Arquivos armazenados</h3>
              {databaseInfo?.storage_files?.map(file => <div key={file.name} style={{ fontSize: '12px', padding: '5px 0' }}>{file.name} ({file.size} bytes)</div>)}
            </div>
          </div>
        )}

        {activeTab === 'pdf_database' && (
          <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ marginTop: 0 }}>Precedentes PDF</h3>
              <p style={{ fontSize: '12px', color: '#64748b' }}>Envie documentos para indexação local e consulte trechos por palavra-chave.</p>
              <input type="file" accept=".pdf" onChange={e => uploadPdf(e)} disabled={uploadingPdf} />
              {pdfMessage && <p style={{ color: '#047857', fontSize: '12px' }}>{pdfMessage}</p>}
              <input value={pdfQuery} onChange={e => setPdfQuery(e.target.value)} placeholder="Ex.: multa, vencimento"
                style={{ width: '100%', boxSizing: 'border-box', padding: '8px', marginTop: '16px' }} />
              <button onClick={() => queryPdfs().catch(e => setError(e.message))}
                style={{ marginTop: '8px', padding: '8px 12px', cursor: 'pointer' }}>Pesquisar precedentes</button>
              <h4>Documentos indexados</h4>
              {pdfList.length === 0 && <div style={{ fontSize: '12px', color: '#64748b' }}>Nenhum PDF indexado.</div>}
              {pdfList.map(file => <div key={file} style={{ fontSize: '12px', padding: '5px 0' }}>{file}</div>)}
            </div>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ marginTop: 0 }}>Resultados da consulta</h3>
              {pdfResults.length === 0 && <div style={{ color: '#64748b', fontSize: '13px' }}>Faça uma pesquisa para ver os trechos encontrados.</div>}
              {pdfResults.map(resultItem => (
                <div key={resultItem.file} style={{ marginBottom: '18px' }}>
                  <strong>{resultItem.file}</strong>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>{resultItem.matches_count} ocorrência(s)</div>
                  {resultItem.snippets?.map((snippet, index) => (
                    <div key={index} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '8px', marginTop: '6px', fontSize: '12px' }}>
                      Linha {snippet.line}: {snippet.text}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div>
            {/* Interactive FSM Controls */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Zap size={18} color="#0f172a" />
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#1e293b' }}>
                  Simulador de Cumprimento de Obrigações (Clique para Registrar no Documento):
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={() => toggleRuntimeParam('comprador.assinatura')}
                  style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '4px', border: '1px solid', borderColor: runtimeState['comprador.assinatura'] ? '#059669' : '#cbd5e1', background: runtimeState['comprador.assinatura'] ? '#ecfdf5' : '#ffffff', color: runtimeState['comprador.assinatura'] ? '#059669' : '#64748b', cursor: 'pointer', fontWeight: '600' }}
                >
                  {runtimeState['comprador.assinatura'] ? '✓ Assinatura: Comprador' : 'Pendente: Assinatura Comprador'}
                </button>
                <button 
                  onClick={() => toggleRuntimeParam('vendedor.assinatura')}
                  style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '4px', border: '1px solid', borderColor: runtimeState['vendedor.assinatura'] ? '#059669' : '#cbd5e1', background: runtimeState['vendedor.assinatura'] ? '#ecfdf5' : '#ffffff', color: runtimeState['vendedor.assinatura'] ? '#059669' : '#64748b', cursor: 'pointer', fontWeight: '600' }}
                >
                  {runtimeState['vendedor.assinatura'] ? '✓ Assinatura: Vendedor' : 'Pendente: Assinatura Vendedor'}
                </button>
                <button 
                  onClick={() => toggleRuntimeParam('comprovante.pagamento')}
                  style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '4px', border: '1px solid', borderColor: runtimeState['comprovante.pagamento'] ? '#059669' : '#cbd5e1', background: runtimeState['comprovante.pagamento'] ? '#ecfdf5' : '#ffffff', color: runtimeState['comprovante.pagamento'] ? '#059669' : '#64748b', cursor: 'pointer', fontWeight: '600' }}
                >
                  {runtimeState['comprovante.pagamento'] ? '✓ Pagamento Efetuado' : 'Aguardando Pagamento'}
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              
              {/* Resumo do Contrato */}
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '12px', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a' }}>Identificação do Documento</h3>
                  <span style={{ fontSize: '11px', background: '#0f172a', color: '#ffffff', padding: '4px 8px', borderRadius: '4px', fontWeight: '600' }}>
                    ESTADO: {primaryContract?.current_state || 'RASCUNHO'}
                  </span>
                </div>
                
                <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr' }}>
                    <strong style={{ color: '#64748b' }}>Nome/Classe:</strong>
                    <span style={{ fontWeight: '600' }}>{primaryContract?.name || 'Instrumento Não Definido'}</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr' }}>
                    <strong style={{ color: '#64748b' }}>Partes:</strong>
                    <span>{primaryContract?.partes?.join(', ') || 'Ausentes'}</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr' }}>
                    <strong style={{ color: '#64748b' }}>Objeto / Valor:</strong>
                    <span>{primaryContract?.obligations?.[0]?.valor || 'Não Especificado'}</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr' }}>
                    <strong style={{ color: '#64748b' }}>Assinatura PGP:</strong>
                    <code style={{ fontSize: '11px', color: '#059669' }}>{audit.pgp_fingerprint}</code>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr' }}>
                    <strong style={{ color: '#64748b' }}>Hash Documento:</strong>
                    <code style={{ fontSize: '11px', color: '#0f172a' }}>{audit.uuid}</code>
                  </div>
                </div>

                <div style={{ marginTop: '20px', borderTop: '1px solid #f1f5f9', paddingTop: '14px' }}>
                  <h4 style={{ fontSize: '13px', margin: '0 0 10px', color: '#0f172a' }}>Obrigações e vencimentos</h4>
                  {primaryContract?.obligations?.map((ob, idx) => {
                    const overdue = ob.due_status === 'VENCIDA';
                    return (
                      <div key={idx} style={{ padding: '10px', marginBottom: '8px', border: `1px solid ${overdue ? '#fecaca' : '#e2e8f0'}`, borderRadius: '6px', background: overdue ? '#fef2f2' : '#f8fafc' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                          <strong style={{ fontSize: '12px' }}>{ob.title}</strong>
                          <span style={{ fontSize: '10px', fontWeight: '700', color: overdue ? '#dc2626' : '#059669' }}>
                            {overdue ? 'VENCIDA' : ob.due_status === 'SEM_DATA' ? 'SEM DATA' : 'NO PRAZO'}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                          Vencimento: {ob.vencimento || 'não informado'} · {ob.devedor || 'devedor não informado'} → {ob.credor || 'credor não informado'}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div style={{ marginTop: '20px' }}>
                  <button onClick={exportPdfDocument} style={{ width: '100%', padding: '8px', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '4px', color: '#0f172a', fontSize: '13px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <Download size={14} /> Exportar Instrumento Certificado (PDF)
                  </button>
                </div>
              </div>

              {/* Status das Condicionais (Gatilhos) */}
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a', borderBottom: '1px solid #f1f5f9', paddingBottom: '12px', marginBottom: '16px' }}>
                  Análise Condicional
                </h3>
                
                {primaryContract?.obligations?.map((ob, idx) => (
                  <div key={idx} style={{ marginBottom: '12px' }}>
                    {ob.conditions?.map((c, cIdx) => (
                      <div key={cIdx} style={{ padding: '12px', border: `1px solid ${c.is_valid ? '#fca5a5' : '#e2e8f0'}`, borderRadius: '6px', background: c.is_valid ? '#fef2f2' : '#f8fafc' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ fontSize: '12px', color: c.is_valid ? '#dc2626' : '#64748b' }}>
                            Condicional: SE {c.condition}
                          </strong>
                          <span style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '4px', background: c.is_valid ? '#dc2626' : '#cbd5e1', color: '#ffffff' }}>
                            {c.is_valid ? 'APLICÁVEL' : 'INATIVA'}
                          </span>
                        </div>
                        {c.is_valid && (
                          <div style={{ fontSize: '12px', color: '#7f1d1d', marginTop: '6px' }}>
                            Consequências: {c.then?.join(' | ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ))}

                {primaryContract?.transitions?.map((tr, idx) => (
                  <div key={idx} style={{ padding: '12px', border: `1px solid ${tr.is_active ? '#6ee7b7' : '#e2e8f0'}`, borderRadius: '6px', background: tr.is_active ? '#ecfdf5' : '#ffffff', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <strong style={{ fontSize: '12px', color: '#0f172a' }}>Transição: {tr.name}</strong>
                      <span style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '4px', background: tr.is_active ? '#059669' : '#cbd5e1', color: '#ffffff' }}>
                        {tr.is_active ? 'AUTORIZADA' : 'PENDENTE'}
                      </span>
                    </div>
                    {tr.requires?.map((req, rIdx) => (
                      <div key={rIdx} style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px', color: req.valid ? '#059669' : '#94a3b8' }}>
                        {req.valid ? <CheckCircle2 size={12} /> : <XCircle size={12} />} {req.requirement}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* EDITOR IDE */}
        {activeTab === 'editor' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px', height: 'calc(100vh - 120px)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#475569', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={14} /> Fonte do Contrato (.jur)
                </span>
                <span style={{ fontSize: '11px', color: isSaved ? '#059669' : '#d97706' }}>
                  {isSaved ? 'Sincronizado' : 'Modificações não salvas'}
                </span>
              </div>
              <textarea 
                value={code} 
                onChange={(e) => { setCode(e.target.value); setIsSaved(false); }}
                style={{ flex: 1, padding: '16px', border: 'none', resize: 'none', outline: 'none', fontFamily: 'JetBrains Mono, monospace', fontSize: '13px', lineHeight: '1.6', background: '#fafafa', color: '#1e293b' }}
              />
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', marginBottom: '8px' }}>Árvore Sintática (AST)</h4>
                <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#475569', background: '#f1f5f9', padding: '10px', borderRadius: '4px', overflowX: 'auto' }}>
                  <pre>{JSON.stringify(result?.contracts?.[0] || {}, null, 2)}</pre>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
