import csv
from typing import TextIO


def writeToCSV(cols, data, fileObj: TextIO):
    print("Started Writing to CSV")

    writer = csv.writer(fileObj)
    writer.writerow(cols)
    writer.writerows(data)

    print("Written to CSV!")


def returnRollingAverage(oldAverage, oldCount, newPrice):
    return (oldAverage * oldCount + newPrice) / (oldCount + 1)

