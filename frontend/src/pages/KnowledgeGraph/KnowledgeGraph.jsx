import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { fetchKnowledgeGraph } from "../../services/neo4jService";
import "./KnowledgeGraph.css";

const NODE_COLORS = {
    drug: { fill: "#38bdf8", stroke: "#0284c7", glow: "rgba(56, 189, 248, 0.4)", label: "Medicine" },
    disease: { fill: "#34d399", stroke: "#059669", glow: "rgba(52, 211, 153, 0.4)", label: "Disease" },
    sideeffect: { fill: "#fbbf24", stroke: "#d97706", glow: "rgba(251, 191, 36, 0.4)", label: "Side Effect" },
    side_effect: { fill: "#fbbf24", stroke: "#d97706", glow: "rgba(251, 191, 36, 0.4)", label: "Side Effect" },
    patient: { fill: "#c084fc", stroke: "#9333ea", glow: "rgba(192, 132, 252, 0.4)", label: "Patient" },
    default: { fill: "#94a3b8", stroke: "#475569", glow: "rgba(148, 163, 184, 0.3)", label: "Entity" },
};

export default function KnowledgeGraph() {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [relationshipFilter, setRelationshipFilter] = useState("ALL");
    const [searchText, setSearchText] = useState("");
    const [selectedNode, setSelectedNode] = useState(null);
    const [hoverNode, setHoverNode] = useState(null);
    const [enableParticles, setEnableParticles] = useState(true);
    const [containerDimensions, setContainerDimensions] = useState({ width: 1000, height: 620 });

    const graphRef = useRef(null);
    const containerRef = useRef(null);

    // Dynamic resize observer for responsive canvas
    useEffect(() => {
        if (!containerRef.current) return;
        const updateDimensions = () => {
            if (containerRef.current) {
                setContainerDimensions({
                    width: containerRef.current.clientWidth || 1000,
                    height: Math.max(550, Math.min(750, window.innerHeight - 280)),
                });
            }
        };
        updateDimensions();
        const observer = new ResizeObserver(updateDimensions);
        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    const loadGraph = () => {
        setLoading(true);
        setError("");
        fetchKnowledgeGraph()
            .then((data) => {
                const rawNodes = data.nodes || [];
                const rawLinks = data.links || data.edges || [];

                const nodes = rawNodes
                    .map((node) => ({
                        ...node,
                        id: String(node.node_id || node.name || node.id || "").trim(),
                        name: String(node.name || node.node_id || node.id || "").trim(),
                        type: String(node.type || "drug").toLowerCase(),
                    }))
                    .filter((node) => node.id);

                const nodeMap = new Map();
                nodes.forEach((node) => {
                    if (node.id) nodeMap.set(node.id.toLowerCase(), node.id);
                    if (node.name) nodeMap.set(node.name.toLowerCase(), node.id);
                });

                // Calculate node degree (connections count)
                const degrees = new Map();
                const links = rawLinks
                    .map((link) => {
                        const sKey = String(link.source ?? link.from ?? "").trim().toLowerCase();
                        const tKey = String(link.target ?? link.to ?? "").trim().toLowerCase();
                        const source = nodeMap.get(sKey);
                        const target = nodeMap.get(tKey);
                        if (!source || !target) return null;

                        degrees.set(source, (degrees.get(source) || 0) + 1);
                        degrees.set(target, (degrees.get(target) || 0) + 1);

                        return {
                            ...link,
                            source,
                            target,
                            relationship: String(link.relationship || link.type || "RELATED").toUpperCase(),
                        };
                    })
                    .filter(Boolean);

                nodes.forEach((node) => {
                    node.degree = degrees.get(node.id) || 1;
                });

                setGraphData({ nodes, links });
            })
            .catch((err) => {
                console.error("Knowledge graph error:", err);
                setError("Unable to load the medication knowledge graph.");
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        loadGraph();
    }, []);

    // Filtered data & neighbor sets
    const { filteredGraphData, neighbors, neighborLinks } = useMemo(() => {
        let nodes = graphData.nodes;
        let links = graphData.links;

        if (relationshipFilter !== "ALL") {
            links = links.filter((link) => {
                const rel = String(link.relationship || "").toUpperCase();
                return rel === relationshipFilter;
            });
            const connectedIds = new Set();
            links.forEach((l) => {
                connectedIds.add(typeof l.source === "object" ? l.source.id : l.source);
                connectedIds.add(typeof l.target === "object" ? l.target.id : l.target);
            });
            nodes = nodes.filter((n) => connectedIds.has(n.id));
        }

        const activeNode = hoverNode || selectedNode;
        const nSet = new Set();
        const lSet = new Set();

        if (activeNode) {
            nSet.add(activeNode.id);
            links.forEach((l) => {
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

        return {
            filteredGraphData: { nodes, links },
            neighbors: nSet,
            neighborLinks: lSet,
        };
    }, [graphData, relationshipFilter, hoverNode, selectedNode]);

    const handleFindNode = () => {
        const query = searchText.trim().toLowerCase();
        if (!query || !graphRef.current) return;

        const matched = graphData.nodes.find(
            (n) => n.name.toLowerCase().includes(query) || n.id.toLowerCase().includes(query)
        );

        if (!matched) {
            alert(`Node "${searchText}" not found.`);
            return;
        }

        setSelectedNode(matched);
        graphRef.current.centerAt(matched.x, matched.y, 800);
        graphRef.current.zoom(3.5, 800);
    };

    const handleZoomIn = () => graphRef.current?.zoom((graphRef.current.zoom() || 1) * 1.4, 400);
    const handleZoomOut = () => graphRef.current?.zoom((graphRef.current.zoom() || 1) / 1.4, 400);
    const handleResetView = () => {
        if (!graphRef.current) return;
        graphRef.current.centerAt(0, 0, 600);
        graphRef.current.zoomToFit(800, 60);
    };

    const handleCleanLayout = () => {
        if (!graphRef.current) return;
        graphRef.current.d3ReheatSimulation();
        setTimeout(() => graphRef.current?.zoomToFit(800, 60), 800);
    };

    // Connected details for inspector side panel
    const selectedConnections = useMemo(() => {
        if (!selectedNode) return [];
        return graphData.links
            .filter((l) => {
                const sId = typeof l.source === "object" ? l.source.id : l.source;
                const tId = typeof l.target === "object" ? l.target.id : l.target;
                return sId === selectedNode.id || tId === selectedNode.id;
            })
            .map((l) => {
                const sId = typeof l.source === "object" ? l.source.id : l.source;
                const tId = typeof l.target === "object" ? l.target.id : l.target;
                const otherId = sId === selectedNode.id ? tId : sId;
                const otherNode = graphData.nodes.find((n) => n.id === otherId);
                return {
                    relationship: l.relationship,
                    targetNode: otherNode || { name: otherId, type: "default" },
                    direction: sId === selectedNode.id ? "→" : "←",
                };
            });
    }, [selectedNode, graphData]);

    if (loading) {
        return (
            <div className="knowledge-graph__loading">
                <div className="graph-spinner" />
                <span>Loading Neo4j Knowledge Graph...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="knowledge-graph__error">
                <span>⚠️ {error}</span>
                <button type="button" onClick={loadGraph} className="knowledge-graph__retry-btn">
                    Retry Connection
                </button>
            </div>
        );
    }

    return (
        <div className="knowledge-graph">
            {/* Header */}
            <div className="knowledge-graph__header">
                <div>
                    <span className="knowledge-graph__label">NEO4J KNOWLEDGE GRAPH</span>
                    <h3>Medication Relationship Explorer</h3>
                    <p>Interactive graph visualization of medicines, diseases, side effects, and clinical drug interactions.</p>
                </div>
                <div className="knowledge-graph__stats">
                    <div>
                        <strong>{filteredGraphData.nodes.length}</strong>
                        <span>Nodes</span>
                    </div>
                    <div>
                        <strong>{filteredGraphData.links.length}</strong>
                        <span>Relationships</span>
                    </div>
                </div>
            </div>

            {/* Toolbar */}
            <div className="knowledge-graph__controls">
                <select
                    className="knowledge-graph__relationship-filter"
                    value={relationshipFilter}
                    onChange={(e) => setRelationshipFilter(e.target.value)}
                >
                    <option value="ALL">All Relationships</option>
                    <option value="INTERACTS_WITH">INTERACTS_WITH (Interactions)</option>
                    <option value="TREATS">TREATS (Indications)</option>
                    <option value="CAUSES">CAUSES (Side Effects)</option>
                    <option value="RELATED">RELATED</option>
                </select>

                <div className="knowledge-graph__search-group">
                    <input
                        type="text"
                        className="knowledge-graph__search"
                        placeholder="Search medicine or disease..."
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleFindNode()}
                    />
                    <button type="button" className="knowledge-graph__control-button" onClick={handleFindNode}>
                        Find
                    </button>
                </div>

                <div className="knowledge-graph__action-btns">
                    <button type="button" onClick={handleZoomIn} title="Zoom In">+</button>
                    <button type="button" onClick={handleZoomOut} title="Zoom Out">−</button>
                    <button type="button" onClick={handleResetView} title="Fit to View">Fit View</button>
                    <button type="button" onClick={handleCleanLayout} title="Re-arrange nodes">Re-layout</button>
                    <button
                        type="button"
                        className={enableParticles ? "is-active" : ""}
                        onClick={() => setEnableParticles(!enableParticles)}
                        title="Toggle animated flow particles"
                    >
                        {enableParticles ? "✨ Flow On" : "✨ Flow Off"}
                    </button>
                </div>
            </div>

            {/* Legend */}
            <div className="knowledge-graph__legend">
                <span><i className="legend-dot legend-dot--drug" /> Medicine (Drug)</span>
                <span><i className="legend-dot legend-dot--disease" /> Disease</span>
                <span><i className="legend-dot legend-dot--sideeffect" /> Side Effect</span>
                <span><i className="legend-line legend-line--interacts" /> Interaction</span>
                <span><i className="legend-line legend-line--treats" /> Treats</span>
            </div>

            {/* Canvas Container */}
            <div className="knowledge-graph__canvas-wrapper" ref={containerRef}>
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
                    linkDirectionalParticles={enableParticles ? (link) => (neighborLinks.has(link) || !hoverNode ? 2 : 0) : 0}
                    linkDirectionalParticleSpeed={0.005}
                    linkDirectionalParticleWidth={3}
                    linkDirectionalParticleColor={(link) => (link.relationship === "INTERACTS_WITH" ? "#ef4444" : "#38bdf8")}
                    linkDirectionalArrowLength={4.5}
                    linkDirectionalArrowRelPos={1}
                    linkColor={(link) => {
                        const active = hoverNode || selectedNode;
                        if (active && !neighborLinks.has(link)) return "rgba(51, 65, 85, 0.25)";
                        const rel = link.relationship;
                        if (rel === "INTERACTS_WITH") return "#ef4444";
                        if (rel === "TREATS") return "#10b981";
                        if (rel === "CAUSES") return "#f59e0b";
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
                        const isSelected = selectedNode?.id === node.id;
                        const config = NODE_COLORS[node.type] || NODE_COLORS.default;

                        const baseRadius = Math.max(7, Math.min(14, (node.degree || 1) * 2.2));
                        const radius = isSelected ? baseRadius + 3 : baseRadius;

                        ctx.save();
                        ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;

                        // Outer Glow Ring for selected/hovered nodes
                        if (isSelected || hoverNode?.id === node.id) {
                            ctx.beginPath();
                            ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI);
                            ctx.fillStyle = config.glow;
                            ctx.fill();
                        }

                        // Node Circle
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
                        ctx.fillStyle = config.fill;
                        ctx.fill();
                        ctx.lineWidth = isSelected ? 3 : 1.5;
                        ctx.strokeStyle = isSelected ? "#ffffff" : config.stroke;
                        ctx.stroke();

                        // Node Label Box & Text
                        const label = node.name || node.id;
                        const fontSize = Math.max(9, Math.min(14, 12 / globalScale));
                        ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;

                        const textWidth = ctx.measureText(label).width;
                        const paddingX = 6 / globalScale;
                        const paddingY = 3 / globalScale;
                        const boxX = node.x - textWidth / 2 - paddingX;
                        const boxY = node.y + radius + 3;
                        const boxW = textWidth + paddingX * 2;
                        const boxH = fontSize + paddingY * 2;

                        // Label Background Pill Box
                        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                        ctx.beginPath();
                        ctx.roundRect(boxX, boxY, boxW, boxH, 4 / globalScale);
                        ctx.fill();
                        ctx.strokeStyle = config.stroke;
                        ctx.lineWidth = 1 / globalScale;
                        ctx.stroke();

                        // Text
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillStyle = "#ffffff";
                        ctx.fillText(label, node.x, boxY + boxH / 2);
                        ctx.restore();
                    }}
                />

                {/* Node Inspector Side Panel */}
                {selectedNode && (
                    <aside className="knowledge-graph__inspector" aria-label="Node Inspector">
                        <div className="inspector__header">
                            <span className="inspector__type-badge" style={{ backgroundColor: (NODE_COLORS[selectedNode.type] || NODE_COLORS.default).fill }}>
                                {(NODE_COLORS[selectedNode.type] || NODE_COLORS.default).label}
                            </span>
                            <button type="button" className="inspector__close-btn" onClick={() => setSelectedNode(null)}>✕</button>
                        </div>
                        <h4 className="inspector__title">{selectedNode.name}</h4>
                        <p className="inspector__id">ID: <code>{selectedNode.id}</code></p>

                        <div className="inspector__meta">
                            <span>Connections: <strong>{selectedNode.degree || selectedConnections.length}</strong></span>
                        </div>

                        <div className="inspector__connections">
                            <h5>Direct Relationships ({selectedConnections.length})</h5>
                            {selectedConnections.length === 0 ? (
                                <p className="inspector__empty">No direct connections found.</p>
                            ) : (
                                <ul className="inspector__list">
                                    {selectedConnections.map((c, i) => (
                                        <li key={i} className="inspector__item">
                                            <span className={`rel-tag rel-tag--${c.relationship.toLowerCase()}`}>
                                                {c.direction} {c.relationship}
                                            </span>
                                            <button
                                                type="button"
                                                className="inspector__target-link"
                                                onClick={() => {
                                                    const target = graphData.nodes.find((n) => n.id === c.targetNode.id);
                                                    if (target && graphRef.current) {
                                                        setSelectedNode(target);
                                                        graphRef.current.centerAt(target.x, target.y, 600);
                                                        graphRef.current.zoom(3.5, 600);
                                                    }
                                                }}
                                            >
                                                {c.targetNode.name}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </aside>
                )}
            </div>
        </div>
    );
}
