// Shared building blocks.

export function Badge({ tone = "muted", dot = false, children }) {
  return (
    <span className={`badge tone-${tone}`}>
      {dot && <i className="badge-dot" />}
      {children}
    </span>
  );
}

export function Card({ className = "", children }) {
  return <section className={`card ${className}`}>{children}</section>;
}

export function CardHead({ icon: Icon, title, children }) {
  return (
    <header className="card-head">
      <h2>
        {Icon && <Icon size={16} strokeWidth={2} />}
        {title}
      </h2>
      {children && <div className="card-head-side">{children}</div>}
    </header>
  );
}

export function Segmented({ options, value, onChange, disabled, label }) {
  return (
    <div className="segmented" role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} type="button" role="radio" aria-checked={value === o.value} className={value === o.value ? "on" : ""} onClick={() => onChange(o.value)} disabled={disabled} title={o.title}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Select({ value, onChange, label, disabled, children }) {
  return (
    <select className="select" value={value} onChange={(e) => onChange(e.target.value)} aria-label={label} disabled={disabled}>
      {children}
    </select>
  );
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}
