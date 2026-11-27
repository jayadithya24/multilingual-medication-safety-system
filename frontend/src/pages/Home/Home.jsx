import HeroSection from "../../components/HeroSection/HeroSection";
import FeatureCard from "../../components/FeatureCard/FeatureCard";
import StatsSection from "../../components/StatsSection/StatsSection";
import Workflow from "../../components/Workflow/Workflow";

import "./Home.css";

function Home() {

    return (

        <>

            <HeroSection />

            <StatsSection />

            <section className="features">

                <h2>Our Features</h2>

                <div className="feature-grid">

                    <FeatureCard
                        icon="💊"
                        title="Medicine Search"
                        description="Search medicines and view complete information."
                    />

                    <FeatureCard
                        icon="📷"
                        title="OCR Sample"
                        description="View predefined scan output; images are not uploaded or processed."
                    />

                    <FeatureCard
                        icon="🎤"
                        title="Voice Sample"
                        description="Explore predefined multilingual examples; audio is not uploaded or transcribed."
                    />

                    <FeatureCard
                        icon="⚠"
                        title="Drug Interaction"
                        description="Check recorded sample pairs from the bundled reference dataset."
                    />

                </div>

            </section>

            <Workflow />

        </>

    );

}

export default Home;