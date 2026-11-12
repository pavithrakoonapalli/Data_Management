"""Independent checks of the generated project outputs. Exits with an error if any check fails."""
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx
import nbformat
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_SHA256 = "43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d"  # official UCI file
RAW_ROWS = 541909
results = []


def check(name, passed, detail=""):
    results.append(bool(passed))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))


def read(name, **kwargs):
    return pd.read_csv(ROOT / "C_Cleaning/output" / name, low_memory=False, **kwargs)


ids = {"InvoiceNo": str, "StockCode": str}
raw_file = ROOT / "data/raw/Online Retail.xlsx"
check("raw Excel file matches official UCI file", hashlib.sha256(raw_file.read_bytes()).hexdigest() == RAW_SHA256)

raw, cleaned, returns, excluded = (read(f, dtype=ids) for f in ["online_retail_raw.csv", "online_retail_cleaned.csv",
                                                                "online_retail_returns.csv", "online_retail_excluded.csv"])
audit = read("audit_log.csv")

check("raw CSV has all rows", len(raw) == RAW_ROWS, f"{len(raw):,}")
check("cleaned + returns + excluded = raw", len(cleaned) + len(returns) + len(excluded) == RAW_ROWS,
      f"{len(cleaned):,} + {len(returns):,} + {len(excluded):,}")
check("audit: each step starts where the last ended", (audit["rows_before"].iloc[1:].values == audit["rows_after"].iloc[:-1].values).all())
check("audit: removed = before - after", (audit["rows_before"] - audit["rows_after"] == audit["rows_removed"]).all())
check("audit: start and end match files", audit["rows_before"].iloc[0] == RAW_ROWS and audit["rows_after"].iloc[-1] == len(cleaned))
check("audit: revenue matches cleaned file", abs(audit["revenue_gbp_after"].iloc[-1] - cleaned["LineRevenue"].sum()) < 1,
      f"{cleaned['LineRevenue'].sum():,.2f}")

check("cleaned: no duplicates", cleaned[list(raw.columns)].duplicated().sum() == 0)
check("cleaned: quantity and price positive", (cleaned["Quantity"] > 0).all() and (cleaned["UnitPrice"] > 0).all())
check("cleaned: descriptions present", cleaned["Description"].notna().all())
check("cleaned: no cancellation invoices", not cleaned["InvoiceNo"].str.startswith("C").any())
check("cleaned: StockCode upper case", (cleaned["StockCode"] == cleaned["StockCode"].str.upper()).all())
check("cleaned: real products retained", cleaned["StockCode"].str.startswith("DCGS").any() and cleaned["StockCode"].eq("PADS").any())
check("cleaned: administrative codes gone", not cleaned["StockCode"].isin(["POST", "DOT", "M", "C2", "BANK CHARGES", "AMAZONFEE"]).any())
check("cleaned: CustomerID whole numbers", (cleaned["CustomerID"].dropna() % 1 == 0).all())
check("cleaned: HasCustomerID agrees", (cleaned["HasCustomerID"] == cleaned["CustomerID"].notna()).all())
check("cleaned: max quantity below 10,000", cleaned["Quantity"].max() < 10000, str(cleaned["Quantity"].max()))

register = pd.read_csv(ROOT / "B_Quality/output/quality_issue_register.csv")
check("register: at least 3 dimensions", register["dimension"].nunique() >= 3, ", ".join(sorted(register["dimension"].unique())))
check("register: root cause and impact filled", register[["root_cause_hypothesis", "downstream_impact"]].notna().all().all())
check("register IDs used by audit log", set(",".join(audit["b_issue"]).replace(" ", "").split(",")) <= set(register["id"]))
for chart in ["chart1_missing_values", "chart2_quality_issues", "chart3_quantity_extremes", "chart4_missing_customer_by_month"]:
    check(f"figure exists: {chart}", (ROOT / f"B_Quality/figures/{chart}.png").stat().st_size > 5000)

output = ROOT / "D_Graph/output"
G = nx.read_gexf(output / "copurchase_network.gexf")
nodes, edges = pd.read_csv(output / "node_metrics.csv", dtype={"StockCode": str}), pd.read_csv(output / "edge_list.csv", dtype={"source": str, "target": str})
summary = json.loads((output / "graph_summary.json").read_text(encoding="utf-8"))["graph"]
check("graph: GEXF, CSV and JSON agree", G.number_of_nodes() == len(nodes) == summary["nodes"] and G.number_of_edges() == len(edges) == summary["edges"],
      f"{len(nodes)} nodes, {len(edges)} edges")
check("graph: degree centrality = degree / (n-1)", ((nodes["degree"] / (len(nodes) - 1) - nodes["degree_centrality"]).abs() < 0.0001).all())

sales = cleaned[~cleaned["LaterCancelled"]]
sample = edges.head(5).to_dict("records")
counts_ok = all(len(set(sales.loc[sales.StockCode == e["source"], "InvoiceNo"]) & set(sales.loc[sales.StockCode == e["target"], "InvoiceNo"])) == e["weight"] for e in sample)
check("graph: top 5 weights recomputed from cleaned data", counts_ok)

metadata = json.loads((ROOT / "A_FAIR/metadata_record.json").read_text(encoding="utf-8"))
check("metadata: 8 variables match data columns", [v["name"] for v in metadata["variableMeasured"]] == list(raw.columns))
check("metadata: required fields", all(k in metadata for k in ["name", "description", "identifier", "creator", "publisher", "license", "distribution", "temporalCoverage"]))

for path in ["B_Quality/profiling.ipynb", "C_Cleaning/cleaning.ipynb", "D_Graph/graph.ipynb"]:
    code = [c for c in nbformat.read(ROOT / path, as_version=4).cells if c.cell_type == "code"]
    errors = sum(o.output_type == "error" for c in code for o in c.outputs)
    check(f"notebook fully executed without errors: {path}", all(c.execution_count for c in code) and errors == 0, f"{len(code)} code cells")

# ---- Cross-component definitions (B, C, A and the graph must agree)
from quality_rules import RECORD_ADMIN_REVERSAL, RECORD_PRODUCT_CANCELLATION, RECORD_STOCK_ADJUSTMENT, is_admin_code, is_cancellation

kinds = returns["RecordType"].value_counts()
check("returns: exactly three record types", set(kinds.index) == {RECORD_PRODUCT_CANCELLATION, RECORD_ADMIN_REVERSAL, RECORD_STOCK_ADJUSTMENT}, kinds.to_dict())
check("returns: no administrative code classed as product cancellation", not (returns["RecordType"].eq(RECORD_PRODUCT_CANCELLATION) & is_admin_code(returns["StockCode"])).any())
admin_rows = returns[returns["RecordType"] == RECORD_ADMIN_REVERSAL]
check("returns: administrative reversals all on 'C' invoices with admin codes", is_cancellation(admin_rows["InvoiceNo"]).all() and is_admin_code(admin_rows["StockCode"]).all(), f"{len(admin_rows)} rows")
check("returns: financial value preserved", abs(returns["LineRevenue"].sum() - (returns["Quantity"] * returns["UnitPrice"]).sum()) < 1, f"{returns['LineRevenue'].sum():,.2f}")
summary_file = read("returns_summary.csv")
check("returns summary agrees with returns file", summary_file["rows"].sum() == len(returns) and abs(summary_file["value_gbp"].sum() - returns["LineRevenue"].sum()) < 1)

q = register.set_index("id")
step = audit.set_index(audit["step"].astype(str))
check("Q9: register, audit log and before/after agree", q.loc["Q9", "rows_affected"] == step.loc["2", "cells_changed"] == int(read("before_after_summary.csv").set_index("measure").loc["Q9 lower-case StockCode rows", "before"]), str(q.loc["Q9", "rows_affected"]))
check("Q1: register matches raw missing CustomerID", q.loc["Q1", "rows_affected"] == raw["CustomerID"].isna().sum(), str(q.loc["Q1", "rows_affected"]))
check("Q12: measured in identifier columns, not rows", q.loc["Q12", "count_unit"] == "identifier columns" and q.loc["Q12", "rows_affected"] == 3)
check("register: dimensions of Q4, Q5, Q6, Q8", [q.loc[i, "dimension"] for i in ["Q4", "Q5", "Q6", "Q8"]] == ["Consistency", "Validity", "Validity", "Validity"])

sensitivity = pd.read_csv(output / "threshold_sensitivity.csv")
baseline = sensitivity[sensitivity["is_baseline"]]
check("graph: sensitivity baseline equals the published graph", len(baseline) == 1 and baseline["nodes"].iloc[0] == summary["nodes"] and baseline["edges"].iloc[0] == summary["edges"], f"{len(sensitivity)} settings")
graph_notebook = (ROOT / "D_Graph/graph.ipynb").read_text(encoding="utf-8")
check("graph: outdated wording removed", "previous figure" not in graph_notebook and "LOCATED_IN" not in graph_notebook and "natural anchor" not in graph_notebook)

manifest = {f["file"]: f for f in json.loads((ROOT / "C_Cleaning/output/file_manifest.json").read_text(encoding="utf-8"))}
check("manifest: sizes and checksums match files", all((ROOT / "C_Cleaning/output" / name).stat().st_size == entry["bytes"] and hashlib.sha256((ROOT / "C_Cleaning/output" / name).read_bytes()).hexdigest() == entry["sha256"] for name, entry in manifest.items() if name.endswith(".csv")), f"{len(manifest)} files")
source_part = metadata["distribution"][0]["hasPart"]
check("metadata: source file size and checksum match raw file", source_part["sha256"] == RAW_SHA256 and source_part["contentSize"] == f"{raw_file.stat().st_size} bytes")

# ---- Added during finalisation: limitations must be backed by generated outputs
variants = pd.read_csv(output / "invoice_definition_sensitivity.csv").set_index("variant")
check("graph: invoice-definition baseline equals the published graph", variants.loc["baseline", "nodes"] == summary["nodes"] and variants.loc["baseline", "edges_shared_with_baseline"] == summary["edges"])
check("graph: five invoice-definition variants recorded", len(variants) == 5)
residual = json.loads((ROOT / "C_Cleaning/output/cleaning_residual_checks.json").read_text(encoding="utf-8"))
check("cleaning: matched + unmatched = product cancellations", residual["matched_exactly"] + residual["unmatched"] == residual["product_cancellation_lines"] == kinds[RECORD_PRODUCT_CANCELLATION], f"{residual['matched_exactly']} + {residual['unmatched']}")
check("cleaning: matched flag agrees with audit log", residual["matched_exactly"] == step.loc["11", "cells_changed"])
check("cleaning: residual non-product rows present in cleaned data", residual["non_product_descriptions_remaining_rows"] == int(cleaned["StockCode"].isin(["23444", "23702"]).sum()))
miss = json.loads((ROOT / "B_Quality/output/missing_customer_profile.json").read_text(encoding="utf-8"))
check("profiling: invoice-level missing CustomerID recorded", miss["invoices_total"] == raw["InvoiceNo"].nunique())
check("FAIR: gap 7 does not attribute a format judgement to F-UJI", "proprietary" not in (ROOT / "A_FAIR/gap_table.md").read_text(encoding="utf-8"))
check("register: Q1 cause stated as possibilities", "Possible explanations" in q.loc["Q1", "root_cause_hypothesis"])

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
