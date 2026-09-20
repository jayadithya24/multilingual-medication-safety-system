import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import api from "../../services/api";
import "./KnowledgeGraph.css";

const NODE_COLORS = {
    drug: { fill: "#38bdf8", stroke: "#0284c7", glow: "rgba(56, 189, 248, 0.4)", label: "Medicine" },
    disease: { fill: "#34d399", stroke: "#059669", glow: "rgba(52, 211, 153, 0.4)", label: "Disease" },
    sideeffect: { fill: "#fbbf24", stroke: "#d97706", glow: "rgba(251, 191, 36, 0.4)", label: "Side Effect" },
    side_effect: { fill: "#fbbf24", stroke: "#d97706", glow: "rgba(251, 191, 36, 0.4)", label: "Side Effect" },
    patient: { fill: "#c084fc", stroke: "#9333ea", glow: "rgba(192, 132, 252, 0.4)", label: "Patient" },
    default: { fill: "#94a3b8", stroke: "#475569", glow: "rgba(148, 163, 184, 0.3)", label: "Entity" },
};

function KnowledgeGraph({ drug1 = "", drug2 = "" }) {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [disease, setDisease] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [selectedNode, setSelectedNode] = useState(null);
    const [hoverNode, setHoverNode] = useState(null);
    const [containerDimensions, setContainerDimensions] = useState({ width: 900, height: 500 });

    const graphRef = useRef(null);
    const containerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;
        const updateDimensions = () => {
            if (containerRef.current) {
                setContainerDimensions({
                    width: containerRef.current.clientWidth || 900,
                    height: 500,
                });
            }
        };
        updateDimensions();
        const observer = new ResizeObserver(updateDimensions);
        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const loadGraph = async () => {
            if (!drug1 || !drug2) {
                setGraphData({ nodes: [], links: [] });
                setDisease("");
                return;
            }
            try {
                setLoading(true);
                setError("");
                const response = await api.get("/neo4j/interaction-graph", {
                    params: { drug1, drug2 },
                });
                const rawNodes = response.data.nodes || [];
                const rawLinks = response.data.links || response.data.edges || [];

                const nodes = rawNodes.map((n) => ({
                    ...n,
                    id: String(n.node_id || n.id || n.name || "").trim(),
                    name: String(n.name || n.node_id || n.id || "").trim(),
                    type: String(n.type || "drug").toLowerCase(),
                }));

                const nodeIds = new Set(nodes.map((n) => n.id));
                const links = rawLinks
                    .map((l) => ({
                        ...l,
                        source: String(typeof l.source === "object" ? l.source.id : l.source).trim(),
                        target: String(typeof l.target === "object" ? l.target.id : l.target).trim(),
                        relationship: String(l.relationship || l.type || "RELATED").toUpperCase(),
                    }))
                    .filter((l) => l.source && l.target && nodeIds.has(l.source) && nodeIds.has(l.target));

                setGraphData({ nodes, links });
                setDisease(response.data.disease || "");
            } catch (err) {
                console.error("Interaction graph error:", err);
                setError("Unable to load the medication interaction graph.");
            } finally {
                setLoading(false);
            }
        };
        loadGraph();
    }, [drug1, drug2]);

    const { neighbors, neighborLinks } = useMemo(() => {
        const activeNode = hoverNode || selectedNode;
        const nSet = new Set();
        const lSet = new Set();

        if (activeNode) {
            nSet.add(activeNode.id);
            graphData.links.forEach((l) => {
                const sId = typeof l.source === "object" ? l.source.id : l.source;
                const tId = typeof l.target === "object" ? l.target.id : l.target;
                if (sId === activeNode.id) {
                    nSet.add(tId);
                    lSet.add(l);
                } else if (tId === activeNode.id) {
                    nSet.add(sId);
                    lSet.add(l);
                }
            });
        }

        return { neighbors: nSet, neighborLinks: lSet };
    }, [graphData, hoverNode, selectedNode]);

    if (loading) {
        return (
            <div className="knowledge-graph__loading">
                <div className="graph-spinner" />
                <span>Loading interaction graph...</span>
            </div>
        );
    }

    if (error) {
        return <div className="knowledge-graph__error">{error}</div>;
    }

    if (!drug1 || !drug2) {
        return null;
    }

    if (!graphData.nodes.length) {
        return <div className="knowledge-graph__empty">No relationship data found for selected medicines.</div>;
    }

    return (
        <div className="knowledge-graph">
            <div className="knowledge-graph__header">
                <div>
                    <span className="knowledge-graph__label">MEDICATION RELATIONSHIP</span>
                    <h2>Drug Interaction Graph</h2>
                    <p>
                        {disease
                            ? `Relationships between ${drug1}, ${drug2}, and medicines associated with ${disease}.`
                            : `Relationship between ${drug1} and ${drug2}.`}
                    </p>
                </div>
                <div className="knowledge-graph__stats">
                    <div>
                        <strong>{graphData.nodes.length}</strong>
                        <span>Nodes</span>
                    </div>
                    <div>
                        <strong>{graphData.links.length}</strong>
                        <span>Relationships</span>
                    </div>
                </div>
            </div>

            <div className="knowledge-graph__legend">
                <span><i className="legend-dot legend-dot--drug" /> Medicine</span>
                <span><i className="legend-dot legend-dot--disease" /> Disease</span>
                <span><i className="legend-dot legend-dot--sideeffect" /> Side Effect</span>
                <span><i className="legend-line legend-line--interacts" /> Interaction</span>
            </div>

            <div className="knowledge-graph__canvas" ref={containerRef}>
                <ForceGraph2D
                    ref={graphRef}
                    graphData={graphData}
                    nodeId="id"
                    width={containerDimensions.width}
                    height={containerDimensions.height}
                    backgroundColor="#090d16"
                    nodeRelSize={6}
                    onNodeClick={(node) => setSelectedNode(node)}
                    onNodeHover={(node) => setHoverNode(node)}
                    linkDirectionalParticles={(link) => (neighborLinks.has(link) || !hoverNode ? 2 : 0)}
                    linkDirectionalParticleSpeed={0.005}
                    linkDirectionalParticleWidth={3}
                    linkDirectionalParticleColor={(link) => (link.relationship === "INTERACTS_WITH" ? "#ef4444" : "#38bdf8")}
                    linkDirectionalArrowLength={4}
                    linkDirectionalArrowRelPos={1}
                    linkColor={(link) => {
                        const active = hoverNode || selectedNode;
                        if (active && !neighborLinks.has(link)) return "rgba(51, 65, 85, 0.25)";
                        if (link.relationship === "INTERACTS_WITH") return "#ef4444";
                        if (link.relationship === "TREATS") return "#10b981";
                        return "#64748b";
                    }}
                    linkWidth={(link) => {
                        const active = hoverNode || selectedNode;
                        if (active && neighborLinks.has(link)) return 3;
                        return link.relationship === "INTERACTS_WITH" ? 2.5 : 1.5;
                    }}
                    linkLabel={(link) => `${link.relationship}${link.severity ? ` (${link.severity})` : ""}`}
                    nodeCanvasObject={(node, ctx, globalScale) => {
                        const active = hoverNode || selectedNode;
                        const isHighlighted = active ? neighbors.has(node.id) : true;
                        const isSelected = selectedNode?.id === node.id || node.name === drug1 || node.name === drug2;
                        const config = NODE_COLORS[node.type] || NODE_COLORS.default;

                        const baseRadius = node.type === "disease" ? 12 : isSelected ? 10 : 7;

                        ctx.save();
                        ctx.globalAlpha = isHighlighted ? 1.0 : 0.25;

                        if (isSelected || hoverNode?.id === node.id) {
                            ctx.beginPath();
                            ctx.arc(node.x, node.y, baseRadius + 4, 0, 2 * Math.PI);
                            ctx.fillStyle = config.glow;
                            ctx.fill();
                        }

                        ctx.beginPath();
                        ctx.arc(node.x, node.y, baseRadius, 0, 2 * Math.PI);
                        ctx.fillStyle = config.fill;
                        ctx.fill();
                        ctx.lineWidth = isSelected ? 2.5 : 1.5;
                        ctx.strokeStyle = isSelected ? "#ffffff" : config.stroke;
                        ctx.stroke();

                        const label = node.name || node.id;
                        const fontSize = Math.max(9, Math.min(13, 12 / globalScale));
                        ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;

                        const textWidth = ctx.measureText(label).width;
                        const paddingX = 5 / globalScale;
                        const paddingY = 2 / globalScale;
                        const boxX = node.x - textWidth / 2 - paddingX;
                        const boxY = node.y + baseRadius + 3;
                        const boxW = textWidth + paddingX * 2;
                        const boxH = fontSize + paddingY * 2;

                        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                        ctx.beginPath();
                        ctx.roundRect(boxX, boxY, boxW, boxH, 3 / globalScale);
                        ctx.fill();
                        ctx.strokeStyle = config.stroke;
                        ctx.lineWidth = 1 / globalScale;
                        ctx.stroke();

                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillStyle = "#ffffff";
                        ctx.fillText(label, node.x, boxY + boxH / 2);
                        ctx.restore();
                    }}
                />
            </div>
        </div>
    );
}

export default KnowledgeGraph;