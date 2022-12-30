import time
from typing import Tuple, List, Dict
import json
import os
import sys
sys.path.append("")
from services.insights.api.rf import getRFOrdersAfterDate
from services.insights.api.bm import getBMOrdersAfterDate
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


def aggregateAndGetInsightsRF(orders: List[Dict], insights):
    for order in orders:
        for orderline in order["items"]:
            sku: str = orderline["sku"]
            name: str = orderline["name"]
            price: float = float(orderline["total_charged"])
            product: str = sku[:6]
            grading: str = sku[6:]

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


if __name__ == "__main__":
    print("INFO: Started!")

    date = "2022-12-29"


    datetime = date + " 00:00:00"
    start = time.time()
    print(f"{'':->90}")
    os.makedirs(os.path.join(os.getcwd(), f"data/bm/orders/{date}"), exist_ok=True)
    with open(f"data/bm/orders/{date}/{date}.json", 'w') as f:
        # res, APICallCounter = asyncio.run(get_symbols())
        f.write(json.dumps(getBMOrdersAfterDate(datetime), indent=3))
    end = time.time()
    total_time = end - start
    print(
        f"{f'BM Stats: It took {total_time} seconds': ^90}")

    datetime = "2022-12-29T00:00:00.00000Z"
    start = time.time()
    print(f"{'':->90}")
    os.makedirs(os.path.join(os.getcwd(), f"data/rf/orders/{date}"), exist_ok=True)
    with open(f"data/rf/orders/{date}/{date}.json", 'w') as f:
        # res, APICallCounter = asyncio.run(get_symbols())
        f.write(json.dumps(getRFOrdersAfterDate(datetime), indent=3))
    end = time.time()
    total_time = end - start
    print(
        f"{f'RF Stats: It took {total_time} seconds': ^90}")
    print(f"{'':->90}")

    print("Generating insights")
    with open(f"data/bm/orders/{date}/{date}.json", "r") as f1, open(f"data/rf/orders/{date}/{date}.json", "r") as f2:
        BMorders = json.load(f1)
        insights = aggregateAndGetInsightsBackMarket(BMorders)
        RFOrders = json.load(f2)
        insights = aggregateAndGetInsightsRF(RFOrders, insights)
    print("Insights generated")

    print("Writing insights")
    os.makedirs(os.path.join(os.getcwd(), f"data/bm/insights/{date}"), exist_ok=True)
    with open(f"data/bm/insights/{date}/{date}.json", "w") as f:
        f.write(json.dumps(insights, indent=3))

    # COLS = ["Model_SKU", "Product_name",
    #         "Total Sold", "BM - Total", "RF - Total",
    #         "Average Price of Model", "BM - Average Price of Model", "RF - Average Price of Model",
    #         "BM - Count SH", "BM - Average Price SH",
    #         "BM - Count SL", "BM - Average Price SL",
    #         "BM - Count BR", "BM - Average Price BR",
    #         "BM - Count BR2", "BM - Average Price BR2",
    #         "BM - Count SH2", "BM - Average Price SH2",
    #         "RF - Count SH", "RF - Average Price SH",
    #         "RF - Count SL", "RF - Average Price SL",
    #         "RF - Count BR", "RF - Average Price BR",
    #         "RF - Count BR2", "RF - Average Price BR2",
    #         "RF - Count SH2", "RF - Average Price SH2",
    #         ]
    insightList = [[f"'{sku}", insight["name"],
                    insight["count"], insight["BM"]["count"], insight["RF"]["count"],
                    insight["average_price"], insight["BM"]["average_price"], insight["RF"]["average_price"],
                    insight["BM"]["grading"]["SH"], insight["BM"]["pricing"]["SH"],
                    insight["BM"]["grading"]["SL"], insight["BM"]["pricing"]["SL"],
                    insight["BM"]["grading"]["BR"], insight["BM"]["pricing"]["BR"],
                    insight["BM"]["grading"]["BR2"], insight["BM"]["pricing"]["BR2"],
                    insight["BM"]["grading"]["SH2"], insight["BM"]["pricing"]["SH2"],
                    insight["RF"]["grading"]["SH"], insight["RF"]["pricing"]["SH"],
                    insight["RF"]["grading"]["SL"], insight["RF"]["pricing"]["SL"],
                    insight["RF"]["grading"]["BR"], insight["RF"]["pricing"]["BR"],
                    insight["RF"]["grading"]["BR2"], insight["RF"]["pricing"]["BR2"],
                    insight["RF"]["grading"]["SH2"], insight["RF"]["pricing"]["SH2"],
                    ] for (sku, insight) in insights.items()]
    with open(f"data/bm/insights/{date}/{date}.csv", "w") as f:
        writeToCSV(COLS, insightList, f)
    print("Insights written")

    # print("------------------------------------------------------------------------")
    # start = time.time()
    # with open("data/swd.json", "w") as f:
    #     f.write(json.dumps(InfoSource.mapEnumToGetParams()[InfoSource.SWD](), indent=3))
    # end = time.time()
    # total_time = end - start
    # print("------------SWD Stats: It took {} seconds to make {} API calls------------".format(total_time, len(symbols)))
