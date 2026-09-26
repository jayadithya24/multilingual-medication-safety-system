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
                        title="OCR Scanner"
                        description="Upload medicine images to identify tablets."
                    />

                    <FeatureCard
                        icon="🎤"
                        title="Voice Assistant"
                        description="Search medicines using multilingual voice input."
                    />

                    <FeatureCard
                        icon="⚠"
                        title="Drug Interaction"
                        description="Analyze interactions between medicines."
                    />

                </div>

            </section>

            <Workflow />

        </>

    );

}

export default Home;