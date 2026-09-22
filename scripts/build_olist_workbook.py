from __future__ import annotations

import json
from pathlib import Path

from xninetzy.tools.ecosystem.tableau_tools import (
    tableau_dashboard_create,
    tableau_dashboard_layout,
    tableau_story_create,
    tableau_twbx_package,
    tableau_workbook_generate,
    tableau_workbook_validate,
)


CSV_PATH = "/home/misbahul45/Documents/Analisis-dan-Visualisasi-Data-Praktikum/datasets/olist-ecommerce/olist_merged.csv"

VISUALIZATIONS = [
    {"type": "kpi",    "name": "01_KPI_Orders",       "measure": "order_id",     "measure_aggregation": "CountDistinct"},
    {"type": "kpi",    "name": "02_KPI_Revenue",      "measure": "price",        "measure_aggregation": "Sum"},
    {"type": "kpi",    "name": "03_KPI_LateRate",     "measure": "is_late",      "measure_aggregation": "Avg"},
    {"type": "kpi",    "name": "04_KPI_Review",       "measure": "review_score", "measure_aggregation": "Avg"},
    {"type": "kpi",    "name": "05_KPI_AvgFreight",   "measure": "freight_value", "measure_aggregation": "Avg"},
    {"type": "kpi",    "name": "06_KPI_AvgDelivery",  "measure": "delivery_days", "measure_aggregation": "Avg"},
    {"type": "kpi",    "name": "07_KPI_CancelRate",   "measure": "is_canceled",  "measure_aggregation": "Avg"},
    {"type": "kpi",    "name": "08_KPI_RepeatRate",   "measure": "same_state",   "measure_aggregation": "Avg"},

    {"type": "map",    "name": "09_Map_Customer_State", "rows": ["customer_state"], "measure": "price",        "color": "price"},
    {"type": "map",    "name": "10_Map_Seller_State",   "rows": ["seller_state"],   "measure": "order_id",     "measure_aggregation": "CountDistinct", "color": "price"},

    {"type": "line",   "name": "11_Trend_Monthly",       "rows": ["purchase_yearmonth"], "measure": "price",        "measure_aggregation": "Sum", "trend_line": True},
    {"type": "area",   "name": "12_Trend_Daily",         "rows": ["purchase_date"],      "measure": "price",        "measure_aggregation": "Sum"},
    {"type": "line",   "name": "13_Trend_DOW_Hour",      "rows": ["purchase_hour"],      "cols": ["purchase_dow"], "measure": "order_id", "measure_aggregation": "CountDistinct"},
    {"type": "area",   "name": "14_Trend_Review_Monthly", "rows": ["purchase_yearmonth"], "measure": "review_score", "measure_aggregation": "Avg"},

    {"type": "bar",    "name": "15_Top_Categories",      "rows": ["product_category_en"], "measure": "price", "top_n": 15},
    {"type": "bar",    "name": "16_Payment_Types",       "rows": ["payment_types"],       "measure": "order_id", "measure_aggregation": "CountDistinct"},
    {"type": "pie",    "name": "17_Payment_Type_Share",  "rows": ["payment_types"],       "measure": "payment_total", "measure_aggregation": "Sum"},
    {"type": "bar",    "name": "18_Review_Distribution", "rows": ["review_score"],        "measure": "order_id", "measure_aggregation": "CountDistinct"},
    {"type": "bar",    "name": "19_Order_Status",        "rows": ["order_status"],        "measure": "order_id", "measure_aggregation": "CountDistinct"},

    {"type": "scatter", "name": "20_Price_vs_Freight",   "rows": ["price_log"],   "cols": ["freight_log"], "measure": "freight_value", "color": "is_late"},
    {"type": "scatter", "name": "21_Weight_vs_Price",    "rows": ["product_weight_g"], "cols": ["price"],  "measure": "price",        "color": "review_score"},
    {"type": "scatter", "name": "22_Delivery_vs_Freight", "rows": ["delivery_days"], "cols": ["freight_value"], "measure": "order_id", "measure_aggregation": "CountDistinct", "color": "is_late"},

    {"type": "heatmap", "name": "23_Heat_Late_State_Month", "rows": ["customer_state"], "cols": ["purchase_yearmonth"], "measure": "is_late",      "measure_aggregation": "Avg"},
    {"type": "heatmap", "name": "24_Heat_Review_State",     "rows": ["customer_state"], "cols": ["review_score"],        "measure": "review_score", "measure_aggregation": "Avg"},

    {"type": "circle",  "name": "25_Freight_Distance",     "rows": ["customer_state"], "measure": "freight_ratio", "color": "is_late", "size": "price"},

    {"type": "table",   "name": "26_Table_Top_Sellers",    "rows": ["seller_state", "product_category_en"], "measure": "price", "measure_aggregation": "Sum"},
]

DASHBOARD_ZONES = [
    {"name": "01_KPI_Orders",       "x": 0,   "y": 0,   "w": 1, "h": 1},
    {"name": "02_KPI_Revenue",      "x": 1,   "y": 0,   "w": 1, "h": 1},
    {"name": "03_KPI_LateRate",     "x": 2,   "y": 0,   "w": 1, "h": 1},
    {"name": "04_KPI_Review",       "x": 3,   "y": 0,   "w": 1, "h": 1},
    {"name": "05_KPI_AvgFreight",   "x": 4,   "y": 0,   "w": 1, "h": 1},
    {"name": "06_KPI_AvgDelivery",  "x": 5,   "y": 0,   "w": 1, "h": 1},
    {"name": "07_KPI_CancelRate",   "x": 6,   "y": 0,   "w": 1, "h": 1},
    {"name": "08_KPI_RepeatRate",   "x": 7,   "y": 0,   "w": 1, "h": 1},
    {"name": "09_Map_Customer_State","x": 0,  "y": 1,   "w": 4, "h": 4},
    {"name": "10_Map_Seller_State",  "x": 4,  "y": 1,   "w": 4, "h": 4},
    {"name": "11_Trend_Monthly",     "x": 0,  "y": 5,   "w": 4, "h": 3},
    {"name": "12_Trend_Daily",       "x": 4,  "y": 5,   "w": 4, "h": 3},
    {"name": "13_Trend_DOW_Hour",    "x": 0,  "y": 8,   "w": 4, "h": 3},
    {"name": "14_Trend_Review_Monthly","x": 4,"y": 8,   "w": 4, "h": 3},
    {"name": "15_Top_Categories",    "x": 0,  "y": 11,  "w": 4, "h": 4},
    {"name": "16_Payment_Types",     "x": 4,  "y": 11,  "w": 2, "h": 4},
    {"name": "17_Payment_Type_Share","x": 6,  "y": 11,  "w": 2, "h": 4},
    {"name": "18_Review_Distribution","x": 0, "y": 15,  "w": 2, "h": 3},
    {"name": "19_Order_Status",      "x": 2,  "y": 15,  "w": 2, "h": 3},
    {"name": "20_Price_vs_Freight",  "x": 4,  "y": 15,  "w": 4, "h": 3},
    {"name": "21_Weight_vs_Price",   "x": 0,  "y": 18,  "w": 4, "h": 3},
    {"name": "22_Delivery_vs_Freight","x": 4, "y": 18,  "w": 4, "h": 3},
    {"name": "23_Heat_Late_State_Month","x": 0,"y": 21,"w": 4, "h": 4},
    {"name": "24_Heat_Review_State", "x": 4,  "y": 21,  "w": 4, "h": 4},
    {"name": "25_Freight_Distance",  "x": 0,  "y": 25,  "w": 4, "h": 3},
    {"name": "26_Table_Top_Sellers", "x": 4,  "y": 25,  "w": 4, "h": 3},
]

STORY_POINTS = [
    "Brazilian e-commerce grew 3x in 2 years; revenue peaked late 2017 then dropped sharply",
    "North/Northeast states (MA, PB, AL, SE, RN) show 18-25% late delivery vs <8% in SP",
    "Credit card dominates 73% of payments; boleto covers another 19%; minority methods negligible",
    "Top 15 categories capture ~60% of revenue, led by health_beauty, watches_gifts, bed_bath_table",
    "Freight ratio rises linearly with delivery distance; intra-state orders ship ~30% cheaper",
    "Review scores cluster at 4-5 stars, but 1-star orders correlate with long delivery_days",
    "Action: prioritize SP/RJ sellers serving north region; renegotiate freight contracts with MA/PB carriers",
    "Cancellation rate ~0.6%; canceled orders skew toward specific product categories worth investigating",
    "Weight-vs-price scatter reveals logistics outliers: heavy low-value items dominate freight cost",
    "Hour-of-day heat: most orders placed 19-22h weekdays; weekend dip confirms B2C evening pattern",
]

DASHBOARD_NAME = "Olist E-Commerce Dashboard"


def main() -> None:
    print("[1/6] Generating workbook...")
    result = tableau_workbook_generate.invoke(
        {
            "csv_paths": [CSV_PATH],
            "name": "olist_avd_praktikum",
            "dashboard_title": DASHBOARD_NAME,
            "story_points": STORY_POINTS,
            "visualizations": VISUALIZATIONS,
        }
    )
    workbook_path = result["path"]
    print(f"      wrote {result['bytes']} bytes -> {workbook_path}")
    print(f"      worksheets: {result['worksheets']}")
    print(f"      datasources: {result['datasources']}")

    print("[2/6] Building dashboard...")
    dashboard = tableau_dashboard_create.invoke(
        {
            "workbook_path": workbook_path,
            "dashboard_name": DASHBOARD_NAME,
            "worksheets": [v["name"] for v in VISUALIZATIONS],
        }
    )
    print(f"      dashboards: {dashboard.get('dashboards')}")

    print("[3/6] Applying 8-column dashboard layout...")
    layout = tableau_dashboard_layout.invoke(
        {
            "workbook_path": workbook_path,
            "dashboard_name": DASHBOARD_NAME,
            "layout": [{"worksheet": z["name"], "x": z["x"], "y": z["y"], "w": z["w"], "h": z["h"]} for z in DASHBOARD_ZONES],
        }
    )
    print(f"      layout: {layout.get('zones')}")

    print("[4/6] Anchoring story points...")
    story = tableau_story_create.invoke(
        {
            "workbook_path": workbook_path,
            "story_name": "Olist Story",
            "points": STORY_POINTS,
        }
    )
    print(f"      story_points: {story.get('story_points')}")

    print("[5/6] Validating...")
    report = tableau_workbook_validate.invoke({"workbook_path": workbook_path})
    print(f"      valid: {report.get('valid')}")
    print(f"      checks: {json.dumps(report.get('checks'), indent=2)}")
    if report.get("errors"):
        print(f"      ERRORS: {report['errors']}")

    print("[6/6] Packaging .twbx...")
    twbx = tableau_twbx_package.invoke(
        {
            "workbook_path": workbook_path,
            "resources": [CSV_PATH],
        }
    )
    print(f"      package: {twbx['package_path']}")
    print(f"      entries: {twbx['entries']}")


if __name__ == "__main__":
    main()
