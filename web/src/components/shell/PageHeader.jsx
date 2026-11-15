// Page title with a subtitle, controls on the right, and a row of filters underneath.
export default function PageHeader({ title, subtitle, controls, filters, side }) {
  return (
    <div className="page-header">
      <div className="page-title-row">
        <div className="page-title">
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {controls && <div className="page-controls">{controls}</div>}
      </div>
      {(filters || side) && (
        <div className="page-filter-row">
          <div className="chips">{filters}</div>
          <div className="page-filter-side">{side}</div>
        </div>
      )}
    </div>
  );
}
