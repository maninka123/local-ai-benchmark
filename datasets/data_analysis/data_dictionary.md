# Aurora Instruments: data dictionary

Fictional operational data, 2024–2025. Monetary amounts are AUD.

transactions: transaction_id (business key); customer_id/products/region foreign keys; transaction_date ISO date; quantity units; selling_price AUD/unit before discount; discount fraction; unit_cost AUD/unit; revenue AUD = quantity × selling_price × (1−discount); delivery_days; supplier_id; service_class; on_time 0/1; ad_index arbitrary advertising index.

products: product_id, name, category, standard unit_cost, list_price. customers: customer_id, segment, home region, joined_date, arbitrary marketing_group. regions: region_id/name, timezone, shipping_distance_km. inventory: monthly product stock_units and stockouts. operational_events: dated business events.

Rows represent completed sales, not returns; sales quantity must be positive. You decide and disclose cleaning rules. Financial margin = (revenue − quantity × unit_cost)/revenue. Distinguish genuine large orders from errors; do not infer causation from association.
