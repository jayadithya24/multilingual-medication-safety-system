import DashboardCard from "../components/DashboardCard";

function PublicDashboard() {
  return (
    <div className="page-shell">
      <section className="section-header">
        <span className="hero__kicker">Public access</span>
        <h1>Public Dashboard</h1>
        <p>
          A friendly entry point for medicine lookup, prescription upload, and
          simple drug guidance.
        </p>
      </section>

      <div className="dashboard-grid">
        <DashboardCard title="Medicine Search" badge="Search" description="Look up drug names and basic safety information." />

        <DashboardCard title="Upload Prescription" badge="OCR" description="Capture prescription details from an image or file." />

        <DashboardCard title="Voice Search" badge="Assistive" description="Search by speaking for hands-free access." />

        <DashboardCard title="Drug Information" badge="Guide" description="Review usage, warnings, and interaction notes." />
      </div>
    </div>
  );
}

export default PublicDashboard;