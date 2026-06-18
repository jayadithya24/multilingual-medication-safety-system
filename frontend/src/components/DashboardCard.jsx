function DashboardCard({ title, description, badge }) {
  return (
    <div className="feature-card">
      <div className="feature-card__header">
        <span className="feature-card__badge">{badge ?? "Module"}</span>
        <span className="feature-card__arrow">→</span>
      </div>

      <h3>{title}</h3>

      {description ? <p>{description}</p> : null}
    </div>
  );
}

export default DashboardCard;