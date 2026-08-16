import { useEffect, useMemo, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import api from "../../services/api";

import "./KnowledgeGraph.css";

function KnowledgeGraph({ drug1 = "", drug2 = "" }) {

    const [graphData, setGraphData] = useState({
        nodes: [],
        links: [],
    });

    const [disease, setDisease] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");


    // =========================================================
    // Load graph
    // =========================================================

    useEffect(() => {

        const loadGraph = async () => {

            /*
             * Do not load anything until two medicines
             * have been selected.
             */

            if (!drug1 || !drug2) {

                setGraphData({
                    nodes: [],
                    links: [],
                });

                setDisease("");

                return;
            }


            try {

                setLoading(true);
                setError("");


                const response = await api.get(
                    "/neo4j/interaction-graph",
                    {
                        params: {
                            drug1,
                            drug2
                        }
                    }
                );


                console.log(
                    "Interaction Graph Data:",
                    response.data
                );


                setGraphData({
                    nodes: response.data.nodes || [],
                    links:
                        response.data.links ||
                        response.data.edges ||
                        [],
                });


                setDisease(
                    response.data.disease || ""
                );


            } catch (err) {

                console.error(
                    "Interaction graph error:",
                    err
                );

                setError(
                    "Unable to load the medication interaction graph."
                );

            } finally {

                setLoading(false);

            }

        };


        loadGraph();

    }, [drug1, drug2]);


    // =========================================================
    // Normalize graph
    // =========================================================

    const safeGraphData = useMemo(() => {

        const nodes = (graphData.nodes || []).map(
            (node) => ({

                ...node,

                id: String(
                    node.node_id ||
                    node.id ||
                    node.name
                ).trim(),

                label:
                    node.name ||
                    node.node_id

            })
        );


        const nodeIds = new Set(
            nodes.map(
                (node) => node.id
            )
        );


        const normalizeId = (value) => {

            if (!value) {
                return null;
            }


            if (typeof value === "object") {

                return String(
                    value.node_id ||
                    value.id ||
                    value.name ||
                    ""
                ).trim();

            }


            return String(value).trim();

        };


        const links = (graphData.links || [])
            .map((link) => ({

                ...link,

                source:
                    normalizeId(link.source),

                target:
                    normalizeId(link.target)

            }))
            .filter(
                (link) =>
                    link.source &&
                    link.target &&
                    nodeIds.has(link.source) &&
                    nodeIds.has(link.target)
            );


        console.log(
            "Interaction graph nodes:",
            nodes.length
        );

        console.log(
            "Interaction graph links:",
            links.length
        );


        return {
            nodes,
            links
        };

    }, [graphData]);


    // =========================================================
    // Loading
    // =========================================================

    if (loading) {

        return (
            <div className="knowledge-graph__loading">
                Loading interaction graph...
            </div>
        );

    }


    // =========================================================
    // Error
    // =========================================================

    if (error) {

        return (
            <div className="knowledge-graph__error">
                {error}
            </div>
        );

    }


    // =========================================================
    // No medicines selected
    // =========================================================

    if (!drug1 || !drug2) {

        return null;

    }


    // =========================================================
    // Empty graph
    // =========================================================

    if (!safeGraphData.nodes.length) {

        return (
            <div className="knowledge-graph__empty">
                No relationship data found for the selected medicines.
            </div>
        );

    }


    // =========================================================
    // Render
    // =========================================================

    return (

        <div className="knowledge-graph">

            {/* Header */}

            <div className="knowledge-graph__header">

                <div>

                    <span className="knowledge-graph__label">
                        MEDICATION RELATIONSHIP
                    </span>

                    <h2>
                        Drug Interaction Graph
                    </h2>

                    <p>

                        {disease
                            ? `Relationships between ${drug1}, ${drug2}, and medicines associated with ${disease}.`
                            : `Relationship between ${drug1} and ${drug2}.`
                        }

                    </p>

                </div>


                <div className="knowledge-graph__stats">

                    <div>

                        <strong>
                            {safeGraphData.nodes.length}
                        </strong>

                        <span>
                            Nodes
                        </span>

                    </div>


                    <div>

                        <strong>
                            {safeGraphData.links.length}
                        </strong>

                        <span>
                            Relationships
                        </span>

                    </div>

                </div>

            </div>


            {/* Legend */}

            <div className="knowledge-graph__legend">

                <span>

                    <i className="legend-dot legend-dot--drug"></i>

                    Medicine

                </span>


                <span>

                    <i className="legend-dot legend-dot--disease"></i>

                    Disease

                </span>


                <span>

                    <i
                        className="legend-dot"
                        style={{
                            backgroundColor: "#ef4444"
                        }}
                    ></i>

                    Drug Interaction

                </span>

            </div>


            {/* Graph */}

            <div className="knowledge-graph__canvas">

                <ForceGraph2D

                    graphData={safeGraphData}

                    nodeId="id"

                    linkSource="source"

                    linkTarget="target"


                    nodeLabel={(node) =>
                        node.label || node.id
                    }


                    nodeCanvasObject={(
                        node,
                        ctx,
                        globalScale
                    ) => {

                        const label =
                            node.label ||
                            node.id;


                        const isSelected =
                            label === drug1 ||
                            label === drug2;


                        const isDisease =
                            node.type === "disease";


                        let nodeColor =
                            "#3b82f6";


                        if (isDisease) {

                            nodeColor =
                                "#10b981";

                        }


                        const radius =
                            isDisease
                                ? 14
                                : isSelected
                                    ? 12
                                    : 7;


                        ctx.beginPath();

                        ctx.arc(
                            node.x,
                            node.y,
                            radius,
                            0,
                            2 * Math.PI
                        );


                        ctx.fillStyle =
                            nodeColor;

                        ctx.fill();


                        /*
                         * White border around selected
                         * medicines and disease.
                         */

                        if (
                            isSelected ||
                            isDisease
                        ) {

                            ctx.strokeStyle =
                                "#ffffff";

                            ctx.lineWidth =
                                2;

                            ctx.stroke();

                        }


                        const fontSize =
                            (
                                isSelected ||
                                isDisease
                            )
                                ? 14 / globalScale
                                : 10 / globalScale;


                        ctx.font =
                            `${fontSize}px Inter, Arial, sans-serif`;


                        ctx.textAlign =
                            "center";


                        ctx.textBaseline =
                            "top";


                        ctx.fillStyle =
                            "#ffffff";


                        ctx.fillText(
                            label,
                            node.x,
                            node.y + radius + 4
                        );

                    }}


                    linkColor={(link) => {

                        if (
                            link.relationship ===
                            "INTERACTS_WITH"
                        ) {

                            return "#ef4444";

                        }


                        if (
                            link.relationship ===
                            "TREATS"
                        ) {

                            return "#10b981";

                        }


                        return "#64748b";

                    }}


                    linkWidth={(link) => {

                        if (
                            link.relationship ===
                            "INTERACTS_WITH"
                        ) {

                            return 3;

                        }


                        if (
                            link.relationship ===
                            "TREATS"
                        ) {

                            return 2;

                        }


                        return 1;

                    }}


                    linkDirectionalArrowLength={5}

                    linkDirectionalArrowRelPos={1}


                    linkLabel={(link) => {

                        if (
                            link.relationship ===
                            "INTERACTS_WITH"
                        ) {

                            return (
                                `INTERACTS_WITH — ${
                                    link.severity ||
                                    "Unknown severity"
                                }`
                            );

                        }


                        if (
                            link.relationship ===
                            "TREATS"
                        ) {

                            return "TREATS";

                        }


                        return link.relationship || "";

                    }}


                    width={1000}

                    height={550}

                    backgroundColor="#0b1220"

                    cooldownTicks={150}

                    d3VelocityDecay={0.35}

                    enableZoomInteraction={true}

                    enablePanInteraction={true}


                    onNodeClick={(node) => {

                        console.log(
                            "Selected graph node:",
                            node
                        );

                    }}

                />

            </div>

        </div>

    );

}

export default KnowledgeGraph;