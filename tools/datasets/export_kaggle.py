"""Build a local publication draft. Does not assign rights or upload anything."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
from sync_datasets import validate, DATA, ROOT

FIELDS = {
    'drug_id': 'Stable English-slug medicine identifier shared across languages.',
    'drug_name': 'Shared medicine display name; 100 distinct names per file.',
    'generic_name': 'Supplied generic name, possibly localized.',
    'disease': 'Supplied localized catalog category, not an exhaustive indication list.',
    'drug_class': 'Supplied pharmacological class; blank where not provided.',
    'active_ingredient': 'Supplied ingredient text; not independently verified.',
    'description': 'Supplied educational medicine description.',
    'side_effects': 'Supplied side-effect text; not observed patient outcomes.',
    'contraindications': 'Supplied contraindication text.',
    'warnings': 'Supplied precaution text.',
    'major_interactions': 'Supplied narrative, not validated pair labels or a complete interaction database.',
    'source': 'Attribution supplied by the author; citations and redistribution permissions are not independently verified.',
}

def main():
    # This is explicitly a non-publishable draft with a missing-field audit.
    frames = validate(allow_incomplete=True)
    output = ROOT / 'artifacts/kaggle-multilingual-medication-draft'
    output.mkdir(parents=True, exist_ok=True)
    audit, hashes, sources, resources = {}, {}, [], []
    for language, frame in frames.items():
        name = f'{language}_master_dataset.csv'
        shutil.copyfile(DATA / name, output / name)
        hashes[name] = hashlib.sha256((output / name).read_bytes()).hexdigest()
        repeated = {field: [{'text': value, 'count': int(count)} for value, count in frame[field].value_counts().items() if count > 1]
                    for field in ('description', 'major_interactions')}
        audit[language] = {'rows': len(frame), 'diseases': frame.disease.nunique(),
                           'missing_fields': {field: frame.loc[frame[field].str.strip().eq(''), 'drug_id'].tolist() for field in frame if frame[field].str.strip().eq('').any()},
                           'repeated_narratives': repeated}
        sources.extend({'language': language, 'drug_id': row.drug_id, 'source_as_supplied': row.source,
                        'exact_source_url': '', 'permission_or_license_evidence': '', 'review_status': 'unverified'} for row in frame.itertuples())
        resources.append({'path': name, 'description': f'{language.title()}: 100 medicine rows across 10 categories.',
                          'schema': {'fields': [{'name': field, 'type': 'string', 'description': FIELDS[field]} for field in frame.columns]}})
    with (output / 'SOURCE_REVIEW.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sources[0]))
        writer.writeheader()
        writer.writerows(sources)
    (output / 'checksums.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    (output / 'quality-report.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    metadata = {'title': 'Multilingual Medication Reference: 100 Medicines',
                'id': 'YOUR_KAGGLE_USERNAME/multilingual-medication-reference',
                'subtitle': 'English, Kannada and Tulu educational catalog across 10 disease categories',
                'description': 'Publication draft. Rights, authorship and translation review pending. See DATASET_CARD.md and LICENSE_REVIEW.md.',
                'licenses': [{'name': 'unknown'}], 'resources': resources}
    # Intentionally not an upload-ready filename: username and rights are unresolved.
    (output / 'dataset-metadata.template.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    card = '''# Multilingual medication reference — publication draft

Three UTF-8 CSVs contain 100 medicines each across 10 categories. These are
300 localized records about 100 shared medicines, not 300 distinct medicines.
Join files using `drug_id`. Disease labels are localized and have changed since
earlier project versions. The metadata template documents all 12 columns.

## Provenance and intended use

The project author supplied the CSV content directly. English, Kannada and
Tulu cell text is preserved; tab-delimited pasted files were converted to
standard quoted CSV. Human/AI authorship, translation method, individual source
URLs, dates and redistribution permissions still require author confirmation.
Source strings mention FDA DailyMed, DrugBank, RxNorm and ICMR; these are
supplied citations, not verified permission grants or verified source matches.

Use for exploratory multilingual information-retrieval demonstrations after
rights review. Not validated clinical guidance, a prescribing resource, or
patient data. The files contain no severity training targets. Do not infer
that an unlisted interaction is safe. The package excludes DDInter downloads,
synthetic patients, trained models, credentials and application records.

## Quality limitations

Tulu has 11 missing drug-class values. Some columns contain English text in
localized files. Repeated generic descriptions/interaction narratives appear
in the updated source; see quality-report.json for exact counts and examples.
Medical accuracy, category assignments, citations and translation equivalence
have not been clinically validated. The word correction requested by the
author must not be interpreted as independent translation certification.

## Before publication

Complete SOURCE_REVIEW.csv with exact sources and applicable redistribution
terms. Confirm authorship/translation methods and choose a compatible license
only when rights are established. Replace the template Kaggle username and
license, then rename dataset-metadata.template.json to dataset-metadata.json.
No upload or public publication has been performed by this exporter.
'''
    (output / 'DATASET_CARD.md').write_text(card, encoding='utf-8')
    review = '''# Licensing review — unresolved

No new license is granted by this draft. A source citation alone does not
establish the right to redistribute its wording or a derivative translation.
The `unknown` value is a draft placeholder, not publication clearance.

Check the exact DrugBank product/version/access agreement used:
https://trust.drugbank.com/drugbank-trust-center/drugbank-terms-of-service
Do not assume that public access or academic access permits Kaggle distribution.
Confirm applicable rights for all other cited sources and for translations.
Do not label the combined dataset CC0 or apply a blanket Creative Commons
license without confirming that all included material permits those terms.

Kaggle requires a selected dataset license and an owner/dataset identifier:
https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets_metadata.md

DDInter has separate CC BY-NC-SA terms and is not included in this package.
Its license does not license these three source CSVs.
'''
    (output / 'LICENSE_REVIEW.md').write_text(review, encoding='utf-8')
    shutil.make_archive(str(output), 'zip', output)
    print(json.dumps({'draft': str(output), 'zip': str(output) + '.zip', 'rows': 300, 'license_status': 'pending author/source review'}))

if __name__ == '__main__':
    main()
