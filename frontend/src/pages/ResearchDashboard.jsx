import DashboardCard from "../components/DashboardCard";

function ResearchDashboard() {
  return (
    <div className="page-shell">
      <section className="section-header">
        <span className="hero__kicker">Research workspace</span>
        <h1>Research Dashboard</h1>
        <p>
          Explore medicines, interaction signals, and reporting tools in a
          focused workspace for advanced review.
        </p>
      </section>

      <div className="dashboard-grid">
        <DashboardCard title="Drug Search" badge="Lookup" description="Find drug details quickly across multilingual records." />

        <DashboardCard title="Drug Interactions" badge="Safety" description="Review high-risk combinations and interaction notes." />

        <DashboardCard title="Knowledge Graph" badge="Insights" description="Connect medications, conditions, and safety context." />

        <DashboardCard title="Reports" badge="Export" description="Summarize research findings and review outcomes." />
      </div>
    </div>
  );
}

export default ResearchDashboard;