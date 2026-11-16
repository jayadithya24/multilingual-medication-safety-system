# Tulu dataset

The maintained source is `tulu_master_dataset.csv`, updated by the user to
100 medicines across 10 diseases on 19 October 2026. The backend reads this
CSV directly. The older workbook, importer and 30-drug generator are archived
under `artifacts/`; they must not overwrite the current CSV.

After editing, run `python tools/datasets/prepare_ml_data.py` and restart the backend.
See the export manifest's `missing_optional_fields` for the 11 missing
drug-class values; no translated clinical content is fabricated.

Tulu speech uses Kannada synthesis, so pronunciation depends on that voice.
Data integration checks do not certify medical accuracy or translation quality.

## User-confirmed terminology (24 October 2026)

Preserve these words when their sentence uses the confirmed meaning:

| Tulu | Meaning |
| --- | --- |
| ದೆತೊನ್ನಗ | while taking |
| ದೆತೊನರೆ | to take |
| ತಿನ್ಪಿನ | eating |
| ಕಾರ್ | leg |
| ಉಪ್ಪುನಕ್ಲೆಗ್ | who are having |
| ವೈದ್ಯೆರ್ (vaidyer) | doctor |
| ಬೋಡು (bodu) | need |
| ಕೊರ್ಪುನ (korpuna) | give |
| ಮಲ್ಪೆರೆ ಬಲ್ಲಿ (malpere balli) | do not do |
| ಆಪುಂಡು (aapundu) | happens |
| aavu | will happen (future tense) |
| aapina | becomes |
| ಬೇನೆ (bene) | pain |
| ಅತ್ತಂಡ (atthnda), ijjinda | or |
| ಇಜ್ಜಿ (ijji) | no |
| ತರೆ (tare) | head |
| ತರೆ ಬೇನೆ | headache |
| ಬಾಲೆ (baale) | child |
| untaayere | to stop |
| ತಿಂಗೊಳು (tingolu) | month |
| ತಿಂಡಿ (tindi) | food |
| ತಿಂಡಿದ ಒಟ್ಟುಗು ದೆತೊನ್ಲೆ | take with food |

Romanized alternatives above retain the user's spelling where the Kannada-script
form has not been confirmed. Tense, inflection and negative instructions require
sentence-level review: do not replace every `ಮಲ್ಪಡ` with a negative instruction,
because the current CSV also uses it in affirmative instructions. This glossary
records language corrections, not a clinical review of the medicine advice.
