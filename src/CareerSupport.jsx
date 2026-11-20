import Coligacoes from './Coligacoes.jsx';

/** Parte de App.jsx: linha:362. Recebe do App o estado e as ações de que precisa. */
export default function CareerSupport({ busy, inviteParty, overview }) {
  return (
    <section className="panel"><Coligacoes view={overview.coalition} tv={overview.tv} busy={busy} onInvite={inviteParty} /></section>
  );
}
