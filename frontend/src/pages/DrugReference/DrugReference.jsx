import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import LanguageSelector from "../../components/LanguageSelector/LanguageSelector";
import KnowledgeGraph from "../../components/KnowledgeGraph/KnowledgeGraph";
import { fetchMedicines, searchMedicine } from "../../services/medicineService";
import "./DrugReference.css";

export default function DrugReference() {
  const [medicines, setMedicines] = useState([]);
  const [medicine, setMedicine] = useState("");
  const [lang, setLang] = useState("en");
  const [drug, setDrug] = useState(null);
  const [error, setError] = useState("");
  const [listError, setListError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    fetchMedicines().then(data => { if (active) { setMedicines((data.medicines || []).sort()); setListError(""); } })
      .catch(() => { if (active) setListError("Unable to load medicines."); });
    return () => { active = false; };
  }, [retry]);
  useEffect(() => {
    if (!medicine) return;
    let active = true;
    searchMedicine(medicine, lang).then(data => {
      if (!active) return;
      const match = (data.results || []).find(n => n.drug_name?.toLowerCase() === medicine.toLowerCase());
      setDrug(match || null); setError(match ? "" : "No reference information is available for this medicine.");
    }).catch(() => { if (active) setError("Unable to load medicine information."); });
    return () => { active = false; };
  }, [medicine, lang]);
  const text = field => drug?.[`${field}_${lang}`] || drug?.[`${field}_en`] || drug?.[field] || "Not available in the current dataset.";
  return <div className="drug-reference-page reference-workspace">
    <section className="drug-reference-hero"><p className="drug-reference-kicker">MEDICATION REFERENCE</p><h1>Explore a medicine</h1><p>Choose a medicine to see its connected conditions, side effects and interactions.</p></section>
    <section className="reference-picker"><label>Choose a medicine<select aria-label="Choose a medicine" value={medicine} onChange={e => { setMedicine(e.target.value); setDrug(null); setError(""); }} disabled={!medicines.length}><option value="">{medicines.length ? "Select from the medicine list" : "Loading medicines…"}</option>{medicines.map(name => <option key={name}>{name}</option>)}</select></label><LanguageSelector selectedLanguage={lang} onLanguageChange={value => { setLang(value); setDrug(null); setError(""); }} /></section>
    {listError && <p role="alert">{listError} <button onClick={() => setRetry(retry + 1)}>Retry</button></p>}
    {!medicine ? <section className="reference-welcome"><span>01 / SELECT A MEDICINE</span><h2>Start with a medicine. Follow its connections.</h2><p>The graph will show only directly related nodes, with clinical reference details below.</p><div><b>Conditions treated</b><b>Recorded side effects</b><b>Related medicines</b></div></section> : <>
      <KnowledgeGraph key={medicine} drug1={medicine} />
      {error ? <p role="alert" className="drug-reference-error">{error}</p> : !drug ? <p role="status">Loading reference details…</p> : <section className="reference-details"><header><p className="drug-reference-kicker">CLINICAL REFERENCE</p><h2>{drug.drug_name}</h2><p>{drug.generic_name} · {drug.drug_class}</p></header><div className="reference-detail-grid">
        <article><h3>Overview</h3><p>{text("description")}</p><p><strong>Active ingredient:</strong> {drug.active_ingredient || drug.generic_name || "Not available"}</p></article>
        <article className="reference-warning"><h3>Warnings</h3><p>{text("warnings")}</p></article>
        <article><h3>Contraindications</h3><p>{text("contraindications")}</p></article>
        <article><h3>Explore interactions</h3><p>Select a medicine node in the graph to inspect its recorded relationships, or compare a specific pair in the interaction checker.</p><Link to="/drug-interaction">Compare two medicines →</Link></article>
      </div></section>}
    </>}
  </div>;
}
