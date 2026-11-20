import { AdvanceMenu } from './Shell';
import Brand from './Brand';
import { OFFICE_STATUS_LABEL } from './appData.jsx';
import { signOut } from 'aws-amplify/auth';

/** Parte de App.jsx: linha:405. Recebe do App o estado e as ações de que precisa. */
export default function TopBar({ advance, advanceOpen, authConfig, authUser, busy, careerMode, dateLabel, gameGuideOpen, partyMode, setAdvanceOpen, setAuthUser, setGameGuideOpen, setNotice, setShowAccountPanel, setShowAuthPanel, setShowGameMenu, setState, state, termMonth }) {
  return (
    <header className="ds-top"><Brand /><div className="ds-date"><span>{dateLabel}</span><small>{careerMode ? `${state.career_overview.office_label} · ${state.career_overview.campaign_territory || state.career_overview.state_name} · ${({ pre_campaign: 'pré-campanha', campaign: 'campanha', transition: 'transição para a posse', office: 'no mandato', opposition: 'fora do cargo', term_complete: 'mandato concluído', runoff_campaign: 'segundo turno', runoff_observer: 'apuração do segundo turno' })[state.career_overview.phase] || state.career_overview.phase.replaceAll('_', ' ')}` : (partyMode ? `TRAJETÓRIA PARTIDÁRIA · ${String(state.party_path.stage).replaceAll('_', ' ').toUpperCase()}` : `MÊS ${termMonth} DE 48 · DIA ${state.day_of_mandate} DE 1461 · ${OFFICE_STATUS_LABEL[state.office_status || 'incumbent'] || String(state.office_status).replaceAll('_', ' ')}`)}</small></div><div className="ds-top-actions">{authConfig?.enabled && (authUser?.isGuest ? <button className="ds-btn" onClick={() => { setShowAuthPanel(true); setNotice(""); }}>Entrar / criar conta</button> : <><button className="ds-btn" onClick={() => setShowAccountPanel(true)}>Conta</button><button className="ds-btn" onClick={async () => { await signOut(); setAuthUser(null); setState(null); setShowGameMenu(true); }}>Sair</button></>)}<button type="button" className="ds-btn" onClick={() => setGameGuideOpen((open) => !open)} aria-pressed={gameGuideOpen}>Guia</button><button type="button" className="ds-btn" onClick={() => setShowGameMenu(true)}>Partidas</button><AdvanceMenu open={advanceOpen} setOpen={setAdvanceOpen} busy={busy} advance={advance} /></div></header>
  );
}
