import { useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

import { fetchKnowledgeGraph } from "../../services/neo4jService";

import "./KnowledgeGraph.css";

function KnowledgeGraph() {
    const [graphData, setGraphData] = useState({
        nodes: [],
        links: [],
    });

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [relationshipFilter, setRelationshipFilter] =
    useState("ALL");

const [searchText, setSearchText] =
    useState("");

const [filteredGraphData, setFilteredGraphData] =
    useState({
        nodes: [],
        links: [],
    });

const graphRef = useRef(null);

    const loadGraph = async () => {
    try {
        setLoading(true);
        setError("");

        const data = await fetchKnowledgeGraph();

        console.log("Knowledge Graph Data:", data);

        const rawNodes = data.nodes || [];
        const rawLinks = data.links || data.edges || [];

        const nodes = rawNodes
            .map((node) => ({
                ...node,

                id:
                    node.node_id ||
                    node.name ||
                    String(node.id),

                node_id:
                    node.node_id ||
                    node.name ||
                    String(node.id),
            }))
            .filter((node) => node.id);

        const nodeMap = new Map();

        nodes.forEach((node) => {
            const id = String(node.id).trim();

            const name = String(
                node.name || ""
            ).trim();

            const nodeId = String(
                node.node_id || ""
            ).trim();

            if (id) {
                nodeMap.set(id.toLowerCase(), id);
            }

            if (name) {
                nodeMap.set(name.toLowerCase(), id);
            }

            if (nodeId) {
                nodeMap.set(nodeId.toLowerCase(), id);
            }
        });

        const links = rawLinks
            .map((link) => {
                const rawSource =
                    link.source ??
                    link.from;

                const rawTarget =
                    link.target ??
                    link.to;

                if (
                    rawSource === undefined ||
                    rawTarget === undefined
                ) {
                    return null;
                }

                const sourceKey =
                    String(rawSource)
                        .trim()
                        .toLowerCase();

                const targetKey =
                    String(rawTarget)
                        .trim()
                        .toLowerCase();

                const source =
                    nodeMap.get(sourceKey);

                const target =
                    nodeMap.get(targetKey);

                if (!source || !target) {
                    console.warn(
                        "Invalid graph link:",
                        link
                    );

                    return null;
                }

                return {
                    ...link,

                    source,
                    target,

                    relationship:
                        link.relationship ||
                        link.type ||
                        "RELATED",

                    type:
                        link.type ||
                        link.relationship ||
                        "RELATED",
                };
            })
            .filter(Boolean);

        console.log(
            "Graph nodes:",
            nodes.length
        );

        console.log(
            "Graph valid links:",
            links.length
        );

        const newGraphData = {
            nodes,
            links,
        };

        setGraphData(newGraphData);
        setFilteredGraphData(newGraphData);

    } catch (err) {

        console.error(
            "Knowledge graph error:",
            err
        );

        setError(
            "Unable to load the medication knowledge graph."
        );

    } finally {

        setLoading(false);

    }
};
useEffect(() => {
    loadGraph();
}, []);

useEffect(() => {
    let nodes = graphData.nodes;
    let links = graphData.links;

    // Filter relationships
    if (relationshipFilter !== "ALL") {
        links = links.filter((link) => {
            const relationship = String(
                link.relationship || link.type || ""
            ).toUpperCase();

            return relationship === relationshipFilter;
        });

        // Keep only nodes connected to filtered relationships
        const connectedNodeIds = new Set();

        links.forEach((link) => {
            connectedNodeIds.add(
                typeof link.source === "object"
                    ? link.source.id
                    : link.source
            );

            connectedNodeIds.add(
                typeof link.target === "object"
                    ? link.target.id
                    : link.target
            );
        });

        nodes = nodes.filter((node) =>
            connectedNodeIds.has(node.id)
        );
    }

    setFilteredGraphData({
        nodes,
        links,
    });
}, [graphData, relationshipFilter]);

const handleFindNode = () => {
    const query = searchText.trim().toLowerCase();

    if (!query || !graphRef.current) {
        return;
    }

    const node = graphData.nodes.find((item) => {
        const name = String(item.name || "").toLowerCase();
        const nodeId = String(item.node_id || "").toLowerCase();

        return (
            name.includes(query) ||
            nodeId.includes(query)
        );
    });

    if (!node) {
        alert(`Node "${searchText}" not found.`);
        return;
    }

    graphRef.current.centerAt(
        node.x,
        node.y,
        1000
    );

    graphRef.current.zoom(4, 1000);

    console.log("Found node:", node);
};


const handleCleanLayout = () => {
    if (!graphRef.current) {
        return;
    }

    graphRef.current.d3ReheatSimulation();

    setTimeout(() => {
        graphRef.current.zoomToFit(
            1000,
            80
        );
    }, 1000);
};


const handleResetView = () => {
    if (!graphRef.current) {
        return;
    }

    graphRef.current.centerAt(
        0,
        0,
        800
    );

    graphRef.current.zoom(
        1,
        800
    );

    graphRef.current.zoomToFit(
        1000,
        80
    );
};


const handleClusterPatients = () => {
    if (!graphRef.current) {
        return;
    }

    /*
     * Your current Neo4j graph contains
     * Medicine, Disease and Side Effect nodes.
     *
     * There are currently no Patient nodes
     * in graphData.
     *
     * Therefore we cluster the existing
     * node types visually.
     */

    const typePositions = {
        drug: {
            x: -250,
            y: 0,
        },

        disease: {
            x: 0,
            y: 0,
        },

        sideeffect: {
            x: 250,
            y: 0,
        },
    };

    graphData.nodes.forEach((node) => {
        const type = String(
            node.type || ""
        ).toLowerCase();

        const position =
            typePositions[type];

        if (position) {
            node.fx = position.x;
            node.fy = position.y;
        }
    });

    graphRef.current.d3ReheatSimulation();

    setTimeout(() => {
        graphData.nodes.forEach((node) => {
            node.fx = undefined;
            node.fy = undefined;
        });
    }, 2000);
};
    /*
     * --------------------------------------------------
     * Loading
     * --------------------------------------------------
     */

    if (loading) {
        return (
            <div className="knowledge-graph__loading">
                Loading medication knowledge graph...
            </div>
        );
    }


    /*
     * --------------------------------------------------
     * Error
     * --------------------------------------------------
     */

    if (error) {
        return (
            <div className="knowledge-graph__error">
                {error}
            </div>
        );
    }


    /*
     * --------------------------------------------------
     * Empty
     * --------------------------------------------------
     */

    if (!graphData.nodes.length) {
        return (
            <div className="knowledge-graph__empty">
                No knowledge graph data available.
            </div>
        );
    }


    /*
     * --------------------------------------------------
     * Node color
     * --------------------------------------------------
     */

    const getNodeColor = (node) => {

        const type =
            String(node.type || "")
                .toLowerCase();

        if (type === "drug") {
            return "#4f9cff";
        }

        if (type === "disease") {
            return "#22c55e";
        }

        if (
            type === "sideeffect" ||
            type === "side_effect"
        ) {
            return "#f59e0b";
        }

        return "#94a3b8";
    };


    /*
     * --------------------------------------------------
     * Render
     * --------------------------------------------------
     */

    return (
        <div className="knowledge-graph">

            {/* Header */}

            <div className="knowledge-graph__header">

                <div>

                    <span className="knowledge-graph__label">
                        NEO4J KNOWLEDGE GRAPH
                    </span>

                    <h3>
                        Medication Relationship Explorer
                    </h3>

                    <p>
                        Explore relationships between medicines,
                        diseases, side effects, and drug interactions.
                    </p>

                </div>


                {/* Statistics */}

                <div className="knowledge-graph__stats">

                    <div>
                        <strong>
                            {graphData.nodes.length}
                        </strong>

                        <span>
                            Nodes
                        </span>
                    </div>


                    <div>
                        <strong>
                            {graphData.links.length}
                        </strong>

                        <span>
                            Relationships
                        </span>
                    </div>

                </div>

            </div>

{/* Graph Controls */}

<div className="knowledge-graph__controls">

    {/* Relationship Filter */}

    <select
        className="knowledge-graph__relationship-filter"
        value={relationshipFilter}
        onChange={(event) =>
            setRelationshipFilter(event.target.value)
        }
    >
        <option value="ALL">
            All Relationships
        </option>

        <option value="TREATS">
            TREATS
        </option>

        <option value="CAUSES">
            CAUSES
        </option>

        <option value="INTERACTS_WITH">
            INTERACTS_WITH
        </option>

        <option value="RELATED">
            RELATED
        </option>
    </select>


    {/* Search */}

    <input
        type="text"
        className="knowledge-graph__search"
        placeholder="Search node..."
        value={searchText}
        onChange={(event) =>
            setSearchText(event.target.value)
        }
        onKeyDown={(event) => {
            if (event.key === "Enter") {
                handleFindNode();
            }
        }}
    />


    <button
        type="button"
        className="knowledge-graph__control-button"
        onClick={handleFindNode}
    >
        Find
    </button>


    <button
        type="button"
        className="knowledge-graph__control-button"
        onClick={loadGraph}
    >
        Load / Refresh Graph
    </button>

</div>


{/* Layout Controls */}

<div className="knowledge-graph__layout-controls">

    <button
        type="button"
        onClick={handleCleanLayout}
    >
        Clean Layout
    </button>

    <button
        type="button"
        onClick={handleClusterPatients}
    >
        Cluster Patients
    </button>

    <button
        type="button"
        onClick={handleResetView}
    >
        Reset View
    </button>

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
                    <i className="legend-dot legend-dot--sideeffect"></i>
                    Side Effect
                </span>

            </div>


            {/* Graph */}

            <div className="knowledge-graph__canvas">

                <ForceGraph2D
    ref={graphRef}

                    /*
                     * IMPORTANT
                     *
                     * Tell react-force-graph to use our
                     * semantic node ID instead of Neo4j's
                     * internal ID.
                     */

                    nodeId="id"

                    graphData={filteredGraphData}

                    width={1000}
                    height={600}

                    backgroundColor="#0b1220"


                    /*
                     * Node tooltip
                     */

                    nodeLabel={(node) => {

                        return (
                            node.name ||
                            node.node_id ||
                            "Unknown"
                        );

                    }}


                    /*
                     * Node color
                     */

                    nodeColor={getNodeColor}


                    /*
                     * Node size
                     */

                    nodeRelSize={6}


                    /*
                     * Custom node drawing
                     */

                    nodeCanvasObject={(
                        node,
                        ctx,
                        globalScale
                    ) => {

                        const label =
                            node.name ||
                            node.node_id ||
                            "Unknown";


                        /*
                         * Make labels smaller when zoomed out.
                         */

                        const fontSize =
                            Math.max(
                                8,
                                12 / globalScale
                            );


                        ctx.font =
                            `${fontSize}px Inter, Arial, sans-serif`;


                        const nodeColor =
                            getNodeColor(node);


                        /*
                         * Draw node
                         */

                        ctx.beginPath();

                        ctx.arc(
                            node.x,
                            node.y,
                            5,
                            0,
                            2 * Math.PI
                        );

                        ctx.fillStyle =
                            nodeColor;

                        ctx.fill();


                        /*
                         * Draw label
                         */

                        ctx.textAlign =
                            "center";

                        ctx.textBaseline =
                            "top";

                        ctx.fillStyle =
                            "#ffffff";


                        ctx.fillText(
                            label,
                            node.x,
                            node.y + 7
                        );

                    }}


                    /*
                     * --------------------------------------------------
                     * RELATIONSHIP LINES
                     * --------------------------------------------------
                     */

                    linkColor={(link) => {

                        const relationship =
                            String(
                                link.relationship ||
                                link.type ||
                                ""
                            ).toUpperCase();


                        if (
                            relationship ===
                            "INTERACTS_WITH"
                        ) {
                            return "#ef4444";
                        }


                        if (
                            relationship ===
                            "TREATS"
                        ) {
                            return "#22c55e";
                        }


                        if (
                            relationship ===
                            "CAUSES"
                        ) {
                            return "#f59e0b";
                        }


                        return "#64748b";

                    }}


                    /*
                     * Make relationships clearly visible.
                     */

                    linkWidth={(link) => {

                        const relationship =
                            String(
                                link.relationship ||
                                link.type ||
                                ""
                            ).toUpperCase();


                        if (
                            relationship ===
                            "INTERACTS_WITH"
                        ) {
                            return 2.5;
                        }


                        return 1.8;

                    }}


                    /*
                     * Arrows
                     */

                    linkDirectionalArrowLength={5}

                    linkDirectionalArrowRelPos={1}


                    /*
                     * Relationship tooltip
                     */

                    linkLabel={(link) => {

                        const relationship =
                            link.relationship ||
                            link.type ||
                            "RELATED";


                        if (
                            String(
                                relationship
                            ).toUpperCase() ===
                            "INTERACTS_WITH"
                        ) {

                            return (
                                `Interaction: ${
                                    link.severity ||
                                    "Unknown"
                                }`
                            );

                        }


                        return relationship;

                    }}


                    /*
                     * Click a node
                     */

                    onNodeClick={(node) => {

                        console.log(
                            "Selected node:",
                            node
                        );

                    }}


                    /*
                     * Physics
                     */

                    cooldownTicks={200}

                    d3VelocityDecay={0.25}

                    d3AlphaDecay={0.02}

                />

            </div>

        </div>
    );
}

export default KnowledgeGraph;