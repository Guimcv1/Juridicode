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
  const [activeTab, setActiveTab] = useState('dashboard');
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
    custom_clauses: []
  });
  const [signer, setSigner] = useState({ name: '', document: '', email: '', consent: false });
  const [signatureMessage, setSignatureMessage] = useState('');
  const [footerImageName, setFooterImageName] = useState('');
  const [drafts, setDrafts] = useState([]);
  const [databaseInfo, setDatabaseInfo] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(true);

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

  const loadDraft = async (id) => {
    const res = await fetch(`${API_BASE}/contracts/${id}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Não foi possível abrir o modelo.');
    setDraftId(data.id);
    setDraftName(data.name);
    setCode(data.code);
    setFormatting(data.formatting || { margins: { top: 40, right: 40, bottom: 40, left: 40 }, custom_clauses: [] });
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
    setSignatureMessage(`Assinatura registrada em ${new Date(data.signed_at).toLocaleString()} · hash ${data.document_sha256.slice(0, 16)}...`);
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
    const res = await fetch(`${API_BASE}/pdf/footer-image`, { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Não foi possível enviar a imagem.');
    setFooterImageName(data.filename);
    setFormatting(prev => ({ ...prev, footer_image: data.filename }));
  };

  const updateClause = (index, field, value) => {
    setFormatting(prev => ({
      ...prev,
      custom_clauses: prev.custom_clauses.map((clause, clauseIndex) =>
        clauseIndex === index ? { ...clause, [field]: value } : clause
      )
    }));
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
        padding: '12px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
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

        <div style={{ display: 'flex', gap: '6px', background: '#f1f5f9', padding: '4px', borderRadius: '6px' }}>
          {['dashboard', 'editor', 'contract', 'models', 'database', 'pdf_database'].map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)} 
              style={{ 
                background: activeTab === tab ? '#ffffff' : 'transparent',
                color: activeTab === tab ? '#0f172a' : '#64748b',
                boxShadow: activeTab === tab ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                border: 'none', borderRadius: '4px', fontSize: '12px', padding: '6px 14px', fontWeight: '600', cursor: 'pointer'
              }}
            >
              {tab === 'dashboard' ? 'Métricas & Compliance' : tab === 'editor' ? 'IDE & Interpretador' : tab === 'contract' ? 'Contrato & Estilo' : tab === 'models' ? 'Modelos salvos' : tab === 'database' ? 'Banco de dados' : 'Precedentes (PDF)'}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            onClick={manualSave}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', border: '1px solid #cbd5e1', color: '#475569', fontSize: '12px', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}
          >
            <Save size={14} /> {isSaved ? 'Salvo' : 'Salvar Alterações'}
          </button>

          <button 
            onClick={() => runJuridicoCode()} 
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#0f172a', color: '#ffffff', border: 'none', fontSize: '12px', padding: '6px 16px', borderRadius: '4px', fontWeight: '600', cursor: 'pointer' }}
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
                  </div>
                ))}
                <button onClick={addClause} style={{ padding: '7px 10px', cursor: 'pointer' }}>+ Adicionar cláusula</button>
                <label style={{ display: 'block', marginTop: '14px', fontSize: '12px' }}>
                  Imagem do rodapé (PNG/JPG)
                  <input type="file" accept=".png,.jpg,.jpeg" onChange={e => uploadFooterImage(e).catch(err => setError(err.message))}
                    style={{ display: 'block', marginTop: '5px' }} />
                </label>
                {footerImageName && <div style={{ fontSize: '11px', color: '#047857', marginTop: '5px' }}>Rodapé: {footerImageName}</div>}
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
                <p style={{ fontSize: '11px', color: '#64748b' }}>O sistema registra identidade informada, consentimento, data e hash do conteúdo assinado.</p>
                {signatureMessage && <div style={{ color: '#047857', fontSize: '12px' }}>{signatureMessage}</div>}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'models' && (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '22px' }}>
            <h2 style={{ marginTop: 0 }}>Modelos e textos salvos</h2>
            <p style={{ color: '#64748b', fontSize: '13px' }}>Cada modelo contém o texto .jur e a configuração visual salva.</p>
            {drafts.length === 0 && <p>Nenhum modelo salvo ainda.</p>}
            {drafts.map(draft => (
              <div key={draft.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '1px solid #e2e8f0' }}>
                <div><strong>{draft.name}</strong><div style={{ color: '#64748b', fontSize: '11px' }}>Atualizado: {new Date(draft.updated_at).toLocaleString()}</div></div>
                <button onClick={() => loadDraft(draft.id).catch(e => setError(e.message))} style={{ padding: '7px 12px', cursor: 'pointer' }}>Abrir e editar</button>
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
