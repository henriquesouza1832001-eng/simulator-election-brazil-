import { useState } from 'react';
import {
  confirmResetPassword,
  confirmSignIn,
  confirmSignUp,
  getCurrentUser,
  resendSignUpCode,
  resetPassword,
  signIn,
  signUp,
} from 'aws-amplify/auth';

const messages = {
  login: { title: 'Entre na sua conta', subtitle: 'Sua campanha fica salva e separada das outras partidas.' },
  signup: { title: 'Crie sua conta', subtitle: 'Use um e-mail válido para proteger a recuperação da conta.' },
  confirm: { title: 'Confirme sua conta', subtitle: 'Digite o código enviado pelo Cognito para concluir o cadastro.' },
  forgot: { title: 'Recupere o acesso', subtitle: 'Vamos enviar um código ao e-mail confirmado da sua conta.' },
  reset: { title: 'Defina uma nova senha', subtitle: 'Digite o código recebido e escolha outra senha.' },
  challenge: { title: 'Confirme o acesso', subtitle: 'Digite o código de segurança solicitado pela sua conta.' },
};

export default function AuthPanel({ onAuthenticated, notice, setNotice }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);

  async function finishSignIn() {
    onAuthenticated(await getCurrentUser());
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setNotice('');
    try {
      if (mode === 'login') {
        const result = await signIn({ username: email.trim(), password });
        if (result.isSignedIn) return await finishSignIn();
        if (result.nextStep.signInStep === 'CONFIRM_SIGN_UP') {
          setMode('confirm');
          setNotice('Este cadastro ainda precisa ser confirmado.');
        } else if (result.nextStep.signInStep === 'RESET_PASSWORD') {
          setMode('forgot');
          setNotice('A conta precisa de uma nova senha. Solicite o código de recuperação.');
        } else if (result.nextStep.signInStep.startsWith('CONFIRM_SIGN_IN')) {
          setMode('challenge');
          setNotice('A conta pediu uma confirmação adicional.');
        } else {
          setNotice(`A autenticação precisa de outra etapa: ${result.nextStep.signInStep}.`);
        }
      } else if (mode === 'signup') {
        const result = await signUp({ username: email.trim(), password, options: { userAttributes: { email: email.trim() } } });
        if (result.isSignUpComplete || result.nextStep.signUpStep === 'DONE') {
          const signedIn = await signIn({ username: email.trim(), password });
          if (signedIn.isSignedIn) return await finishSignIn();
        }
        if (result.nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
          setMode('confirm');
          setNotice(`O código de confirmação foi enviado para ${email.trim()}.`);
        } else {
          setNotice('Cadastro criado. Entre com seu e-mail e senha.');
          setMode('login');
        }
      } else if (mode === 'confirm') {
        await confirmSignUp({ username: email.trim(), confirmationCode: code.trim() });
        const signedIn = await signIn({ username: email.trim(), password });
        if (signedIn.isSignedIn) return await finishSignIn();
        setMode('login');
        setNotice('Cadastro confirmado. Entre com sua senha.');
      } else if (mode === 'forgot') {
        const result = await resetPassword({ username: email.trim() });
        if (result.nextStep.resetPasswordStep === 'CONFIRM_RESET_PASSWORD_WITH_CODE') {
          setMode('reset');
          setNotice(`O código de recuperação foi enviado para ${result.nextStep.codeDeliveryDetails.destination || 'seu e-mail'}.`);
        } else setNotice('A recuperação foi concluída. Entre com sua nova senha.');
      } else if (mode === 'reset') {
        await confirmResetPassword({ username: email.trim(), confirmationCode: code.trim(), newPassword });
        setPassword(newPassword);
        setNewPassword('');
        setCode('');
        setMode('login');
        setNotice('Senha atualizada. Entre com a nova senha.');
      } else if (mode === 'challenge') {
        const result = await confirmSignIn({ challengeResponse: code.trim() });
        if (result.isSignedIn) return await finishSignIn();
        setNotice(`Ainda falta concluir: ${result.nextStep.signInStep}.`);
      }
    } catch (error) {
      setNotice(error?.message || 'Não foi possível concluir a autenticação. Confira os dados e tente novamente.');
    } finally {
      setBusy(false);
    }
  }

  async function resendCode() {
    setBusy(true);
    setNotice('');
    try {
      await resendSignUpCode({ username: email.trim() });
      setNotice(`Um novo código foi enviado para ${email.trim()}.`);
    } catch (error) {
      setNotice(error?.message || 'Não foi possível enviar outro código.');
    } finally {
      setBusy(false);
    }
  }

  const needsPassword = ['login', 'signup'].includes(mode);
  const needsCode = ['confirm', 'reset', 'challenge'].includes(mode);
  const heading = messages[mode];

  return <main className="auth-screen"><section className="auth-card">
    <span className="brand-mark">M</span>
    <div className="eyebrow">MANDATO · CONTA DO JOGADOR</div>
    <h1>{heading.title}</h1>
    <p>{heading.subtitle}</p>
    <form className="auth-form" onSubmit={submit}>
      <label>E-mail<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required disabled={busy || mode === 'challenge'} /></label>
      {needsPassword && <label>Senha<input type="password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} minLength={12} pattern={mode === 'signup' ? '(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{12,}' : undefined} title="Use 12 caracteres ou mais, com maiúscula, minúscula, número e símbolo." required disabled={busy} /></label>}
      {mode === 'reset' && <label>Nova senha<input type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={12} pattern="(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{12,}" title="Use 12 caracteres ou mais, com maiúscula, minúscula, número e símbolo." required disabled={busy} /></label>}
      {needsCode && <label>{mode === 'challenge' ? 'Código de segurança' : 'Código enviado por e-mail'}<input inputMode="numeric" autoComplete="one-time-code" value={code} onChange={(event) => setCode(event.target.value)} maxLength={12} required disabled={busy} /></label>}
      {mode === 'signup' && <small className="auth-password-hint">Cadastro sem código de confirmação. Use uma senha de 12+ caracteres com maiúscula, minúscula, número e símbolo.</small>}
      <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Aguarde…' : ({ login: 'Entrar', signup: 'Criar conta', confirm: 'Confirmar cadastro', forgot: 'Enviar código', reset: 'Atualizar senha', challenge: 'Confirmar acesso' })[mode]} <b>→</b></button>
    </form>
    {mode === 'login' && <div className="auth-links"><button type="button" onClick={() => { setMode('signup'); setNotice(''); }}>Criar conta</button><button type="button" onClick={() => { setMode('forgot'); setNotice(''); }}>Esqueci a senha</button></div>}
    {mode === 'signup' && <div className="auth-links"><button type="button" onClick={() => { setMode('login'); setNotice(''); }}>Já tenho uma conta</button></div>}
    {mode === 'confirm' && <div className="auth-links"><button type="button" onClick={resendCode} disabled={busy}>Enviar outro código</button><button type="button" onClick={() => { setMode('login'); setNotice(''); }}>Voltar ao acesso</button></div>}
    {['forgot', 'reset', 'challenge'].includes(mode) && <div className="auth-links"><button type="button" onClick={() => { setMode('login'); setCode(''); setNotice(''); }}>Voltar ao acesso</button></div>}
    {notice && <p className="auth-notice" role="status">{notice}</p>}
    <small className="auth-provider-note">As senhas ficam no Amazon Cognito, não no jogo. A conta entra sem confirmar o e-mail; para recuperar a senha, valide o endereço na área Conta após entrar.</small>
  </section></main>;
}
