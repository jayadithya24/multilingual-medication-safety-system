import "./MedicineCard.css";

function formatValue(value) {
	if (value === null || value === undefined) {
		return "N/A";
	}

	if (Array.isArray(value)) {
		return value.length > 0 ? value.join(", ") : "N/A";
	}

	const text = String(value).trim();
	return text ? text : "N/A";
}

function MedicineCard({ medicine }) {
	if (!medicine) {
		return (
			<div className="medicine-card medicine-card--empty" role="status" aria-live="polite">
				<div className="medicine-card__empty-icon">!</div>
				<h2>Medicine not found in database.</h2>
				<p>
					Try uploading a clearer image or an image with the medicine name more visible.
				</p>
			</div>
		);
	}

	return (
		<article className="medicine-card">
			<div className="medicine-card__header">
				<div>
					<p className="medicine-card__eyebrow">Scan Result</p>
					<h2 className="medicine-card__title">{formatValue(medicine.drug_name)}</h2>
					<p className="medicine-card__subtitle">
						{formatValue(medicine.generic_name)}
					</p>
				</div>

				<div className="medicine-card__badges" aria-label="Medicine classifications">
					<span className="medicine-badge medicine-badge--disease">
						{formatValue(medicine.disease)}
					</span>
					<span className="medicine-badge medicine-badge--class">
						{formatValue(medicine.drug_class)}
					</span>
				</div>
			</div>

			<dl className="medicine-card__details">
				<div className="medicine-card__detail-row">
					<dt>Drug Name</dt>
					<dd>{formatValue(medicine.drug_name)}</dd>
				</div>
				<div className="medicine-card__detail-row">
					<dt>Generic Name</dt>
					<dd>{formatValue(medicine.generic_name)}</dd>
				</div>
				<div className="medicine-card__detail-row">
					<dt>Disease</dt>
					<dd>{formatValue(medicine.disease)}</dd>
				</div>
				<div className="medicine-card__detail-row">
					<dt>Drug Class</dt>
					<dd>{formatValue(medicine.drug_class)}</dd>
				</div>
				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Active Ingredient</dt>
					<dd>{formatValue(medicine.active_ingredient)}</dd>
				</div>
				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Description</dt>
					<dd>{formatValue(medicine.description)}</dd>
				</div>
				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Side Effects</dt>
					<dd>{formatValue(medicine.side_effects)}</dd>
				</div>
				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Contraindications</dt>
					<dd>{formatValue(medicine.contraindications)}</dd>
				</div>
				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Warnings</dt>
					<dd>{formatValue(medicine.warnings)}</dd>
				</div>
				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Major Interactions</dt>
					<dd>{formatValue(medicine.major_interactions)}</dd>
				</div>
			</dl>
		</article>
	);
}

export default MedicineCard;
