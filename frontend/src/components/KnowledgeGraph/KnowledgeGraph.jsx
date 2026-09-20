import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import api from "../../services/api";
import "./KnowledgeGraph.css";

const NODE_CONFIGS = {
    drug: { fill: "#38bdf8", stroke: "#0284c7", glow: "rgba(56, 189, 248, 0.4)", label: "Medicine", icon: "💊" },
    disease: { fill: "#34d399", stroke: "#059669", glow: "rgba(52, 211, 153, 0.4)", label: "Disease", icon: "🏥" },
    sideeffect: { fill: "#fbbf24", stroke: "#d97706", glow: "rgba(251, 191, 36, 0.4)", label: "Side Effect", icon: "⚠️" },
    side_effect: { fill: "#fbbf24", stroke: "#d97706", glow: "rgba(251, 191, 36, 0.4)", label: "Side Effect", icon: "⚠️" },
    patient: { fill: "#c084fc", stroke: "#9333ea", glow: "rgba(192, 132, 252, 0.4)", label: "Patient", icon: "👤" },
    default: { fill: "#94a3b8", stroke: "#475569", glow: "rgba(148, 163, 184, 0.3)", label: "Entity", icon: "🌐" },
};

function KnowledgeGraph({ drug1 = "", drug2 = "" }) {
    const [rawGraphData, setRawGraphData] = useState({ nodes: [], links: [] });
    const [disease, setDisease] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedNode, setSelectedNode] = useState(null);
    const [hoverNode, setHoverNode] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [activeFilter, setActiveFilter] = useState("all");
    const [containerDimensions, setContainerDimensions] = useState({ width: 900, height: 520 });

    const graphRef = useRef(null);
    const containerRef = useRef(null);

    // Responsive container dimensions
    useEffect(() => {
        if (!containerRef.current) return;
        const updateDimensions = () => {
            if (containerRef.current) {
                setContainerDimensions({
                    width: containerRef.current.clientWidth || 900,
                    height: 520,
                });
            }
        };
        updateDimensions();
        const observer = new ResizeObserver(updateDimensions);
        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    // Load graph data: either focused interaction graph or full knowledge graph
    useEffect(() => {
        let isMounted = true;
        const loadGraph = async () => {
            try {
                setLoading(true);
                setError("");

                let response;
                if (drug1 && drug2) {
                    response = await api.get("/neo4j/interaction-graph", {
                        params: { drug1, drug2 },
                    });
                } else {
                    response = await api.get("/neo4j/graph");
                }

                if (!isMounted) return;

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

                setRawGraphData({ nodes, links });
                setDisease(response.data.disease || "");
            } catch (err) {
                console.error("Knowledge graph error:", err);
                setError("Unable to load knowledge graph.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        loadGraph();
        return () => {
            isMounted = false;
        };
    }, [drug1, drug2]);

    // Filter nodes & links based on user search term & category filter
    const filteredGraphData = useMemo(() => {
        let nodes = rawGraphData.nodes;

        if (activeFilter !== "all") {
            nodes = nodes.filter((n) => {
                if (activeFilter === "drug") return n.type === "drug";
                if (activeFilter === "disease") return n.type === "disease";
                if (activeFilter === "sideeffect") return n.type.includes("side");
                if (activeFilter === "patient") return n.type === "patient";
                return true;
            });
        }

        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase();
            nodes = nodes.filter(
                (n) =>
                    n.name.toLowerCase().includes(term) ||
                    (n.generic_name && n.generic_name.toLowerCase().includes(term)) ||
                    (n.drug_class && n.drug_class.toLowerCase().includes(term))
            );
        }

        const validIds = new Set(nodes.map((n) => n.id));
        const links = rawGraphData.links.filter(
            (l) =>
                validIds.has(typeof l.source === "object" ? l.source.id : l.source) &&
                validIds.has(typeof l.target === "object" ? l.target.id : l.target)
        );

        return { nodes, links };
    }, [rawGraphData, activeFilter, searchTerm]);

    // Calculate highlighted neighbors and links on node hover or select
    const { neighbors, neighborLinks } = useMemo(() => {
        const activeNode = hoverNode || selectedNode;
        const nSet = new Set();
        const lSet = new Set();

        if (activeNode) {
            nSet.add(activeNode.id);
            filteredGraphData.links.forEach((l) => {
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
    }, [filteredGraphData, hoverNode, selectedNode]);

    // Graph Controls
    const handleZoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.3, 400);
    const handleZoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.3, 400);
    const handleResetZoom = () => graphRef.current?.zoomToFit(400, 40);

    if (loading) {
        return (
            <div className="knowledge-graph__loading">
                <div className="graph-spinner" />
                <span>Loading NeoGraphMed Knowledge Graph...</span>
            </div>
        );
    }

    if (error) {
        return <div className="knowledge-graph__error">{error}</div>;
    }

    return (
        <div className="knowledge-graph">
            {/* Header & Controls */}
            <div className="knowledge-graph__header">
                <div>
                    <span className="knowledge-graph__label">CLINICAL KNOWLEDGE GRAPH</span>
                    <h2>NeoGraphMed Interactive Graph</h2>
                    <p>Explore relationships between medicines, diseases, side effects, and patient profiles.</p>
                </div>
                <div className="knowledge-graph__stats">
                    <div>
                        <strong>{filteredGraphData.nodes.length}</strong>
                        <span>Nodes</span>
                    </div>
                    <div>
                        <strong>{filteredGraphData.links.length}</strong>
                        <span>Links</span>
                    </div>
                </div>
            </div>

            {/* Filter Toolbar & Search */}
            <div className="knowledge-graph__toolbar">
                <div className="knowledge-graph__search">
                    <span>⌕</span>
                    <input
                        type="text"
                        placeholder="Search nodes in graph..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    {searchTerm && <button onClick={() => setSearchTerm("")}>×</button>}
                </div>

                <div className="knowledge-graph__filters">
                    <button className={activeFilter === "all" ? "is-active" : ""} onClick={() => setActiveFilter("all")}>All</button>
                    <button className={activeFilter === "drug" ? "is-active" : ""} onClick={() => setActiveFilter("drug")}>💊 Medicines</button>
                    <button className={activeFilter === "disease" ? "is-active" : ""} onClick={() => setActiveFilter("disease")}>🏥 Diseases</button>
                    <button className={activeFilter === "sideeffect" ? "is-active" : ""} onClick={() => setActiveFilter("sideeffect")}>⚠️ Side Effects</button>
                    <button className={activeFilter === "patient" ? "is-active" : ""} onClick={() => setActiveFilter("patient")}>👤 Patients</button>
                </div>

                <div className="knowledge-graph__controls">
                    <button title="Zoom In" onClick={handleZoomIn}>+</button>
                    <button title="Zoom Out" onClick={handleZoomOut}>−</button>
                    <button title="Fit to View" onClick={handleResetZoom}>⛶</button>
                </div>
            </div>

            {/* Canvas Container */}
            <div className="knowledge-graph__canvas" ref={containerRef}>
                {filteredGraphData.nodes.length === 0 ? (
                    <div className="knowledge-graph__empty">No matching nodes found for your filter.</div>
                ) : (
                    <ForceGraph2D
                        ref={graphRef}
                        graphData={filteredGraphData}
                        nodeId="id"
                        width={containerDimensions.width}
                        height={containerDimensions.height}
                        backgroundColor="#090d16"
                        nodeRelSize={6}
                        onNodeClick={(node) => setSelectedNode(node)}
                        onNodeHover={(node) => setHoverNode(node)}
                        onBackgroundClick={() => setSelectedNode(null)}
                        linkDirectionalParticles={(link) => (neighborLinks.has(link) || !hoverNode ? 2 : 0)}
                        linkDirectionalParticleSpeed={0.005}
                        linkDirectionalParticleWidth={3}
                        linkDirectionalParticleColor={(link) => (link.relationship === "INTERACTS_WITH" ? "#ef4444" : "#38bdf8")}
                        linkDirectionalArrowLength={4}
                        linkDirectionalArrowRelPos={1}
                        linkColor={(link) => {
                            const active = hoverNode || selectedNode;
                            if (active && !neighborLinks.has(link)) return "rgba(51, 65, 85, 0.2)";
                            if (link.relationship === "INTERACTS_WITH") return "#ef4444";
                            if (link.relationship === "TREATS") return "#10b981";
                            if (link.relationship === "CAUSES") return "#f59e0b";
                            return "#64748b";
                        }}
                        linkWidth={(link) => {
                            const active = hoverNode || selectedNode;
                            if (active && neighborLinks.has(link)) return 3.5;
                            return link.relationship === "INTERACTS_WITH" ? 2.5 : 1.5;
                        }}
                        linkLabel={(link) => `${link.relationship}${link.severity ? ` (${link.severity})` : ""}`}
                        nodeCanvasObject={(node, ctx, globalScale) => {
                            const active = hoverNode || selectedNode;
                            const isHighlighted = active ? neighbors.has(node.id) : true;
                            const isSelected = selectedNode?.id === node.id;
                            const config = NODE_CONFIGS[node.type] || NODE_CONFIGS.default;

                            const baseRadius = node.type === "disease" ? 13 : isSelected ? 11 : 8;

                            ctx.save();
                            ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;

                            // Glowing halo
                            if (isSelected || hoverNode?.id === node.id) {
                                ctx.beginPath();
                                ctx.arc(node.x, node.y, baseRadius + 5, 0, 2 * Math.PI);
                                ctx.fillStyle = config.glow;
                                ctx.fill();
                            }

                            // Core node
                            ctx.beginPath();
                            ctx.arc(node.x, node.y, baseRadius, 0, 2 * Math.PI);
                            ctx.fillStyle = config.fill;
                            ctx.fill();
                            ctx.lineWidth = isSelected ? 3 : 1.5;
                            ctx.strokeStyle = isSelected ? "#ffffff" : config.stroke;
                            ctx.stroke();

                            // Node label pill
                            const label = `${config.icon} ${node.name || node.id}`;
                            const fontSize = Math.max(9, Math.min(13, 12 / globalScale));
                            ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;

                            const textWidth = ctx.measureText(label).width;
                            const paddingX = 6 / globalScale;
                            const paddingY = 2 / globalScale;
                            const boxX = node.x - textWidth / 2 - paddingX;
                            const boxY = node.y + baseRadius + 4;
                            const boxW = textWidth + paddingX * 2;
                            const boxH = fontSize + paddingY * 2;

                            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                            ctx.beginPath();
                            ctx.roundRect(boxX, boxY, boxW, boxH, 4 / globalScale);
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
                )}
            </div>

            {/* Node Inspector Drawer */}
            {selectedNode && (
                <div className="knowledge-graph__inspector">
                    <div className="knowledge-graph__inspector-header">
                        <div>
                            <span className="knowledge-graph__inspector-type">
                                {(NODE_CONFIGS[selectedNode.type] || NODE_CONFIGS.default).icon} {(NODE_CONFIGS[selectedNode.type] || NODE_CONFIGS.default).label}
                            </span>
                            <h3>{selectedNode.name}</h3>
                        </div>
                        <button onClick={() => setSelectedNode(null)}>×</button>
                    </div>

                    <div className="knowledge-graph__inspector-body">
                        {selectedNode.generic_name && (
                            <div>
                                <strong>Generic Name:</strong> {selectedNode.generic_name}
                            </div>
                        )}
                        {selectedNode.drug_class && (
                            <div>
                                <strong>Drug Class:</strong> {selectedNode.drug_class}
                            </div>
                        )}
                        <div>
                            <strong>Connected Relationships:</strong>
                            <ul>
                                {filteredGraphData.links
                                    .filter(
                                        (l) =>
                                            (typeof l.source === "object" ? l.source.id : l.source) === selectedNode.id ||
                                            (typeof l.target === "object" ? l.target.id : l.target) === selectedNode.id
                                    )
                                    .map((l, idx) => {
                                        const otherId = (typeof l.source === "object" ? l.source.id : l.source) === selectedNode.id
                                            ? (typeof l.target === "object" ? l.target.id : l.target)
                                            : (typeof l.source === "object" ? l.source.id : l.source);
                                        return (
                                            <li key={idx}>
                                                <span style={{ color: l.relationship === "INTERACTS_WITH" ? "#ef4444" : "#3b82f6" }}>
                                                    {l.relationship}
                                                </span>{" "}
                                                ➔ <strong>{otherId}</strong>
                                                {l.description && <p className="inspector-desc">{l.description}</p>}
                                            </li>
                                        );
                                    })}
                            </ul>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default KnowledgeGraph;