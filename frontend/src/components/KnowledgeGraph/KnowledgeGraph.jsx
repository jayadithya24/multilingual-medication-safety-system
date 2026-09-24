import { useEffect, useId, useMemo, useState } from "react";
import api from "../../services/api";
import "./KnowledgeGraph.css";

const kind = n => n.type?.includes("side") ? "sideeffect" : n.type || "drug";
const labels = { drug: "Medicine", disease: "Condition", sideeffect: "Side effect" };
const relation = l => (l.relationship || l.type || "related").replaceAll("_", " ").toLowerCase();
const endpoint = v => String(typeof v === "object" ? v.id : v);

export default function KnowledgeGraph({ drug1 = "", drug2 = "" }) {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [focus, setFocus] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [retry, setRetry] = useState(0);
  const marker = useId().replaceAll(":", "");
  useEffect(() => {
    let active = true;
    const url = drug2 ? "/neo4j/interaction-graph" : drug1 ? "/neo4j/drug-graph" : "/neo4j/graph";
    api.get(url, { params: drug2 ? { drug1, drug2 } : drug1 ? { drug: drug1 } : {} }).then(({ data: response }) => {
      if (!active) return;
      const aliases = new Map();
      const nodes = (response.nodes || []).map(n => {
        const id = String(n.node_id || n.id || n.name);
        [n.id, n.node_id, n.name].filter(Boolean).forEach(v => aliases.set(String(v), id));
        return { ...n, id, name: n.name || id };
      });
      const links = (response.links || response.edges || []).map(l => ({ ...l,
        source: aliases.get(endpoint(l.source)), target: aliases.get(endpoint(l.target)),
      })).filter(l => l.source && l.target);
      setData({ nodes, links, source: response.source }); setError(""); setLoading(false);
    }).catch(() => { if (active) { setError("Medicine relationships could not be loaded. Please retry."); setLoading(false); } });
    return () => { active = false; };
  }, [drug1, drug2, retry]);
  const medicines = useMemo(() => data.nodes.filter(n => kind(n) === "drug").sort((a, b) => a.name.localeCompare(b.name)), [data]);
  const focused = drug1 || focus || medicines[0]?.name || "";
  const centers = data.nodes.filter(n => kind(n) === "drug" && [focused.toLowerCase(), drug2.toLowerCase()].includes(n.name.toLowerCase()));
  const centerIds = new Set(centers.map(n => n.id));
  const relatedLinks = data.links.filter(l => centerIds.has(l.source) || centerIds.has(l.target));
  const connected = new Set(relatedLinks.flatMap(l => [l.source, l.target]));
  const neighbors = data.nodes.filter(n => connected.has(n.id) && !centerIds.has(n.id) && (filter === "all" || kind(n) === filter))
    .sort((a, b) => kind(a).localeCompare(kind(b)) || a.name.localeCompare(b.name));
  const visible = neighbors.slice(page * 10, page * 10 + 10);
  const height = Math.max(380, Math.ceil(visible.length / 2) * 94 + 90);
  const positions = new Map();
  centers.forEach((n, i) => positions.set(n.id, { x: 500, y: height / 2 + (i - (centers.length - 1) / 2) * 160 }));
  visible.forEach((n, i) => {
    const side = i % 2, count = Math.ceil((visible.length - side) / 2);
    positions.set(n.id, { x: side ? 865 : 135, y: height / 2 + (Math.floor(i / 2) - (count - 1) / 2) * 94 });
  });
  const links = relatedLinks.filter(l => positions.has(l.source) && positions.has(l.target));
  const isSelectedLink = link => selected && (link.source === selected.id || link.target === selected.id);
  const highlightedIds = new Set(selected ? [selected.id] : []);
  links.filter(isSelectedLink).forEach(link => {
    highlightedIds.add(link.source);
    highlightedIds.add(link.target);
  });
  // Draw highlighted paths last so they remain visible at crossings.
  const orderedLinks = [...links].sort((a, b) => Number(Boolean(isSelectedLink(a))) - Number(Boolean(isSelectedLink(b))));
  const selectNode = node => setSelected(current => current?.id === node.id ? null : node);
  const reset = () => { setPage(0); setSelected(null); setZoom(1); };
  return <section className="med-graph" aria-label="Medication knowledge graph">
    <header className="med-graph__header"><div><p className="med-graph__eyebrow">CONNECTED MEDICINE</p>
      <h2>{drug2 ? "Interaction knowledge graph" : "Medication knowledge graph"}</h2>
      <p>{drug2 ? `${drug1} and ${drug2}.` : "One medicine. Its direct connections."} Select a node to explore its relationships.</p></div>
      <span className="med-graph__count">{relatedLinks.length} relationships</span></header>
    {!loading && !error && <p className="med-graph__source">Source: {data.source === "neo4j" ? "Neo4j database" : data.source === "local_csv" ? "Local dataset (Neo4j unavailable)" : "Not reported"}</p>}
    <div className="med-graph__toolbar">
      {!drug1 && <label>Medicine<select aria-label="Graph medicine" value={focused} onChange={e => { setFocus(e.target.value); reset(); }}>{medicines.map(n => <option key={n.id}>{n.name}</option>)}</select></label>}
      <label>Show connections<select value={filter} onChange={e => { setFilter(e.target.value); reset(); }}><option value="all">All relationships</option><option value="disease">Conditions</option><option value="sideeffect">Side effects</option><option value="drug">Medicines</option></select></label>
      <div className="med-graph__controls"><button aria-label="Zoom out" disabled={zoom <= 1} onClick={() => setZoom(Math.max(1, zoom - .25))}>−</button><button onClick={() => setZoom(1)}>Fit view</button><button aria-label="Zoom in" disabled={zoom >= 2} onClick={() => setZoom(Math.min(2, zoom + .25))}>+</button></div>
    </div>
    <div className="med-graph__legend">{Object.entries(labels).map(([type, label]) => <span key={type}><i className={`med-graph__dot med-graph__dot--${type}`} />{label}</span>)}<span>Arrows show relationship direction</span></div>
    {loading ? <p className="med-graph__message" role="status">Loading medicine relationships…</p> : error ? <div className="med-graph__message" role="alert">{error} <button onClick={() => { setLoading(true); setRetry(retry + 1); }}>Retry</button></div> : !centers.length ? <p className="med-graph__message">No graph data is available for this medicine.</p> : <>
      <div className="med-graph__viewport"><svg className="med-graph__svg" onClick={e => { if (e.target === e.currentTarget) setSelected(null); }} onKeyDown={e => { if (e.key === "Escape") setSelected(null); }} role="group" aria-label={`Relationships for ${focused}${drug2 ? ` and ${drug2}` : ""}`} viewBox={`0 0 1000 ${height}`} style={{ width: `${zoom * 100}%`, minWidth: 760 * zoom }}>
        <defs><marker id={marker} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" /></marker></defs>
        <defs><marker id={`${marker}-highlight`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#087f77" /></marker></defs>
        {orderedLinks.map((l, i) => {
          const a = positions.get(l.source), b = positions.get(l.target), vertical = a.x === b.x;
          const direction = b.x > a.x ? 1 : -1, down = b.y > a.y ? 1 : -1;
          const x1 = a.x + (vertical ? 0 : direction * 110), x2 = b.x - (vertical ? 0 : direction * 115);
          const y1 = a.y + (vertical ? down * 34 : 0), y2 = b.y - (vertical ? down * 38 : 0);
          return <g key={`${l.source}-${l.target}-${i}`} className={`med-graph__edge ${selected ? isSelectedLink(l) ? "is-highlighted" : "is-dimmed" : ""} ${l.relationship === "INTERACTS_WITH" ? "med-graph__edge--interaction" : ""}`}><path d={`M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`} markerEnd={`url(#${isSelectedLink(l) ? `${marker}-highlight` : marker})`} /><text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 7} textAnchor="middle">{relation(l)}</text></g>;
        })}
        {[...centers, ...visible].map(n => {
          const p = positions.get(n.id), words = n.name.match(/.{1,25}(\s|$)|\S{1,25}/g) || [n.name];
          return <g key={n.id} role="button" tabIndex="0" aria-label={`${labels[kind(n)] || "Entity"}: ${n.name}`} aria-pressed={selected?.id === n.id} onClick={() => selectNode(n)} onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectNode(n); } }} className={`med-graph__node ${selected ? highlightedIds.has(n.id) ? "is-connected" : "is-dimmed" : ""} med-graph__node--${kind(n)} ${centerIds.has(n.id) ? "med-graph__node--focus" : ""} ${selected?.id === n.id ? "is-selected" : ""}`} transform={`translate(${p.x},${p.y})`}>
            <title>{n.name}</title><rect x="-110" y="-34" width="220" height="68" rx="12" /><circle cx="-93" cy="-19" r="4" /><text className="med-graph__type" x="-82" y="-15">{centerIds.has(n.id) ? "SELECTED MEDICINE" : labels[kind(n)]}</text>
            {words.slice(0, 2).map((line, i) => <text key={i} x="-94" y={5 + i * 16}>{line.trim()}{i === 1 && words.length > 2 ? "…" : ""}</text>)}
          </g>;
        })}
      </svg></div>
      {!relatedLinks.length && <p className="med-graph__message">No relationships are recorded for this selection in the current dataset.</p>}
      <footer className="med-graph__footer"><span>{neighbors.length ? `Showing ${page * 10 + 1}–${Math.min((page + 1) * 10, neighbors.length)} of ${neighbors.length} related nodes` : "No related nodes in this view"}</span>{neighbors.length > 10 && <div><button disabled={!page} onClick={() => { setPage(page - 1); setSelected(null); }}>Previous</button><button disabled={(page + 1) * 10 >= neighbors.length} onClick={() => { setPage(page + 1); setSelected(null); }}>Next connections</button></div>}</footer>
      {selected && <aside className="med-graph__details" aria-label="Node details"><button className="med-graph__close" aria-label="Close node details" onClick={() => setSelected(null)}>×</button><p className="med-graph__eyebrow">{labels[kind(selected)]}</p><h3>{selected.name}</h3><ul>{relatedLinks.filter(l => l.source === selected.id || l.target === selected.id).map((l, i) => <li key={i}>{data.nodes.find(n => n.id === l.source)?.name} <strong>{relation(l)}</strong> {data.nodes.find(n => n.id === l.target)?.name}{l.severity ? ` · ${l.severity}` : ""}</li>)}</ul></aside>}
    </>}
  </section>;
}
