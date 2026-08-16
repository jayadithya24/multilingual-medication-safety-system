import { useEffect, useMemo, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

import { fetchInteractionGraph } from "../../services/neo4jService";

import "./InteractionGraph.css";


function InteractionGraph({ drug1, drug2 }) {

    const [graphData, setGraphData] = useState({
        nodes: [],
        links: [],
    });

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");


    useEffect(() => {

        if (!drug1 || !drug2) {
            return;
        }

        const loadGraph = async () => {

            try {

                setLoading(true);
                setError("");

                const data = await fetchInteractionGraph(
                    drug1,
                    drug2
                );

                console.log(
                    "Interaction Graph Data:",
                    data
                );

                setGraphData({
                    nodes: data.nodes || [],
                    links: data.links || data.edges || [],
                });

            } catch (err) {

                console.error(
                    "Interaction graph error:",
                    err
                );

                setError(
                    "Unable to load interaction graph."
                );

            } finally {

                setLoading(false);

            }
        };

        loadGraph();

    }, [drug1, drug2]);


    /*
     * --------------------------------------------------
     * CREATE A CLEAN CLINICAL LAYOUT
     * --------------------------------------------------
     *
     * Disease      → center
     * Selected drug → left/right
     * Other drugs   → surrounding ring
     */

    const positionedData = useMemo(() => {
    const allNodes = graphData.nodes || [];
    const allLinks = graphData.links || [];

    if (!allNodes.length) {
        return {
            nodes: [],
            links: [],
        };
    }

    const normalize = (value) => {
        if (!value) return "";

        if (typeof value === "object") {
            return String(
                value.id ||
                value.node_id ||
                value.name ||
                ""
            ).trim();
        }

        return String(value).trim();
    };

    /*
     * --------------------------------------------------
     * 1. FIND THE TWO SELECTED DRUGS
     * --------------------------------------------------
     */

    const selectedDrugNames = new Set([
        drug1?.trim().toLowerCase(),
        drug2?.trim().toLowerCase(),
    ]);

    const selectedDrugs = allNodes.filter(
        node =>
            node.type === "drug" &&
            selectedDrugNames.has(
                String(node.name || node.node_id || "")
                    .trim()
                    .toLowerCase()
            )
    );

    const selectedDrugIds = new Set(
        selectedDrugs.map(
            node =>
                String(
                    node.id ||
                    node.node_id ||
                    node.name
                ).trim()
        )
    );

    /*
     * --------------------------------------------------
     * 2. NORMALIZE LINKS
     * --------------------------------------------------
     */

    const normalizedLinks = allLinks
        .map(link => ({
            ...link,
            source: normalize(link.source),
            target: normalize(link.target),
        }))
        .filter(
            link =>
                link.source &&
                link.target
        );

    /*
     * --------------------------------------------------
     * 3. FIND DISEASES + SIDE EFFECTS CONNECTED
     *    DIRECTLY TO THE TWO SELECTED DRUGS
     * --------------------------------------------------
     */

    const connectedNodeIds = new Set(
        selectedDrugIds
    );

    normalizedLinks.forEach(link => {

        /*
         * Drug → Disease
         * Drug → Side Effect
         */

        if (selectedDrugIds.has(link.source)) {
            connectedNodeIds.add(link.target);
        }

        if (selectedDrugIds.has(link.target)) {
            connectedNodeIds.add(link.source);
        }
    });

    /*
     * --------------------------------------------------
     * 4. KEEP ONLY:
     *
     *    Selected Drug 1
     *    Selected Drug 2
     *    Connected Diseases
     *    Connected Side Effects
     *
     *    NO OTHER DRUGS
     * --------------------------------------------------
     */

    const filteredNodes = allNodes.filter(node => {

        const nodeId = String(
            node.id ||
            node.node_id ||
            node.name ||
            ""
        ).trim();

        /*
         * Always keep the two selected drugs
         */
        if (selectedDrugIds.has(nodeId)) {
            return true;
        }

        /*
         * Keep connected disease nodes
         */
        if (
            node.type === "disease" &&
            connectedNodeIds.has(nodeId)
        ) {
            return true;
        }

        /*
         * Keep connected side effects
         */
        if (
            (
                node.type === "sideeffect" ||
                node.type === "side_effect"
            ) &&
            connectedNodeIds.has(nodeId)
        ) {
            return true;
        }

        /*
         * IMPORTANT:
         * Remove every other medicine.
         */
        return false;
    });

    /*
     * --------------------------------------------------
     * 5. CREATE VALID NODE ID SET
     * --------------------------------------------------
     */

    const validNodeIds = new Set(
        filteredNodes.map(
            node =>
                String(
                    node.id ||
                    node.node_id ||
                    node.name
                ).trim()
        )
    );

    /*
     * --------------------------------------------------
     * 6. KEEP ONLY LINKS BETWEEN THE FILTERED NODES
     * --------------------------------------------------
     */

    const filteredLinks = normalizedLinks.filter(
        link =>
            validNodeIds.has(link.source) &&
            validNodeIds.has(link.target)
    );

    /*
     * --------------------------------------------------
     * 7. CREATE CLEAN NODE OBJECTS
     * --------------------------------------------------
     */

    const nodes = filteredNodes.map(node => ({
        ...node,

        id: String(
            node.id ||
            node.node_id ||
            node.name
        ).trim(),

        label:
            node.name ||
            node.node_id ||
            "Unknown",
    }));

    /*
     * --------------------------------------------------
     * 8. CLINICAL LAYOUT
     * --------------------------------------------------
     */

    const WIDTH = 900;
    const HEIGHT = 500;

    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;

    /*
     * Selected drugs
     */

    const selectedDrugNodes = nodes.filter(
        node =>
            selectedDrugIds.has(node.id)
    );

    if (selectedDrugNodes[0]) {
        selectedDrugNodes[0].fx =
            centerX - 230;

        selectedDrugNodes[0].fy =
            centerY;
    }

    if (selectedDrugNodes[1]) {
        selectedDrugNodes[1].fx =
            centerX + 230;

        selectedDrugNodes[1].fy =
            centerY;
    }

    /*
     * Diseases
     */

    const diseaseNodes = nodes.filter(
        node =>
            node.type === "disease"
    );

    diseaseNodes.forEach((node, index) => {

        const spacing = 180;

        node.fx =
            centerX +
            (index - (diseaseNodes.length - 1) / 2) *
                spacing;

        node.fy =
            centerY - 150;
    });

    /*
     * Side effects
     *
     * Put them below the selected medicines.
     */

    const sideEffectNodes = nodes.filter(
        node =>
            node.type === "sideeffect" ||
            node.type === "side_effect"
    );

    sideEffectNodes.forEach((node, index) => {

        const spacing = 130;

        node.fx =
            centerX +
            (index - (sideEffectNodes.length - 1) / 2) *
                spacing;

        node.fy =
            centerY + 150;
    });

    console.log(
        "Selected drugs:",
        selectedDrugs.map(
            node => node.name
        )
    );

    console.log(
        "Filtered graph nodes:",
        nodes.map(
            node => node.name
        )
    );

    console.log(
        "Filtered graph links:",
        filteredLinks
    );

    return {
        nodes,
        links: filteredLinks,
    };

}, [
    graphData,
    drug1,
    drug2
]);


    if (loading) {

        return (
            <div className="interaction-graph__loading">
                Loading interaction graph...
            </div>
        );

    }


    if (error) {

        return (
            <div className="interaction-graph__error">
                {error}
            </div>
        );

    }


    if (!positionedData.nodes.length) {

        return (
            <div className="interaction-graph__empty">
                No graph data available for these medicines.
            </div>
        );

    }


    return (

        <div className="interaction-graph">

            {/* HEADER */}

            <div className="interaction-graph__header">

                <div>

                    <span className="interaction-graph__label">
                        MEDICATION RELATIONSHIP
                    </span>

                    <h3>
                        Drug Interaction Graph
                    </h3>

                    <p>
                        Relationship between{" "}
                        <strong>{drug1}</strong>
                        {" "}and{" "}
                        <strong>{drug2}</strong>.
                    </p>

                </div>

            </div>


            {/* LEGEND */}

            <div className="interaction-graph__legend">

                <span>
                    <i className="legend-drug"></i>
                    Medicine
                </span>

                <span>
                    <i className="legend-disease"></i>
                    Disease
                </span>

                <span>
                    <i className="legend-treats"></i>
                    TREATS
                </span>

                <span>
                    <i className="legend-interaction"></i>
                    INTERACTS WITH
                </span>

            </div>


            {/* GRAPH */}

            <div className="interaction-graph__canvas">

                <ForceGraph2D

                    graphData={positionedData}

                    width={900}
                    height={500}

                    backgroundColor="#0b1220"


                    /*
                     * IMPORTANT
                     *
                     * We already calculated positions.
                     */

                    staticGraph={true}


                    nodeId="id"


                    nodeLabel={(node) => {

    if (node.type === "disease") {
        return `Disease: ${node.name}`;
    }

    if (
        node.type === "sideeffect" ||
        node.type === "side_effect"
    ) {
        return `Side Effect: ${node.name}`;
    }

    return `Medicine: ${node.name}`;
}}


                    /*
                     * Node colors
                     */

                    nodeColor={(node) => {

    const name =
        node.name?.toLowerCase();

    if (
        name === drug1?.toLowerCase() ||
        name === drug2?.toLowerCase()
    ) {
        return "#2563eb";
    }

    if (node.type === "disease") {
        return "#22c55e";
    }

    if (
        node.type === "sideeffect" ||
        node.type === "side_effect"
    ) {
        return "#f59e0b";
    }

    return "#60a5fa";
}}


                    /*
                     * Node size
                     */

                    nodeRelSize={8}


                    /*
                     * Custom nodes + labels
                     */

                    nodeCanvasObject={(
                        node,
                        ctx,
                        globalScale
                    ) => {

                        const name =
                            node.name ||
                            node.node_id ||
                            "Unknown";


                        const isDisease =
                            node.type === "disease";


                        const isSelected =
                            name.toLowerCase() ===
                                drug1?.toLowerCase() ||
                            name.toLowerCase() ===
                                drug2?.toLowerCase();


                        const radius =
                            isDisease
                                ? 18
                                : isSelected
                                    ? 13
                                    : 9;


                        let color =
                            "#60a5fa";


                        if (isDisease) {
                            color = "#22c55e";
                        }


                        if (isSelected) {
                            color = "#2563eb";
                        }


                        /*
                         * Circle
                         */

                        ctx.beginPath();

                        ctx.arc(
                            node.x,
                            node.y,
                            radius,
                            0,
                            2 * Math.PI
                        );

                        ctx.fillStyle = color;

                        ctx.fill();


                        /*
                         * White border
                         */

                        ctx.strokeStyle =
                            "#ffffff";

                        ctx.lineWidth =
                            isDisease ||
                            isSelected
                                ? 3
                                : 1.5;

                        ctx.stroke();


                        /*
                         * Label
                         */

                        const fontSize =
                            isDisease
                                ? 15
                                : isSelected
                                    ? 14
                                    : 12;


                        ctx.font =
                            `600 ${fontSize}px Inter, Arial, sans-serif`;


                        ctx.textAlign =
                            "center";

                        ctx.textBaseline =
                            "top";


                        ctx.fillStyle =
                            "#ffffff";


                        ctx.fillText(
                            name,
                            node.x,
                            node.y + radius + 7
                        );

                    }}


                    /*
                     * Relationship colors
                     */

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

                            return "#22c55e";

                        }


                        return "#64748b";

                    }}


                    /*
                     * Relationship thickness
                     */

                    linkWidth={(link) => {

                        if (
                            link.relationship ===
                            "INTERACTS_WITH"
                        ) {

                            return 4;

                        }


                        if (
                            link.relationship ===
                            "TREATS"
                        ) {

                            return 2.5;

                        }


                        return 1.5;

                    }}


                    /*
                     * Arrows
                     */

                    linkDirectionalArrowLength={7}

                    linkDirectionalArrowRelPos={1}


                    /*
                     * Relationship label on hover
                     */

                    linkLabel={(link) => {

                        if (
                            link.relationship ===
                            "INTERACTS_WITH"
                        ) {

                            return `INTERACTS WITH — ${
                                link.severity ||
                                "Unknown severity"
                            }`;

                        }


                        if (
                            link.relationship ===
                            "TREATS"
                        ) {

                            return "TREATS";

                        }


                        return (
                            link.relationship ||
                            ""
                        );

                    }}

                />

            </div>

        </div>

    );

}


export default InteractionGraph;