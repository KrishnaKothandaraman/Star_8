import csv
import os
from typing import TextIO


def writeToCSV(cols, data, fileObj: TextIO):
    print("Started Writing to CSV")

    writer = csv.writer(fileObj)
    writer.writerow(cols)
    writer.writerows(data)
    print("Written to CSV!")


def returnRollingAverage(oldAverage, oldCount, newPrice):
    return (oldAverage * oldCount + newPrice) / (oldCount + 1)


def makeDirAndWriteToFile(dirPath: str, filePath: str, data):
    print(dirPath)
    os.makedirs(dirPath, exist_ok=True)
    with open(filePath, 'w') as f:
        import json
        f.write(json.dumps(data, indent=3))
