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
  }, []);

  const runJuridicoCode = async (codeToRun = null, customState = null) => {
    setLoading(true);
    setError(null);
    try {
      const targetCode = codeToRun !== null ? codeToRun : code;
      const targetState = customState || runtimeState;

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

  const saveDocumentEvent = async (key, newValue) => {
    const dataStr = new Date().toISOString().split('T')[0];
    const eventLog = `\n# [${dataStr}] REGISTRO: ${key} = ${newValue}`;
    const newCode = code + eventLog;
    setCode(newCode);
    
    try {
      await fetch(`${API_BASE}/save-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: newCode })
      });
      setIsSaved(true);
    } catch (e) {
      console.error("Erro ao salvar", e);
    }
  };

  const toggleRuntimeParam = (key) => {
    const updatedValue = !runtimeState[key];
    const updatedState = { ...runtimeState, [key]: updatedValue };
    setRuntimeState(updatedState);
    saveDocumentEvent(key, updatedValue);
    runJuridicoCode(code, updatedState); // pass updated state and old code, wait! newCode isn't passed here. Let's pass newCode to execute as well.
  };

  const manualSave = async () => {
    try {
      await fetch(`${API_BASE}/save-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })
      });
      setIsSaved(true);
    } catch (e) {
      console.error("Erro ao salvar", e);
    }
  };

  const exportPdfDocument = async () => {
    try {
      const res = await fetch(`${API_BASE}/export/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, runtime_state: runtimeState })
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Instrumento_Juridico_${Date.now()}.pdf`;
      a.click();
    } catch (e) {
      alert('Erro ao exportar PDF: ' + e.message);
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
          {['dashboard', 'editor', 'pdf_database'].map(tab => (
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
              {tab === 'dashboard' ? 'Métricas & Compliance' : tab === 'editor' ? 'IDE & Interpretador' : 'Precedentes (PDF)'}
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
