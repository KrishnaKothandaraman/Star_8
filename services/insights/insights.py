import time
from typing import Tuple, List, Dict
import json
import os
import sys
import argparse
import datetime
sys.path.append("")
from services.insights.api.rf import getRFOrdersBetweenDates
from services.insights.api.bm import getBMOrdersBetweenDates
from services.insights.insightjson import initInsights
from services.insights.utils.util import writeToCSV, returnRollingAverage

COLS = ["Model_SKU", "Product_name",
        "Total Sold", "BM - Total", "RF - Total",
        "Average Price of Model", "BM - Average Price of Model", "RF - Average Price of Model",
        "BM - Count SH", "BM - Average Price SH",
        "BM - Count SL", "BM - Average Price SL",
        "BM - Count BR", "BM - Average Price BR",
        "BM - Count BR2", "BM - Average Price BR2",
        "BM - Count SH2", "BM - Average Price SH2",
        "RF - Count SH", "RF - Average Price SH",
        "RF - Count SL", "RF - Average Price SL",
        "RF - Count BR", "RF - Average Price BR",
        "RF - Count BR2", "RF - Average Price BR2",
        "RF - Count SH2", "RF - Average Price SH2",
        ]
GRADINGS = ['SH', 'SL', "BR", "SH2", "BR2"]


def aggregateAndGetInsightsRF(orders: List[Dict], insights):
    for order in orders:
        for orderline in order["items"]:
            sku: str = orderline["sku"]
            name: str = orderline["name"]
            price: float = float(orderline["settlement_total_paid"])
            product: str = sku[:6]
            grading: str = sku[6:]

            # ignoring potential custom gradings
            if grading not in GRADINGS:
                print(f"RF: Ignoring grading {grading}")
                continue

            if product not in insights:
                insights[product] = initInsights()
                # global update
                insights[product]["name"] = name
                insights[product]["count"] = 1
                insights[product]["average_price"] = price

                # RF global update
                insights[product]["RF"]["count"] = 1
                insights[product]["RF"]["average_price"] = price

                # RF grading update
                insights[product]["RF"]["grading"][grading] = 1
                insights[product]["RF"]["pricing"][grading] = price

            else:
                # global update
                insights[product]["average_price"] = returnRollingAverage(insights[product]["average_price"],
                                                                          insights[product]["count"], price)
                insights[product]["count"] += 1

                # RF global update
                insights[product]["RF"]["average_price"] = returnRollingAverage(
                    insights[product]["RF"]["average_price"], insights[product]["RF"]["count"], price)
                insights[product]["RF"]["count"] += 1

                # RF grading update
                insights[product]["RF"]["pricing"][grading] = returnRollingAverage(
                    insights[product]["RF"]["pricing"][grading], insights[product]["RF"]["grading"][grading], price)
                insights[product]["RF"]["grading"][grading] += 1

    return insights


def aggregateAndGetInsightsBackMarket(orders: List[Dict]):
    insights = {}
    for order in orders:
        for orderline in order["orderlines"]:
            sku: str = orderline["listing"]
            name: str = orderline["product"]
            price: float = float(orderline["price"])
            product: str = sku[:6]
            grading: str = sku[6:]

            # ignoring potential custom gradings
            if grading not in GRADINGS:
                print(f"BM: Ignoring grading {grading}")
                continue

            if product not in insights:
                insights[product] = initInsights()
                # global update
                insights[product]["name"] = name
                insights[product]["count"] = 1
                insights[product]["average_price"] = price

                # BM global update
                insights[product]["BM"]["count"] = 1
                insights[product]["BM"]["average_price"] = price

                # BM grading update
                insights[product]["BM"]["grading"][grading] = 1
                insights[product]["BM"]["pricing"][grading] = price

            else:
                # global update
                insights[product]["average_price"] = returnRollingAverage(insights[product]["average_price"],
                                                                          insights[product]["count"], price)
                insights[product]["count"] += 1

                # BM global update
                insights[product]["BM"]["average_price"] = returnRollingAverage(
                    insights[product]["BM"]["average_price"], insights[product]["BM"]["count"], price)
                insights[product]["BM"]["count"] += 1

                # BM grading update
                insights[product]["BM"]["pricing"][grading] = returnRollingAverage(
                    insights[product]["BM"]["pricing"][grading], insights[product]["BM"]["grading"][grading], price)
                insights[product]["BM"]["grading"][grading] += 1

    return insights


def generateInsights(startDate, endDate):
    """Generates insights between startDate 00:00:00 and endDate 23:59:59"""
    startDateTime = startDate + " 00:00:00"
    endDateTime = endDate + " 23:59:59"

    startTimer = time.time()
    print(f"{'':->90}")
    os.makedirs(os.path.join(os.getcwd(), f"data/bm/orders/{startDate}"), exist_ok=True)
    with open(f"data/bm/orders/{startDate}/{startDate}.json", 'w') as f:
        f.write(json.dumps(getBMOrdersBetweenDates(startDateTime, endDateTime), indent=3))
    endTimer = time.time()
    total_time = endTimer - startTimer
    print(f"{f'BM Stats: It took {total_time} seconds': ^90}")

    startDateTime = startDate + "T00:00:00.00000Z"
    endDateTime = endDate + "T23:59:59.9999Z"
    startTimer = time.time()
    print(f"{'':->90}")
    os.makedirs(os.path.join(os.getcwd(), f"data/rf/orders/{startDate}"), exist_ok=True)
    with open(f"data/rf/orders/{startDate}/{startDate}.json", 'w') as f:
        # res, APICallCounter = asyncio.run(get_symbols())
        f.write(json.dumps(getRFOrdersBetweenDates(startDateTime, endDateTime), indent=3))
    endTimer = time.time()
    total_time = endTimer - startTimer
    print(f"{f'RF Stats: It took {total_time} seconds': ^90}")
    print(f"{'':->90}")

    print("Generating insights")
    with open(f"data/bm/orders/{startDate}/{startDate}.json", "r") as f1, open(f"data/rf/orders/{startDate}/{startDate}.json", "r") as f2:
        BMorders = json.load(f1)
        insights = aggregateAndGetInsightsBackMarket(BMorders)
        RFOrders = json.load(f2)
        insights = aggregateAndGetInsightsRF(RFOrders, insights)
    print("Insights generated")

    print("Writing insights")
    os.makedirs(os.path.join(os.getcwd(), f"data/insights/{startDate}"), exist_ok=True)
    with open(f"data/insights/{startDate}/{startDate}.json", "w") as f:
        f.write(json.dumps(insights, indent=3))

    insightList = [[f"'{sku}", insight["name"],
                    insight["count"], insight["BM"]["count"], insight["RF"]["count"],
                    round(insight["average_price"], 2), round(insight["BM"]["average_price"], 2),
                    round(insight["RF"]["average_price"], 2),
                    insight["BM"]["grading"]["SH"], round(insight["BM"]["pricing"]["SH"], 2),
                    insight["BM"]["grading"]["SL"], round(insight["BM"]["pricing"]["SL"], 2),
                    insight["BM"]["grading"]["BR"], round(insight["BM"]["pricing"]["BR"], 2),
                    insight["BM"]["grading"]["BR2"], round(insight["BM"]["pricing"]["BR2"], 2),
                    insight["BM"]["grading"]["SH2"], round(insight["BM"]["pricing"]["SH2"], 2),
                    insight["RF"]["grading"]["SH"], round(insight["RF"]["pricing"]["SH"], 2),
                    insight["RF"]["grading"]["SL"], round(insight["RF"]["pricing"]["SL"], 2),
                    insight["RF"]["grading"]["BR"], round(insight["RF"]["pricing"]["BR"], 2),
                    insight["RF"]["grading"]["BR2"], round(insight["RF"]["pricing"]["BR2"], 2),
                    insight["RF"]["grading"]["SH2"], round(insight["RF"]["pricing"]["SH2"], 2),
                    ] for (sku, insight) in insights.items()]

    with open(f"data/insights/{startDate}/{startDate}.csv", "w") as f:
        writeToCSV(COLS, insightList, f)
    print("Insights written")


if __name__ == "__main__":
    # To generate insights, simply run the command python3 insights.py -d <YYYY-MM-DD> to generate insights on all
    # sales after the date -d
    parser = argparse.ArgumentParser(description='Generate Insights for all sales after the specified date')
    parser.add_argument('-start', type=str, help="Start date: YYYY-MM-DD format", required=True)
    parser.add_argument('-end', type=str, help="End date: YYYY-MM-DD format. Default is today's date", default=datetime.datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()
    print("INFO: Started!")

    generateInsights(startDate=args.start, endDate=args.end)

