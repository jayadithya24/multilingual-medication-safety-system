import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchDiseases } from "../../services/neo4jService";

import KnowledgeGraph from "../../components/KnowledgeGraph/KnowledgeGraph";

import "./DoctorDashboard.css";

function DoctorDashboard() {
    const [scope, setScope] = useState(null);
    const [scopeError, setScopeError] = useState(false);
    useEffect(() => {
        let active = true;
        fetchDiseases("en").then((data) => {
            if (active) setScope(data);
        }).catch(() => {
            if (active) setScopeError(true);
        });
        return () => { active = false; };
    }, []);
    return (
        <div className="doctor-dashboard">

            {/* Header */}
            <section className="doctor-dashboard__welcome">
                <div>
                    <p className="doctor-dashboard__kicker">
                        Clinical Overview
                    </p>

                    <h1>
                        Good morning, Doctor
                    </h1>

                    <p className="doctor-dashboard__subtitle">
                        Review medication safety, drug interactions,
                        and clinical information from one workspace.
                    </p>
                </div>

                <div className="doctor-dashboard__status">
                    <span className="doctor-dashboard__status-dot"></span>
                    Doctor workspace
                </div>
            </section>


            {/* Quick Actions */}
            <section className="doctor-dashboard__section">

                <div className="doctor-dashboard__section-header">
                    <div>
                        <h2>Clinical Tools</h2>
                        <p>
                            Access the tools you use for medication review.
                        </p>
                    </div>
                </div>


                <div className="doctor-dashboard__tools">

                    {/* Drug Interaction */}
                    <Link
                        to="/drug-interaction"
                        className="doctor-tool doctor-tool--primary"
                    >
                        <div className="doctor-tool__icon">
                            ⚡
                        </div>

                        <div className="doctor-tool__content">
                            <span className="doctor-tool__label">
                                SAFETY
                            </span>

                            <h3>
                                Drug Interactions
                            </h3>

                            <p>
                                Check potential interactions between
                                medicines before clinical review.
                            </p>
                        </div>

                        <span className="doctor-tool__arrow">
                            →
                        </span>
                    </Link>


                    {/* Drug Reference */}
                   {/* Drug Reference */}
<Link
    to="/drug-reference"
    className="doctor-tool"
>
    <div className="doctor-tool__icon">
        💊
    </div>

    <div className="doctor-tool__content">
        <span className="doctor-tool__label">
            REFERENCE
        </span>

        <h3>
            Drug Reference
        </h3>

        <p>
            Search medicine information, safety data,
            warnings, and clinical details.
        </p>
    </div>

    <span className="doctor-tool__arrow">
        →
    </span>
</Link>


                    {/* Disease Protocols */}
<Link
     to="/disease-protocols"
    className="doctor-tool"
>
    <div className="doctor-tool__icon">
        🏥
    </div>

    <div className="doctor-tool__content">
        <span className="doctor-tool__label">
            CLINICAL
        </span>

        <h3>
            Disease Protocols
        </h3>

        <p>
            Review disease-specific medication
            information and treatment context.
        </p>
    </div>

    <span className="doctor-tool__arrow">
        →
    </span>
</Link>

                    {/* Clinical Insights */}
<Link
     to="/clinical-insights"
    className="doctor-tool"
>
    <div className="doctor-tool__icon">
        📖
    </div>

    <div className="doctor-tool__content">
        <span className="doctor-tool__label">
            CLINICAL
        </span>

        <h3>
            Clinical Insights
        </h3>

        <p>
            View protocol summaries with curated
            sources and further reading.
        </p>
    </div>

    <span className="doctor-tool__arrow">
        →
    </span>
</Link>

                    
                    {/* Medication Knowledge Graph */}
<Link
    to="/knowledge-graph"
    className="doctor-tool"
>
    <div className="doctor-tool__icon">
        🕸️
    </div>

    <div className="doctor-tool__content">
        <span className="doctor-tool__label">
            INTELLIGENCE
        </span>

        <h3>
            Medication Knowledge Graph
        </h3>

        <p>
            Explore relationships between medicines,
            diseases, and potential drug interactions.
        </p>
    </div>

    <span className="doctor-tool__arrow">
        →
    </span>
</Link>


                 {/* Patient Drug Lists */}
<Link
    to="/doctor-patients"
    className="doctor-tool"
>
    <div className="doctor-tool__icon">
        👤
    </div>

    <div className="doctor-tool__content">
        <span className="doctor-tool__label">
            PATIENTS
        </span>

        <h3>
            Patient Drug Lists
        </h3>

        <p>
            Review medicines currently associated
            with registered patients.
        </p>
    </div>

    <span className="doctor-tool__arrow">
        →
    </span>
</Link>


                </div>

            </section>


            {/* Scope */}
            <section className="doctor-dashboard__scope">

                <div className="doctor-dashboard__scope-icon">
                    ✓
                </div>

                <div>
                    <span className="doctor-dashboard__scope-label">
                        CURRENT DATA SCOPE
                    </span>

                    <h3>
                        {scope
                            ? `${scope.medicine_count} medicines across ${scope.diseases.length} diseases`
                            : "Medication Safety Dataset"}
                    </h3>

                    <p>
                        {scope ? scope.diseases.join(" · ")
                            : scopeError ? "Dataset scope is currently unavailable."
                            : "Loading English dataset scope..."}
                    </p>
                    <p>Medicine references and disease lists are available in English, Kannada and Tulu.</p>
                </div>

            </section>

{/* Knowledge Graph */}

<section className="doctor-dashboard__section doctor-dashboard__graph-section">

    <div className="doctor-dashboard__section-header">

        <div>
            <h2>
                Medication Knowledge Graph
            </h2>

            <p>
                Explore medicines, diseases, side effects,
                and drug interaction relationships.
            </p>
        </div>

    </div>

    <KnowledgeGraph />

</section>
            {/* Recent Analyses */}
            <section className="doctor-dashboard__section">

                <div className="doctor-dashboard__section-header">
                    <div>
                        <h2>Recent Analyses</h2>
                        <p>
                            Your latest medication safety reviews will
                            appear here.
                        </p>
                    </div>

                    <Link
                        to="/drug-interaction"
                        className="doctor-dashboard__view-link"
                    >
                        New Analysis →
                    </Link>
                </div>


                <div className="doctor-dashboard__empty">

                    <div className="doctor-dashboard__empty-icon">
                        📋
                    </div>

                    <h3>
                        No recent analyses
                    </h3>

                    <p>
                        Start a drug interaction analysis and your
                        recent reviews will appear here.
                    </p>

                    <Link
                        to="/drug-interaction"
                        className="doctor-dashboard__empty-button"
                    >
                        Start Analysis
                    </Link>

                </div>


            </section>

        </div>
    );
}

export default DoctorDashboard;
