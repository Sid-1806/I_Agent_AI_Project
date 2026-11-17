// Page title with a subtitle and controls on the right.
export default function PageHeader({ title, subtitle, controls }) {
  return (
    <div className="page-header">
      <div className="page-title">
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {controls && <div className="page-controls">{controls}</div>}
    </div>
  );
}
