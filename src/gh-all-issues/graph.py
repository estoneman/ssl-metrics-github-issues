from argparse import ArgumentParser, Namespace
from datetime import datetime
from json import load
from os.path import exists
from typing import Any, KeysView

import matplotlib.pyplot as plt
from dateutil.parser import parse
from intervaltree import IntervalTree
from matplotlib.figure import Figure
from progress.bar import PixelBar


def get_argparse() -> Namespace:
    parser: ArgumentParser = ArgumentParser(
        prog="Graph GitHub Issues",
        usage="This program outputs a series of graphs based on GitHub issue data.",
    )

    parser.add_argument(
        "-i",
        "--input",
        help="The input JSON file that is to be used for graphing",
        type=str,
        required=True,
    )

    return parser.parse_args()


def loadJSON(filename: str = "issues.json") -> list:
    with open(file=filename, mode="r") as jsonFile:
        return load(jsonFile)


def createIntervalTree(data: list, filename: str = "issues.json") -> IntervalTree:
    tree: IntervalTree = IntervalTree()
    day0: datetime = parse(data[0]["created_at"]).replace(tzinfo=None)

    with PixelBar(f"Creating interval tree from {filename}... ", max=len(data)) as pb:
        for issue in data:
            createdDate: datetime = parse(issue["created_at"]).replace(tzinfo=None)

            if issue["state"] == "closed":
                closedDate: datetime = parse(issue["closed_at"]).replace(tzinfo=None)
            else:
                closedDate: datetime = datetime.now(tz=None)

            begin: int = (createdDate - day0).days
            end: int = (closedDate - day0).days

            try:
                issue["endDayOffset"] = 0
                tree.addi(begin=begin, end=end, data=issue)
            except ValueError:
                issue["endDayOffset"] = 1
                tree.addi(begin=begin, end=end + 1, data=issue)

            pb.next()

    return tree


def plot_OpenIssuesPerDay_Line(
    pregeneratedData: dict = None,
    filename: str = "open_issues_per_day_line.png",
):
    figure: Figure = plt.figure()

    plt.title("Number of Open Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    data: dict = pregeneratedData

    plt.plot(data.keys(), data.values())
    figure.savefig(filename)

    return exists(filename)


def plot_ClosedIssuesPerDay_Line(
    pregeneratedData: dict = None,
    filename: str = "closed_issues_per_day_line.png",
):
    figure: Figure = plt.figure()

    plt.title("Number of Closed Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    data: dict = pregeneratedData

    plt.plot(data.keys(), data.values())
    figure.savefig(filename)

    return exists(filename)


def plot_OpenClosedIssuesPerDay_Line(
    pregeneratedData_OpenIssues: dict = None,
    pregeneratedData_ClosedIssues: dict = None,
    filename: str = "open_closed_issues_per_day_line.png",
):
    figure: Figure = plt.figure()

    plt.title("Number of Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    openData: dict = pregeneratedData_OpenIssues
    closedData: dict = pregeneratedData_ClosedIssues

    plt.plot(openData.keys(), openData.values(), color="blue", label="Open Issues")
    plt.plot(closedData.keys(), closedData.values(), color="red", label="Closed Issues")
    plt.legend()

    figure.savefig(filename)

    return exists(filename)


def fillDictBasedOnKeyValue(
    dictionary: dict, tree: IntervalTree, key: str, value: Any
) -> dict:
    data: dict = {}
    keys: KeysView = dictionary.keys()

    maxKeyValue: int = max(keys)
    minKeyValue: int = min(keys)

    with PixelBar(
        f'Getting the total number of "{key} = {value}" issues per day... ',
        max=maxKeyValue,
    ) as pb:
        for x in range(minKeyValue, maxKeyValue):
            try:
                data[x] = dictionary[x]
            except KeyError:
                count = 0
                interval: IntervalTree
                for interval in tree.at(x):
                    if interval.data[key] == value:
                        count += 1
                data[x] = count

            pb.next()

    return data


if __name__ == "__main__":

    args = get_argparse()

    jsonData: list = loadJSON(filename=args.input)

    tree: IntervalTree = createIntervalTree(data=jsonData, filename=args.input)

    startDay: int = tree.begin()
    endDay: int = tree.end()

    if len(tree.at(endDay)) == 0:
        endDay -= 1

    baseDict: dict = {startDay: len(tree.at(startDay)), endDay: len(tree.at(endDay))}

    openIssues: dict = fillDictBasedOnKeyValue(
        dictionary=baseDict, tree=tree, key="state", value="open"
    )

    closedIssues: dict = fillDictBasedOnKeyValue(
        dictionary=baseDict, tree=tree, key="state", value="closed"
    )

    plot_OpenIssuesPerDay_Line(pregeneratedData=openIssues)
    plot_ClosedIssuesPerDay_Line(pregeneratedData=closedIssues)
    plot_OpenClosedIssuesPerDay_Line(
        pregeneratedData_ClosedIssues=closedIssues,
        pregeneratedData_OpenIssues=openIssues,
    )