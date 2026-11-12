# Persistent Identifiers – Online Retail

## Existing identifiers

| Item | Existing PID | Status |
|---|---|---|
| Dataset | DOI 10.24432/C5BW33 (https://doi.org/10.24432/C5BW33) | Exists and resolves (F-UJI detailedview3) |
| Related paper | DOI 10.1057/dbm.2012.17 (https://doi.org/10.1057/dbm.2012.17) | Exists, named by UCI, but not linked in the DOI metadata (gap 6) |
| Organisation: London South Bank University | ROR https://ror.org/02vwnat91 | Exists in the ROR registry (checked 2026-11-08), but not used in the DOI metadata |
| Creator: Daqing Chen | none in the metadata, which says "Unknown" | Propose an ORCID iD, to be supplied or confirmed by the creator |
| Data file | none: the F-UJI data identifier tests fail | Propose a stable URL or PID for the file (gap 3) |
| Variables | none – plain-text descriptions only | Propose the terms below |

## Proposed identifiers for the variables

| Variable | Proposed term URI | Extra standard |
|---|---|---|
| InvoiceNo | https://schema.org/orderNumber | – |
| StockCode | https://schema.org/sku | – |
| Description | https://schema.org/description | – |
| Quantity | https://schema.org/orderQuantity | – |
| InvoiceDate | https://schema.org/orderDate | ISO 8601 date-time |
| UnitPrice | https://schema.org/price | currency ISO 4217 GBP (https://schema.org/priceCurrency) |
| CustomerID | https://schema.org/customer | Pseudonymous; no external PID should be attached |
| Country | https://schema.org/addressCountry | ISO 3166-1 alpha-2 (e.g. GB), implemented as `CountryISO2` in the cleaned data |

## Proposal for the cleaned dataset

The cleaned file is a new, derived dataset. If it were published, it should receive its own DOI (for example through Zenodo), linked to the source with DataCite relation `IsDerivedFrom` 10.24432/C5BW33, under CC BY 4.0 with attribution. No DOI has been minted.
