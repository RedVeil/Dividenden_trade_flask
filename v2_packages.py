from operator import itemgetter

def create_packages(ranking):
    # 0 start_date, 1 end_date, 2 points, 3 id, 4 name
    counter = 0
    packages = []
    repetition = 30
    if repetition > len(ranking):
        repetition = len(ranking)
    while counter < repetition:
        package = [ranking[counter]]
        points = package[0]["points"]
        for i in ranking:
            if i["buy_date"] < package[-1]["sell_date"] and i["buy_date"] >= package[-1]["buy_date"]:
                pass
            if i["sell_date"] > package[-1]["buy_date"] and i["sell_date"] <= package[-1]["sell_date"]:
                pass
            if i["buy_date"] >= package[-1]["sell_date"]:
                package.append(i)
                points += i["points"]
            if i["sell_date"] <= package[0]["buy_date"]:
                package.insert(0, i)
                points += i["points"]
        packages.append({"points":points,"package":package})
        counter +=1
    return packages


def get_companies(companies, year, last_date="0"):
    to_sort = []
    for key in companies.keys():
        if companies[key].trades[year].buy_date > last_date:
            to_sort.append({"buy_date":companies[key].trades[year].buy_date,"sell_date":companies[key].trades[year].sell_date, "points":companies[key].ranking_points[year-1], "trade":companies[key].trades[year], "name":companies[key].name, "ticker":companies[key].ticker, "dividend_amount":companies[key].dividends[year]["amount"]})
    ranking = sorted(to_sort, key=itemgetter("buy_date"))
    packages = create_packages(ranking)
    packages_sorted = sorted(packages, key=itemgetter("points"), reverse=True)
    best_package = packages_sorted[0]["package"]
    return best_package

def get_forecasting_companies(companies, year, start_date):
    to_sort = []
    for key in companies.keys():
        if companies[key].buy_date > start_date:
            to_sort.append({"buy_date":companies[key].buy_date, "sell_date":companies[key].start_date, "points":companies[key].ranking_points[year-1],"name":companies[key].name, "ticker":companies[key].ticker})
    ranking = sorted(to_sort, key=itemgetter("buy_date"))
    packages = create_packages(ranking)
    packages_sorted = sorted(packages, key=itemgetter("points"), reverse=True)
    best_package = packages_sorted[0]["package"]
    return best_package