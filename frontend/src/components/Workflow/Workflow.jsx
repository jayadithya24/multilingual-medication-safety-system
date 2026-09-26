import React from "react";
import "./Workflow.css";

function Workflow() {

    const steps = [

        "📷 Scan Medicine",

        "📝 OCR Extraction",

        "🎤 Voice Translation",

        "⚠ Drug Interaction",

        "🧠 Knowledge Graph"

    ];

    return (

        <section className="workflow">

            <h2>How Our System Works</h2>

            <div className="workflow-container">

                {

                    steps.map((step,index)=>(
                        <React.Fragment key={index}>
                            <div className="workflow-card">
                                {step}
                            </div>
                            {index!==steps.length-1 && (
                                <span className="arrow">➜</span>
                            )}
                        </React.Fragment>
                    ))

                }

            </div>

        </section>

    );

}

export default Workflow;