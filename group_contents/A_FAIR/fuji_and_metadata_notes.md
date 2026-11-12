# F-UJI Results and Metadata Notes – Online Retail

Source: `fuji_report_10.24432_C5BW33.json` (F-UJI 4.0.1, metric version 0.8).

## 1. Why F-UJI reports both 10/17 and 13/26

These numbers measure different things.

- **10 of 17** counts *metrics* with status "pass". Each metric counts once.
- **13 of 26** counts *points*. Metrics are worth 1 or 2 points, and a metric can earn part of its points. 13 / 26 = 50%, the headline score.

| Principle | Points | Percent | Metrics passed |
|---|---:|---:|---:|
| Findable | 5 / 7 | 71.43% | 3 / 5 |
| Accessible | 3 / 7 | 42.86% | 3 / 4 |
| Interoperable | 2 / 6 | 33.33% | 1 / 3 |
| Reusable | 3 / 6 | 50% | 3 / 5 |
| **Total** | **13 / 26** | **50%** | **10 / 17** |

F-UJI evaluates specific machine-testable FAIR indicators. Its score does not establish the overall quality or value of a dataset.

## 2. Failed, partly scored, and not-scored tests

**No complete metric was skipped.** All 17 metrics have a status of "pass" or "fail". However, F-UJI's debug messages show that it skipped **five internal checks**, because the access or data-identifier information they need is unavailable. This is consistent with gaps 3 and 5 in `gap_table.md`:

| # | Metric | Internal check skipped | Reason |
|---|---|---|---|
| 1 | FsF-F1-01MD | Uniqueness | No data identifier |
| 2 | FsF-A1-01M | Standard terms | No access information |
| 3 | FsF-A1-01M | Machine readability | No access information |
| 4 | FsF-A1.1-01MD | Protocol (for data) | No data identifier |
| 5 | FsF-A1.2-01MD | Authentication (for data) | No data identifier |

These notes do not change any F-UJI result or score.

**Metrics with status "fail" (7):**

| Metric | Points | What failed |
|---|---:|---|
| FsF-F1-02MD | 1 / 1 | Persistent-identifier tests for the *data* failed, but they carry 0 points; see below |
| FsF-F3-01M | 0 / 1 | The metadata has no link to the downloadable data |
| FsF-A1-01M | 0 / 1 | Access conditions are not in the metadata |
| FsF-I2-01M | 0 / 2 | No terms from registered vocabularies |
| FsF-I3-01M | 0 / 2 | No references to related resources |
| FsF-R1.1-01M | 0 / 1 | No licence in the metadata |
| FsF-R1.3-02D | 0 / 1 | The file-format check could not run, because no data content identifier is available; F-UJI did not assess the Excel format |

**Passed, but only partly scored (5):** FsF-F2-01M, FsF-A1-02MD, FsF-A1.1-01MD, FsF-A1.2-01MD and FsF-R1-01M each earned 1 of 2 points. In the A1 tests, the part concerning the metadata passed and the part concerning the data failed, because no data link was found.

**Failed but not scored:** four sub-tests are worth 0 points, so they cannot change the score: FsF-F1-01MD-2, FsF-F1-02MD-4, FsF-F1-02MD-5 and FsF-R1-01M-3. This is why FsF-F1-02MD has status "fail" while earning 1 of 1 point.

**Numbering gaps:** some sub-test numbers are absent from the export, for example FsF-F2-01M-1, FsF-F3-01M-1, FsF-I2-01M-1, FsF-F1-02MD-3 and FsF-R1.3-01M-2. The export does not say why, so we make no claim about them.

## 3. Screenshot and JSON dates

| Evidence | Date | Source of the date |
|---|---|---|
| `Capture1`–`Capture5` | 1 November 2026, about 20:38–20:41 local time | File creation time |
| `detailedview*.PNG` (the two checked) | 2 November 2026, from about 14:22 local time | File creation time |
| F-UJI JSON | 2 November 2026, 15:03:32 UTC (16:03 local time) | `start_timestamp` inside the JSON |

The Capture screenshots show the banner "Showing cached or saved response" and a saved assessment entry that appears to be dated 2026-11-01. So they show an earlier saved result. The JSON records a run on 2 November.

**What can be said:** the score shown in the screenshots (50%; F 5/7, A 3/7, I 2/6, R 3/6) is identical to the JSON. **What cannot be confirmed:** whether the screenshots and JSON come from one run. File creation times can also change when files are copied. The JSON is therefore cited as the record of the assessment (2 November 2026), and the screenshots as supporting evidence.

Screenshot `detailedview34` does not exist, so gaps 5–7 cite the JSON.

## 4. Status of each metadata field

Checked against the public DataCite and UCI records on 8 November 2026.

| Field in `metadata_record.json` | Value | Basis |
|---|---|---|
| `identifier` | 10.24432/C5BW33 | DataCite |
| `datePublished` | 2015 | DataCite gives the year only. The source notes record UCI's "Donated on 11/5/2015", but the date format is ambiguous, so no exact date is claimed |
| `dateModified` | 2024-10-21 | UCI "last updated" field |
| `inLanguage` | en | **Our observation** of the Description field. DataCite has no language value |
| `version` | *not included* | **Unverified:** neither DataCite nor UCI publishes a version |
| Provenance (`additionalProperty`) | see record | UCI page; the source business system remains undocumented |
| Creator ORCID | *not included* | **Unverified:** none found in the record |
| ZIP `contentSize` | 23715478 bytes | Earlier review; not confirmed again on 8 November, as the server returned no size |
| ZIP checksum | *not included* | **Unverified:** the original ZIP is not in the project |
| XLSX size and SHA-256 | see record | Computed from `data/raw/Online Retail.xlsx` and checked by `validate_project.py` |

## 5. Distribution of the XLSX and the derived CSV files

- The published distribution is the UCI **ZIP**. The **XLSX** is listed as its part (`hasPart`) because UCI offers no separate download link.
- The **CSV** files are our outputs and have not been published. They are deliberately *not* listed under `distribution`, as that would imply a download location that does not exist. Their sizes and SHA-256 checksums are in `C_Cleaning/output/file_manifest.json`.
- `online_retail_raw.csv` is an unmodified export of the XLSX. The other CSV files are derived data. If published, they would need their own identifier (see `pid_table.md`).

## 6. Agreement between Component A files

The gap table, PID table and metadata record use the same DOI, ROR, schema.org terms, country and currency standards, and related paper. As before, the metadata record is **our proposal**: F-UJI's score would change only if the repository published these fields, so no improved score is claimed.
