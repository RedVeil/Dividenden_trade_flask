from datetime import date


def package_loop(ranking, counter, last_date=None):
    # 0 start_date, 1 end_date, 2 points, 3 id, 4 name
    if last_date != None:
        for x in range(len(ranking)):
            if x >= counter:
                if ranking[x][0] >= last_date:
                    package = [ranking[x]]
                    break
        points = package[0][2]
        for i in ranking:
            if i[0] < package[-1][1] and i[0] >= package[-1][0] or i[1] > package[-1][0] and i[1] <= package[-1][1]:
                pass
            else:
                if i[0] >= package[-1][1]:
                    package.append(i)
                    points += i[2]
                if i[1] <= package[0][0] and i[0] >= last_date:
                    package.insert(0, i)
                    points += i[2]
    else:
        package = [ranking[counter]]
        points = package[0][2]
        for i in ranking:
            if i[0] < package[-1][1] and i[0] >= package[-1][0] or i[1] > package[-1][0] and i[1] <= package[-1][1]:
                pass
            else:
                if i[0] >= package[-1][1]:
                    package.append(i)
                    points += i[2]
                if i[1] <= package[0][0]:
                    package.insert(0, i)
                    points += i[2]
    return package, points


def sort_ranking(ranking, timeframe, last_date):
    ranking.sort()
    packages = {}
    counter = 0
    while counter < 30:  # 10 or more (amount of packages)
        package, points = package_loop(ranking, counter, last_date)
        packages[counter] = [points, package]
        counter += 1
    to_sort = []
    for key in packages.keys():
        to_sort.append((packages[key][0], key))
    to_sort.sort()
    to_sort.reverse()
    best_package = packages[to_sort[0][1]]
    return best_package


def expert_get_firms_from_db(companies_last_year, companies, timeframe, year, amount_high, amount_medium, amount_low, tax_credit_high, tax_credit_low, last_date=None):
    ranking = []
    for key in companies_last_year.keys():
        if key in companies.keys():
            ranking.append([companies[key].start_date, companies[key].end_date,
                            companies_last_year[key].points, companies_last_year[key].id, companies_last_year[key].name])
    package = sort_ranking(ranking, timeframe, last_date)
