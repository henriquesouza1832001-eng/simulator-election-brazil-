import './measure-forecast.css';

const number = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 });

function display(value) {
  return number.format(Number(value) || 0);
}

export default function MeasureForecast({ forecast }) {
  if (!forecast?.timeline?.length) return null;

  return <section className="measure-forecast">
    <div className="measure-forecast-heading">
      <div><span className="eyebrow">EFEITO DIRETO · SIMULAÇÃO</span><h4>O que pode mudar</h4></div>
      <span>se a medida for aplicada</span>
    </div>
    <div className="measure-impact-summary">
      {forecast.impact_if_applied?.map((metric) => <article key={metric.key}>
        <span>{metric.label}</span>
        <b>{display(metric.before)} → {display(metric.after)} <small>{metric.unit}</small></b>
        <small>Δ {metric.delta > 0 ? '+' : ''}{display(metric.delta)} {metric.unit}</small>
      </article>)}
    </div>
    <details className="measure-forecast-details">
      <summary>Ver a evolução até 12 meses</summary>
      <div className="measure-timeline">
        {forecast.timeline.map((stage) => <article key={stage.day} className={stage.conditional_on_approval ? 'conditional' : ''}>
          <div className="measure-stage-heading"><b>{stage.label}</b><span>{stage.status}</span></div>
          <div className="measure-stage-metrics">
            {stage.metrics.map((metric) => <div key={metric.key}>
              <span>{metric.label}</span><b>{display(metric.after)} <small>{metric.unit}</small></b>
            </div>)}
          </div>
        </article>)}
      </div>
      <ul className="measure-forecast-notes">{forecast.notes?.map((note) => <li key={note}>{note}</li>)}</ul>
    </details>
  </section>;
}
