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

function getLocalizedValue(medicine, field) {
	// First try the normal field used by OCR
	if (
		medicine[field] !== null &&
		medicine[field] !== undefined &&
		String(medicine[field]).trim() !== ""
	) {
		return medicine[field];
	}

	// Then try language-specific fields
	const languageFields = [
		`${field}_en`,
		`${field}_kn`,
		`${field}_tulu`,
	];

	for (const key of languageFields) {
		if (
			medicine[key] !== null &&
			medicine[key] !== undefined &&
			String(medicine[key]).trim() !== ""
		) {
			return medicine[key];
		}
	}

	return null;
}

function MedicineCard({ medicine }) {
	if (!medicine) {
		return (
			<div
				className="medicine-card medicine-card--empty"
				role="status"
				aria-live="polite"
			>
				<div className="medicine-card__empty-icon">!</div>

				<h2>Medicine not found in database.</h2>

				<p>
					Try uploading a clearer image or an image with the
					medicine name more visible.
				</p>
			</div>
		);
	}

	const description = getLocalizedValue(medicine, "description");
	const sideEffects = getLocalizedValue(medicine, "side_effects");
	const contraindications = getLocalizedValue(
		medicine,
		"contraindications"
	);
	const warnings = getLocalizedValue(medicine, "warnings");
	const majorInteractions = getLocalizedValue(
		medicine,
		"major_interactions"
	);

	const activeIngredient =
		getLocalizedValue(medicine, "active_ingredient");

	const disease =
		getLocalizedValue(medicine, "disease");

	return (
		<article className="medicine-card">

			<div className="medicine-card__header">

				<div>
					<p className="medicine-card__eyebrow">
						Scan Result
					</p>

					<h2 className="medicine-card__title">
						{formatValue(medicine.drug_name)}
					</h2>

					<p className="medicine-card__subtitle">
						{formatValue(medicine.generic_name)}
					</p>
				</div>

				<div
					className="medicine-card__badges"
					aria-label="Medicine classifications"
				>
					<span className="medicine-badge medicine-badge--disease">
						{formatValue(disease)}
					</span>

					<span className="medicine-badge medicine-badge--class">
						{formatValue(medicine.drug_class)}
					</span>
				</div>

			</div>

			<dl className="medicine-card__details">

				<div className="medicine-card__detail-row">
					<dt>Drug Name</dt>
					<dd>
						{formatValue(medicine.drug_name)}
					</dd>
				</div>

				<div className="medicine-card__detail-row">
					<dt>Generic Name</dt>
					<dd>
						{formatValue(medicine.generic_name)}
					</dd>
				</div>

				<div className="medicine-card__detail-row">
					<dt>Disease</dt>
					<dd>
						{formatValue(disease)}
					</dd>
				</div>

				<div className="medicine-card__detail-row">
					<dt>Drug Class</dt>
					<dd>
						{formatValue(medicine.drug_class)}
					</dd>
				</div>

				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Active Ingredient</dt>
					<dd>
						{formatValue(activeIngredient)}
					</dd>
				</div>

				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Description</dt>
					<dd>
						{formatValue(description)}
					</dd>
				</div>

				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Side Effects</dt>
					<dd>
						{formatValue(sideEffects)}
					</dd>
				</div>

				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Contraindications</dt>
					<dd>
						{formatValue(contraindications)}
					</dd>
				</div>

				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Warnings</dt>
					<dd>
						{formatValue(warnings)}
					</dd>
				</div>

				<div className="medicine-card__detail-row medicine-card__detail-row--full">
					<dt>Major Interactions</dt>
					<dd>
						{formatValue(majorInteractions)}
					</dd>
				</div>

			</dl>

		</article>
	);
}

export default MedicineCard;