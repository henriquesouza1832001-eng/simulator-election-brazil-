import { useEffect, useState } from 'react';
import { confirmUserAttribute, fetchUserAttributes, sendUserAttributeVerificationCode } from 'aws-amplify/auth';

export default function AccountPanel({ onClose }) {
  const [attributes, setAttributes] = useState(null);
  const [code, setCode] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  async function load() {
    const data = await fetchUserAttributes();
    setAttributes(data);
  }

  useEffect(() => { load().catch((error) => setNotice(error.message)); }, []);

  async function sendCode() {
    setBusy(true);
    setNotice('');
    try {
      const result = await sendUserAttributeVerificationCode({ userAttributeKey: 'email' });
      setSent(true);
      setNotice(`Código enviado para ${result.codeDeliveryDetails?.destination || attributes?.email || 'seu e-mail'}.`);
    } catch (error) { setNotice(error?.message || 'Não foi possível enviar o código.'); }
    finally { setBusy(false); }
  }

  async function verify(event) {
    event.preventDefault();
    setBusy(true);
    setNotice('');
    try {
      await confirmUserAttribute({ userAttributeKey: 'email', confirmationCode: code.trim() });
      await load();
      setSent(false);
      setCode('');
      setNotice('E-mail confirmado. A recuperação de senha ficará disponível para esta conta.');
    } catch (error) { setNotice(error?.message || 'Código inválido ou expirado.'); }
    finally { setBusy(false); }
  }

  return <div className="account-overlay" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="account-card" role="dialog" aria-modal="true" aria-labelledby="account-title">
      <button className="account-close" onClick={onClose} aria-label="Fechar">×</button>
      <span className="eyebrow">CONTA DO JOGADOR</span>
      <h2 id="account-title">Acesso e recuperação</h2>
      {!attributes ? <p>Carregando os dados da conta…</p> : <>
        <div className="account-email"><span>E-MAIL</span><b>{attributes.email || 'Não informado'}</b><small>{attributes.email_verified === 'true' ? 'Confirmado · recuperação ativa' : 'Ainda não confirmado · recuperação de senha indisponível'}</small></div>
        {attributes.email_verified !== 'true' && !sent && <button className="primary-button" onClick={sendCode} disabled={busy}>{busy ? 'Enviando…' : 'Confirmar e-mail para recuperar senha'}</button>}
        {sent && <form className="account-verify" onSubmit={verify}><label>Código enviado ao e-mail<input inputMode="numeric" autoComplete="one-time-code" value={code} onChange={(event) => setCode(event.target.value)} maxLength={12} required /></label><button className="primary-button" disabled={busy}>{busy ? 'Verificando…' : 'Confirmar e-mail'}</button></form>}
        {attributes.email_verified === 'true' && <p className="account-success">Seu e-mail está verificado e pode receber códigos de recuperação.</p>}
      </>}
      {notice && <p className="auth-notice" role="status">{notice}</p>}
      <small className="auth-provider-note">A identidade pertence ao Cognito; o jogo usa somente o identificador autenticado para separar suas partidas.</small>
    </section>
  </div>;
}
