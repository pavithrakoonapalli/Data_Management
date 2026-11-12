# FAIR Gap Table – Online Retail (DOI 10.24432/C5BW33)

F-UJI assessment (metric v0.8, software 4.0.1), run 2026-11-02: overall 50% (13/26, "moderate").
F 5/7 (71.43%), A 3/7 (42.86%), I 2/6 (33.33%), R 3/6 (50%).
Evidence: `fuji_report_10.24432_C5BW33.json` and the screenshots in `FAIR_Assessment/`.
Gaps 1 and 2 were re-checked against the live DataCite record on 2026-11-08 and were still present (`rightsList` empty, creator "Unknown").
The score, the failed tests and the screenshot dates are explained in `fuji_and_metadata_notes.md`.

| Gap # | Principle | F-UJI test | Score | Evidence | What is missing | Proposed improvement |
|---|---|---|---|---|---|---|
| 1 | Reusable (R1.1) | FsF-R1.1-01M | 0/1 | detailedview32: "License information unavailable in metadata" | The CC BY 4.0 licence is shown only as text on the UCI page, not in the machine-readable metadata | Add CC-BY-4.0 to the `rightsList` field of the DOI's DataCite metadata, with the licence URL https://creativecommons.org/licenses/by/4.0/ |
| 2 | Findable (F2) | FsF-F2-01M | 1/2 | detailedview7: `"creator": ["Unknown"]` | The UCI page names Daqing Chen (London South Bank University), but the metadata says "Unknown"; there is also no description of the data | Add Daqing Chen and London South Bank University (ROR https://ror.org/02vwnat91) to `creators`, an ORCID iD if the creator has one, and the UCI abstract to `descriptions` |
| 3 | Findable (F3) | FsF-F3-01M | 0/1 | detailedview15: "Valid data (content) identifier missing" | No link to the actual data file. This is also why the data-related sub-tests of A1, A1.1 and A1.2 fail (FsF-A1-02MD-2, FsF-A1.1-01MD-2, FsF-A1.2-01MD-2) | Add the direct download link using schema.org `contentUrl` (or DataCite `contentUrl`), with `encodingFormat` and file size |
| 4 | Interoperable (I2) | FsF-I2-01M | 0/2 | detailedview28: "NO known vocabulary namespace URI is found which is listed in the LOD registry" | Variables are described only in plain text (e.g. "sterling"), not with registered vocabularies | Describe variables with schema.org terms (which include the former GoodRelations commerce terms), as in `pid_table.md`; give UnitPrice currency as ISO 4217 GBP and countries as ISO 3166 codes. Countries are implemented in the cleaned data (`CountryISO2`) |
| 5 | Accessible (A1) | FsF-A1-01M | 0/1 | F-UJI JSON, test FsF-A1-01M-1 failed | The metadata does not state the access level or conditions | Add an access statement, e.g. DataCite `rightsList` entry with the access-rights URI for open access; schema.org `isAccessibleForFree` and `conditionsOfAccess` |
| 6 | Interoperable (I3) | FsF-I3-01M | 0/2 | F-UJI JSON, tests FsF-I3-01M-1 and -2 failed | No link to related resources, although UCI names an introductory paper | Add DataCite `relatedIdentifiers` with relation `IsDescribedBy` to DOI 10.1057/dbm.2012.17 |
| 7 | Reusable (R1.3) | FsF-R1.3-02D | 0/1 | F-UJI JSON, test FsF-R1.3-02D-1 failed | F-UJI could not perform this file-format check, because no data content identifier is available. It did not assess the Excel format | Provide a data content identifier so the check can run. Separately, and as our own accessibility recommendation rather than an F-UJI finding, also publish a plain-text format such as CSV, and declare it in the metadata. This project provides `.csv` exports |

**Related finding from Component B:** UCI states "Has Missing Values: No", but CustomerID has 135,080 and Description 1,454 missing values. The metadata statement should be corrected.

**How `metadata_record.json` addresses these gaps:** it supplies the creator, description, licence, access conditions, related paper, download link, format, size and vocabulary terms that F-UJI could not find. It is our proposed record. F-UJI's score would change only if the repository published these fields, so no improved score is claimed.
