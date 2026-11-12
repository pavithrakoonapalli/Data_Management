# Online Retail: Data Management Project (Winter 2026/27)

An assessment of the UCI **Online Retail** dataset (DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33), CC BY 4.0, 541,909 rows, 8 variables). The project covers a FAIR assessment, data quality profiling, a reproducible cleaning pipeline, and a product co-purchase graph.

## How the parts connect

| Component | Question | Uses | Produces |
|---|---|---|---|
| **A: FAIR and metadata** | Can people and machines find and reuse the data? | F-UJI; finding Q16 from B | Gap table, PID table, proposed metadata record |
| **B: Quality and profiling** | How trustworthy is the raw data? | Raw file | Issues Q1–Q16, charts |
| **C: Cleaning pipeline** | How can the issues be fixed traceably? | B's issue IDs; A's country-code proposal | Cleaned, returns and excluded files; audit log |
| **D: Graph** | Which products are bought together? | C's cleaned sales | Co-purchase network, measures, sensitivity table |

## Folder structure

| Path | Contents |
|---|---|
| `data/raw/Online Retail.xlsx` | Original file (read only; matches the file in UCI's ZIP) |
| `quality_rules.py` | Definitions shared by B and C, including administrative codes and record types |
| `A_FAIR/` | `metadata_record.json` (schema.org JSON-LD), `gap_table.md`, `pid_table.md`, `fuji_and_metadata_notes.md`, F-UJI JSON export, `FAIR_Assessment/` screenshots |
| `B_Quality/` | `profiling.ipynb`, `figures/` (4 charts), `output/` (issue register, overlap table) |
| `C_Cleaning/` | `cleaning.ipynb`, `output/` (see below) |
| `D_Graph/` | `graph.py`, `graph.ipynb`, `output/` (see below) |
| `run_all.py`, `validate_project.py` | One-command run; independent checks of all outputs |

## Installation and running

**Python version.** The pipeline was run and validated on **Python 3.14.5**. Python 3.14 is not known to be required: all pinned packages are available for Python 3.13, but the full pipeline has not been run on 3.13 in this folder.

From this folder:

```
python -m venv .venv
.venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (macOS/Linux)
pip install -r requirements.txt
python run_all.py
```

`run_all.py` takes several minutes and stops with an error if any step or check fails. It runs, in this order:

1. `B_Quality/profiling.ipynb`
2. `C_Cleaning/cleaning.ipynb` (must come before the graph, which reads its output)
3. `D_Graph/graph.ipynb`
4. `D_Graph/graph.py` (regenerates the same graph files from the script)
5. `validate_project.py`

To run parts by hand, open the notebooks in the same order, each from its own folder. To regenerate only the graph after cleaning: `cd D_Graph` and `python graph.py`.

## Cleaning outputs (`C_Cleaning/output/`)

Every raw row is in exactly one of the first three files:

| File | Contents |
|---|---|
| `online_retail_cleaned.csv` | 522,538 product sales. Added columns: `CountryISO2`, `LaterCancelled`, `HasCustomerID`, `LineRevenue` |
| `online_retail_returns.csv` | 10,587 reversals and adjustments, with all original values, separated by `RecordType` |
| `online_retail_excluded.csv` | 8,784 removed rows, each with an `ExclusionReason` |
| `online_retail_raw.csv` | Unmodified CSV export of the Excel file |
| `audit_log.csv` | Before and after statistics for every step, linked to issue IDs |
| `before_after_summary.csv` | Component B's tests re-run on the raw and cleaned data |
| `returns_summary.csv` | Rows, quantity, value and missing customers by record type and administrative category |
| `file_manifest.json` | Size and SHA-256 checksum of the source and CSV files |
| `cleaning_residual_checks.json` | Cancellation matching coverage and remaining known limitations |

### Record types in the returns file

| `RecordType` | Meaning | Rows | Value (GBP) |
|---|---|---:|---:|
| `product cancellation` | A `C` invoice for real goods | 8,668 | -475,901.16 |
| `administrative reversal` | A `C` invoice on a non-product code (postage, fees, discounts, manual entries, samples). A financial reversal that cannot be identified as a product return; the content of manual entries is unknown. `AdminCategory` gives the kind | 583 | -418,078.57 |
| `stock adjustment` | Negative quantity, no `C` invoice, price 0: a warehouse correction | 1,336 | 0.00 |

The raw file has 8,704 product and 584 administrative `C` rows. The returns file holds 36 and 1 fewer because exact duplicates are removed first.

## Key definitions used across components

| Term | Definition | Figures |
|---|---|---|
| Missing CustomerID (Q1) | Rows without a customer | 135,080 raw (24.93%); 131,387 in cleaned sales (kept and flagged) |
| Q9 lower-case StockCode | Stored code differs from its upper-case form | 1,977 rows = 1,942 catalogue variants + 35 administrative codes. All 1,977 also lack a CustomerID |
| Q12 identifier types | A column-level issue | 3 identifier columns. The step that fixes them converts 1,426,483 numeric values |
| Country | Recorded per invoice; 8 of 4,333 customers in cleaned sales appear under two countries | Modelled as `(Invoice)-[:RECORDED_FOR_COUNTRY]->(Country)` |

Quality dimensions are defined in `B_Quality/profiling.ipynb`, section 5.

## Graph outputs (`D_Graph/output/`)

| File | Contents |
|---|---|
| `copurchase_network.gexf` | Graph for Gephi |
| `copurchase_network.png`, `property_graph_model.png` | Network figure and model diagram |
| `node_metrics.csv`, `edge_list.csv`, `community_summary.csv` | Product measures, product pairs, communities |
| `graph_summary.json` | How the graph was built, and graph-level statistics |
| `threshold_sensitivity.csv` | Results under 9 combinations of product and pair thresholds |
| `invoice_definition_sensitivity.csv`, `invoice_profile.json` | Baseline rebuilt on four other invoice definitions; products per invoice with and without a CustomerID |

## Known limitations

- Only 2,818 of 8,668 product cancellations (32.5% of lines, 89.5% of their value) match a sale exactly. The other 5,850 may be partial, relate to earlier sales, or lack a CustomerID, so total `LineRevenue` overstates net revenue. Filter on `LaterCancelled` to exclude sales cancelled in full.
- 383 raw cancellation rows (379 in the returns file) have no CustomerID, so they cannot be matched to a customer or to the original sale.
- A few non-product descriptions remain in the cleaned sales because their codes look like products (for example `Next Day Carriage`).
- An invoice is not necessarily one shopper's basket; invoices without a CustomerID are much larger. See `invoice_definition_sensitivity.csv`.
- Naming variation remains: some StockCodes still have more than one description. Wording was not changed.
- Root causes in the issue register are hypotheses; the source system is undocumented.
- Graph results describe a filtered network (100 products, 300 strongest pairs). Some measures, especially modularity, change with these thresholds. Shared invoices show association, not causation.
- The dataset ends in December 2011.
- AI assistance (Claude Code) was used to help prepare the code, the project documentation and drafts of the report. All AI-assisted output was reviewed by the authors, and the reported figures were checked against the pipeline outputs, but AI-generated content may still contain errors that were not detected.

## Licence and citation

Source data: Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33. Licensed under CC BY 4.0. The cleaned files are modified versions of the source.
