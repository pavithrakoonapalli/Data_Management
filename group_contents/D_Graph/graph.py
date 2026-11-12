"""Graph modelling: product co-purchase network (Online Retail).

Input : ../C_Cleaning/output/online_retail_cleaned.csv
Output: files in ./output (GEXF for Gephi, CSV tables, JSON summary, PNG figures)

Run with:  python graph.py
graph.ipynb imports these same functions, so the notebook and script cannot disagree.
"""
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

HERE = Path(__file__).resolve().parent
INPUT_FILE = HERE.parent / "C_Cleaning" / "output" / "online_retail_cleaned.csv"
OUTPUT_DIR = HERE / "output"

TOP_PRODUCTS = 100  # candidate products: those appearing on the most invoices
TOP_EDGES = 300     # strongest co-purchase pairs retained, which keeps the graph readable
SEED = 42           # fixes the only randomised step (the Louvain robustness check)
SENSITIVITY_PRODUCTS = (50, 100, 150)  # alternative thresholds tested; 100 and 300 are the chosen baseline
SENSITIVITY_EDGES = (150, 300, 450)

COMMUNITY_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
OTHER_COLOUR = "#b8b7b0"


def load_sales(path=INPUT_FILE):
    """Load cleaned sales, leaving out sales that were later cancelled in full."""
    df = pd.read_csv(path, dtype={"InvoiceNo": str, "StockCode": str})
    return df[~df["LaterCancelled"]]


def select_products(df, n=TOP_PRODUCTS):
    """Return the n products on the most invoices (ties broken by StockCode)."""
    counts = df.groupby("StockCode")["InvoiceNo"].nunique().reset_index(name="invoices")
    return counts.sort_values(["invoices", "StockCode"], ascending=[False, True]).head(n)


def count_pairs(df, products):
    """Count, for every pair of products, the invoices containing both."""
    subset = df[df["StockCode"].isin(products)]
    pairs = Counter()
    for items in subset.groupby("InvoiceNo")["StockCode"].unique():
        pairs.update(combinations(sorted(items), 2))
    return pairs, subset


def build_graph(df, n_products=TOP_PRODUCTS, n_edges=TOP_EDGES):
    """Build the undirected, weighted Product-CO_PURCHASED_WITH-Product property graph."""
    top = select_products(df, n_products)
    pairs, subset = count_pairs(df, top["StockCode"])
    ranked = sorted(pairs.items(), key=lambda item: (-item[1], item[0]))
    kept = ranked[:n_edges]
    cutoff = kept[-1][1]

    invoice_count = dict(zip(top["StockCode"], top["invoices"]))
    total_invoices = df["InvoiceNo"].nunique()

    G = nx.Graph()
    for (a, b), w in kept:
        lift = (w / total_invoices) / ((invoice_count[a] / total_invoices) * (invoice_count[b] / total_invoices))
        jaccard = w / (invoice_count[a] + invoice_count[b] - w)
        G.add_edge(a, b, weight=int(w), lift=round(float(lift), 3), jaccard=round(float(jaccard), 4))

    grouped = subset.groupby("StockCode")
    names = grouped["Description"].agg(lambda s: s.mode().iloc[0])
    quantity = grouped["Quantity"].sum()
    revenue = grouped["LineRevenue"].sum()
    for node in G:
        G.nodes[node].update(label=names[node], invoice_count=int(invoice_count[node]),
                             total_quantity=int(quantity[node]), total_revenue=round(float(revenue[node]), 2))

    info = {
        "invoices_in_cleaned_sales": int(total_invoices),
        "candidate_products": int(n_products),
        "distinct_candidate_pairs": len(pairs),
        "edges_kept": len(kept),
        "weakest_kept_weight": int(cutoff),
        "pairs_tied_at_cutoff": sum(1 for _, w in ranked if w == cutoff),
        "ties_cut_off": sum(1 for _, w in ranked[n_edges:] if w == cutoff),
    }
    return G, info


def add_metrics(G):
    """Compute node measures, store them on the graph, and return them with graph-level statistics."""
    degree = nx.degree_centrality(G)
    strength = dict(G.degree(weight="weight"))
    betweenness = nx.betweenness_centrality(G)  # hops: each kept relationship counts equally
    for _, _, d in G.edges(data=True):
        d["distance"] = 1 / d["weight"]         # strong link = short distance
    betweenness_w = nx.betweenness_centrality(G, weight="distance")
    for _, _, d in G.edges(data=True):
        del d["distance"]                       # helper only, not a model property
    clustering = {n: float(v) for n, v in nx.clustering(G).items()}  # GEXF needs one type per attribute

    communities = nx.community.greedy_modularity_communities(G, weight="weight")
    community_of = {n: i for i, c in enumerate(communities) for n in c}

    components = sorted(nx.connected_components(G), key=len, reverse=True)
    main = G.subgraph(components[0]).copy()
    main_communities = nx.community.greedy_modularity_communities(main, weight="weight")
    louvain = nx.community.louvain_communities(main, weight="weight", seed=SEED)

    for name, values in [("degree_centrality", degree), ("weighted_degree", strength), ("betweenness", betweenness),
                         ("betweenness_weighted", betweenness_w), ("clustering", clustering), ("community", community_of)]:
        nx.set_node_attributes(G, values, name)
    nx.set_node_attributes(G, {n: n in components[0] for n in G}, "in_largest_component")

    metrics = pd.DataFrame({
        "product": nx.get_node_attributes(G, "label"),
        "invoice_count": nx.get_node_attributes(G, "invoice_count"),
        "degree": dict(G.degree()),
        "degree_centrality": degree,
        "weighted_degree": strength,
        "betweenness": betweenness,
        "betweenness_weighted": betweenness_w,
        "clustering": clustering,
        "community": community_of,
        "in_largest_component": nx.get_node_attributes(G, "in_largest_component"),
    }).round(4)
    metrics.index.name = "StockCode"

    summary = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "connected_components": len(components),
        "component_sizes": [len(c) for c in components],
        "largest_component_nodes": main.number_of_nodes(),
        "average_clustering": round(nx.average_clustering(G), 4),
        "average_clustering_weighted": round(nx.average_clustering(G, weight="weight"), 4),
        "communities_greedy_whole_graph": len(communities),
        "community_sizes_greedy_whole_graph": [len(c) for c in communities],
        "modularity_greedy_whole_graph": round(nx.community.modularity(G, communities, weight="weight"), 4),
        "communities_greedy_largest_component": len(main_communities),
        "modularity_greedy_largest_component": round(nx.community.modularity(main, main_communities, weight="weight"), 4),
        "communities_louvain_largest_component": len(louvain),
        "modularity_louvain_largest_component": round(nx.community.modularity(main, louvain, weight="weight"), 4),
        "spearman_popularity_vs_degree": round(metrics["invoice_count"].corr(metrics["degree"], method="spearman"), 3),
    }
    return metrics, summary


def edge_table(G):
    rows = [{"source": a, "target": b, "source_name": G.nodes[a]["label"], "target_name": G.nodes[b]["label"],
             "weight": d["weight"], "lift": d["lift"], "jaccard": d["jaccard"]} for a, b, d in G.edges(data=True)]
    return pd.DataFrame(rows).sort_values(["weight", "source", "target"], ascending=[False, True, True])


def community_table(metrics):
    rows = []
    for community, group in metrics.groupby("community"):
        leaders = group.sort_values("weighted_degree", ascending=False)["product"].head(5)
        rows.append({"community": int(community), "size": len(group), "top_products": " | ".join(leaders)})
    return pd.DataFrame(rows)


def sensitivity_table(df, product_options=SENSITIVITY_PRODUCTS, edge_options=SENSITIVITY_EDGES):
    """Rebuild the graph under other thresholds, to show which results depend on the chosen 100 and 300."""
    def ranked(metrics):
        return metrics.reset_index().sort_values(["degree", "weighted_degree", "StockCode"], ascending=[False, False, True])

    base_metrics, _ = add_metrics(build_graph(df)[0])
    base_top10 = set(ranked(base_metrics)["StockCode"].head(10))
    rows = []
    for n_products in product_options:
        for n_edges in edge_options:
            G, info = build_graph(df, n_products, n_edges)
            metrics, summary = add_metrics(G)
            order = ranked(metrics)
            rows.append({
                "top_products": n_products, "max_edges": n_edges,
                "is_baseline": n_products == TOP_PRODUCTS and n_edges == TOP_EDGES,
                "nodes": summary["nodes"], "edges": summary["edges"], "weakest_kept_weight": info["weakest_kept_weight"],
                "connected_components": summary["connected_components"], "largest_component_nodes": summary["largest_component_nodes"],
                "density": summary["density"], "modularity_largest_component": summary["modularity_greedy_largest_component"],
                "highest_degree_product": order["product"].iloc[0], "highest_degree": int(order["degree"].iloc[0]),
                "highest_betweenness_product": metrics.sort_values("betweenness", ascending=False)["product"].iloc[0],
                "top10_degree_shared_with_baseline": len(set(order["StockCode"].head(10)) & base_top10),
            })
    return pd.DataFrame(rows)


def invoice_definition_table(df):
    """Rebuild the baseline graph on other definitions of what counts as an invoice-level basket."""
    def ranked(metrics):
        return metrics.reset_index().sort_values(["degree", "weighted_degree", "StockCode"], ascending=[False, False, True])

    base_graph, _ = build_graph(df)
    base_metrics, _ = add_metrics(base_graph.copy())
    base_edges = {frozenset(e) for e in base_graph.edges()}
    base_top10 = set(ranked(base_metrics)["StockCode"].head(10))
    size = df.groupby("InvoiceNo")["StockCode"].nunique()
    large = size[size > size.quantile(0.99)].index
    month = df["InvoiceDate"].astype(str).str[5:7]
    variants = {
        "baseline": df,
        "customer_invoices_only": df[df["HasCustomerID"]],
        "largest_1_percent_of_invoices_removed": df[~df["InvoiceNo"].isin(large)],
        "october_to_december_removed": df[~month.isin(["10", "11", "12"])],
        "united_kingdom_only": df[df["Country"] == "United Kingdom"],
    }
    rows = []
    for name, part in variants.items():
        G, _ = build_graph(part)
        edges = {frozenset(e) for e in G.edges()}
        metrics, summary = add_metrics(G)
        order = ranked(metrics)
        rank = metrics["betweenness"].rank(ascending=False, method="min")
        rows.append({
            "variant": name, "invoices": int(part["InvoiceNo"].nunique()), "nodes": summary["nodes"], "edges": summary["edges"],
            "connected_components": summary["connected_components"], "largest_component_nodes": summary["largest_component_nodes"],
            "modularity_largest_component": summary["modularity_greedy_largest_component"], "edges_shared_with_baseline": len(edges & base_edges),
            "highest_degree_product": order["product"].iloc[0], "highest_degree": int(order["degree"].iloc[0]),
            "top10_degree_shared_with_baseline": len(set(order["StockCode"].head(10)) & base_top10),
            "alarm_clock_red_betweenness_rank": int(rank["22727"]) if "22727" in rank.index else None,
        })
    return pd.DataFrame(rows)


def invoice_profile(df):
    """Distinct products per invoice, with and without a CustomerID."""
    table = df.groupby("InvoiceNo").agg(products=("StockCode", "nunique"), has_customer=("HasCustomerID", "first"))
    result = {}
    for label, part in [("with_customer", table[table["has_customer"]]), ("without_customer", table[~table["has_customer"]])]:
        result[label] = {"invoices": len(part), "mean_products": round(float(part["products"].mean()), 1),
                         "median_products": float(part["products"].median()), "max_products": int(part["products"].max())}
    return result


def draw_network(G, metrics, path):
    """Largest component: size = weighted degree, colour = community, numbers = top bridges."""
    main = G.subgraph(max(nx.connected_components(G), key=len))
    pos = nx.kamada_kawai_layout(main)
    in_main = metrics.loc[list(main)]
    largest = in_main["community"].value_counts().index[:len(COMMUNITY_COLOURS)].tolist()
    colour = {c: COMMUNITY_COLOURS[i] for i, c in enumerate(largest)}
    max_strength = metrics["weighted_degree"].max()
    max_weight = max(d["weight"] for _, _, d in main.edges(data=True))

    fig, (ax, side) = plt.subplots(1, 2, figsize=(16, 9.5), gridspec_kw={"width_ratios": [2.5, 1]})
    nx.draw_networkx_edges(main, pos, ax=ax, edge_color="#9a9993", alpha=0.35,
                           width=[0.4 + 3 * main[a][b]["weight"] / max_weight for a, b in main.edges()])
    nx.draw_networkx_nodes(main, pos, ax=ax, edgecolors="white", linewidths=1.5,
                           node_size=[70 + 1500 * metrics.loc[n, "weighted_degree"] / max_strength for n in main],
                           node_color=[colour.get(metrics.loc[n, "community"], OTHER_COLOUR) for n in main])

    top = in_main.sort_values("betweenness", ascending=False).head(10)
    for i, node in enumerate(top.index):        # a white disc keeps each number readable on any node size
        ax.text(*pos[node], str(i + 1), ha="center", va="center", fontsize=10, fontweight="bold", color="#0b0b0b",
                bbox=dict(boxstyle="circle,pad=0.18", facecolor="white", linewidth=2.2,
                          edgecolor=colour.get(metrics.loc[node, "community"], OTHER_COLOUR)))
    ax.set_title(f"Products often on the same invoice: largest connected part ({main.number_of_nodes()} of {G.number_of_nodes()} products)", loc="left", fontsize=14)
    ax.axis("off")

    side.axis("off")
    y = 0.98
    side.text(0, y, "Numbered: top 10 bridges (betweenness)", fontweight="bold", va="top", transform=side.transAxes, fontsize=11)
    y -= 0.05
    for i, name in enumerate(top["product"]):
        side.text(0, y, f"{i + 1}. {name[:42]}", va="top", transform=side.transAxes, fontsize=9.5)
        y -= 0.036
    y -= 0.03
    side.text(0, y, "Colour: community, with its most connected product", fontweight="bold", va="top", transform=side.transAxes, fontsize=11)
    y -= 0.05
    for c in largest:
        group = in_main[in_main["community"] == c]
        leader = group.sort_values("weighted_degree", ascending=False)["product"].iloc[0]
        side.scatter([0.02], [y - 0.01], s=90, color=colour[c], transform=side.transAxes, clip_on=False)
        side.text(0.07, y, f"Community {c}: {len(group)} products\n{leader[:40]}", va="top", transform=side.transAxes, fontsize=9.5)
        y -= 0.06
    if in_main["community"].nunique() > len(largest):
        side.scatter([0.02], [y - 0.01], s=90, color=OTHER_COLOUR, transform=side.transAxes, clip_on=False)
        side.text(0.07, y, "Smaller communities", va="top", transform=side.transAxes, fontsize=9.5)
        y -= 0.036
    y -= 0.02
    side.text(0, y, "Node size: total co-purchase weight\nLine width: number of shared invoices\n\n"
                    f"Scope: the {TOP_PRODUCTS} products on most invoices and\nthe {TOP_EDGES} strongest pairs only. A link shows that\n"
                    "products share invoices, not that one\ncauses the other to be bought.", va="top", transform=side.transAxes, fontsize=9.5, color="#52514e")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    return fig


def draw_property_model(path):
    """Diagram of the property graph model: labels, relationship types and properties."""
    boxes = {
        "Customer": (0.13, 0.74, "customer_id (key)\noptional: many invoices have none"),
        "Invoice": (0.5, 0.74, "invoice_no (key)\ninvoice_date"),
        "Product": (0.87, 0.74, "stock_code (key), name,\ninvoice_count, total_quantity,\ntotal_revenue"),
        "Country": (0.5, 0.2, "name, iso2"),
    }
    fig, ax = plt.subplots(figsize=(13, 6.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    for label, (x, y, props) in boxes.items():
        ax.text(x, y, f"(:{label})\n{props}", ha="center", va="center", fontsize=10.5,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#eef4fc", edgecolor="#2a78d6", linewidth=1.5))

    def arrow(start, end, text, tx, ty):
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="-|>", color="#52514e", linewidth=1.5))
        ax.text(tx, ty, text, ha="center", va="center", fontsize=9.5, color="#0b0b0b", bbox=dict(facecolor="white", edgecolor="none", pad=2))

    arrow((0.265, 0.74), (0.415, 0.74), ":PLACED", 0.34, 0.74)
    arrow((0.585, 0.74), (0.735, 0.74), ":CONTAINS\n{quantity, unit_price}", 0.66, 0.74)
    arrow((0.5, 0.63), (0.5, 0.29), ":RECORDED_FOR_COUNTRY", 0.5, 0.46)

    ax.annotate("", xy=(0.87, 0.3), xytext=(0.87, 0.6), arrowprops=dict(arrowstyle="-", color="#eb6834", linewidth=2, linestyle="--"))
    ax.text(0.87, 0.2, "Derived projection, analysed in NetworkX:\n(:Product)-[:CO_PURCHASED_WITH]-(:Product)\nundirected {weight, lift, jaccard}", ha="center", va="center", fontsize=10,
            bbox=dict(facecolor="#fdf0ea", edgecolor="#eb6834", boxstyle="round,pad=0.5"))
    ax.text(0.13, 0.32, "Country belongs to the Invoice because\nsome customers appear under more\nthan one country, while each invoice\nhas exactly one.", ha="center", va="center", fontsize=9.5, color="#52514e")
    ax.set_title("Property graph model: source entities (blue) and the Product-Product projection analysed (orange)", loc="left", fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    return fig


def export(G, metrics, summary, info):
    OUTPUT_DIR.mkdir(exist_ok=True)
    metrics.sort_values("weighted_degree", ascending=False).to_csv(OUTPUT_DIR / "node_metrics.csv")
    edge_table(G).to_csv(OUTPUT_DIR / "edge_list.csv", index=False)
    community_table(metrics).to_csv(OUTPUT_DIR / "community_summary.csv", index=False)
    (OUTPUT_DIR / "graph_summary.json").write_text(json.dumps({"construction": info, "graph": summary}, indent=2), encoding="utf-8")
    nx.write_gexf(G, OUTPUT_DIR / "copurchase_network.gexf")


def main():
    plt.switch_backend("Agg")
    sales = load_sales()
    G, info = build_graph(sales)
    metrics, summary = add_metrics(G)
    export(G, metrics, summary, info)
    sensitivity_table(sales).to_csv(OUTPUT_DIR / "threshold_sensitivity.csv", index=False)
    invoice_definition_table(sales).to_csv(OUTPUT_DIR / "invoice_definition_sensitivity.csv", index=False)
    (OUTPUT_DIR / "invoice_profile.json").write_text(json.dumps(invoice_profile(sales), indent=2), encoding="utf-8")
    draw_network(G, metrics, OUTPUT_DIR / "copurchase_network.png")
    draw_property_model(OUTPUT_DIR / "property_graph_model.png")
    print(json.dumps({"construction": info, "graph": summary}, indent=2))
    print(metrics.sort_values("betweenness", ascending=False).head(10)[["product", "degree", "weighted_degree", "betweenness", "community"]].to_string())


if __name__ == "__main__":
    main()
