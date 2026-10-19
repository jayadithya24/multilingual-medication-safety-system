# DDInter source and derived data

Provider: Computational Biology & Drug Design Group, DDInter.
Official downloads: https://ddinter.scbdd.com/download/
Terms: https://ddinter.scbdd.com/terms/
License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0
(https://creativecommons.org/licenses/by-nc-sa/4.0/).
Citation: DDInter: an online drug–drug interaction database towards improving
clinical decision-making and patient safety. Nucleic Acids Research.
https://doi.org/10.1093/nar/gkab880

Raw downloads are unmodified. `provenance.json` records their URLs and SHA-256
hashes. `deduplicated_pairs.csv` is a derived, filtered export created by this
project: unordered duplicate pairs, conflicting labels, self-pairs and ungraded
records are removed, and reproducible train/validation/test assignments added.
The derived export is shared under the same CC BY-NC-SA 4.0 terms. The provider
does not endorse this project or its predictions. No clinical validity is
implied. See `ml/DDINTER_MODEL.md` for model limitations and reproduction.
