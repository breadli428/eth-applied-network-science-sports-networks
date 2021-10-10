import requests
import bs4
import re
import json


url_base = "https://www.transfermarkt.com"


def open_url(url):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36"}
    res = requests.get(url, headers=headers)
    return res


def find_club_name(res):
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    target = soup.find(class_="row", id="verein_head")
    if target:
        name = target.h1.text.strip()
    else:
        name = 'NaN'
    return name


def find_data_club(res):
    name = find_club_name(res)
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    target = soup.find(class_="row", id="verein_head")
    data = target.find_all('p')
    data_club = {'Name': name}
    for each in data:
        item = each.find("span", class_="dataItem")
        if item:
            item = item.text.strip().replace(':', '')
            value = each.find("span", class_="dataValue").text.strip()
            if item == "Foreigners":
                value = value.replace('\xa0\xa0', ', ')
            elif item == "Stadium":
                value = value.replace('\xa0\xa0', ' ')
            data_club[item] = value
    market_value = re.search(r'-?\d+.?\d*', target.find(class_="dataMarktwert").text.strip()).group()
    data_club['Market value'] = market_value
    return data_club


def parse_tables(tables):
    """compute the list of two dictionaries corresponding to the in-table and the out-table respectively"""
    loan_data = []
    for table in tables:
        thead = table.thead
        header = thead.text.strip().split('\n')
        header.remove('Pos')
        header.insert(6, "Club ID")
        loan_dict = {} # dictionary collection loan records for a table
        for i in range(len(header)):
            # initialize dictionary
            loan_dict[header[i]] = []
        tbody = table.tbody
        rows = tbody.find_all('tr') # all rows corresponding to a table
        for row in rows:
            record = row.find_all('td')
            if len(record) < 9:
                continue
            name = record[0].div.span.a.text.strip()
            age = record[1].text.strip()
            nat = record[2].img['title'].strip()
            position = record[3].text.strip()
            market_value = record[5].text.strip()
            club_id = record[7].a['id']
            club_url = record[7].a['href']
            club_url = requests.compat.urljoin(url_base, club_url)
            club_res = open_url(club_url)
            club_name = find_club_name(club_res)
            fee = record[8].text.strip()
            row_data = [name, age, nat, position, market_value, club_name, club_id, fee]
            for i, key in enumerate(loan_dict.keys()):
                loan_dict[key].append(row_data[i])
        loan_data.append(loan_dict)

    return loan_data


def find_data_loan(res):
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    target = soup.find_all(class_="table-header", id=re.compile("^to-"))
    data_loan = {} # key = club_name
    for each in target:
        # each club
        club_url = each.h2.a['href']
        club_url = requests.compat.urljoin(url_base, club_url)
        club_res = open_url(club_url)
        club_data = {'Club ID': each.h2.a['id']}
        data_club = find_data_club(club_res) # find information of the club
        club_data.update(data_club)
        club_name = club_data['Name']
        print("Collecting data for", club_name)
        tables = each.parent.find_all('table') # each club has an in-table and an out-table
        loan_data = parse_tables(tables) # list of two dictionaries corresponding to the in-table and the out-table respectively
        data_loan[club_name] = {'club_info': club_data, 'loan_record': loan_data} # each value is a dictionary conataining club_info and loan_data
        print("Successful!")
    return data_loan


def change_to_million(value):
    """change the unit of value to million (m) if represented in thousand (Th.)"""
    searched = re.search(r'(-?\d+\.?\d*)([a-zA-Z]*)', value)
    if searched.group(2) == 'Th':
        value = str(float(searched.group(1)) / 1e3)
    else:
        value = searched.group(1)


def write_json(league, collection):
    filename = './json/' + league + '.json'
    with open(filename, 'w') as file:
        json.dump(collection, file)


def main():
    leagues = {'Bundesliga': ['bundesliga', 'L1'], 'Premier League': ['premier_league', 'GB1'], 'La Liga': ['laliga', 'ES1'], 'Serie A': ['serie-a', 'IT1'], 'Ligue 1': ['ligue-1', 'FR1']}
    seasons = list(range(2010, 2021))
    for league, keyword in leagues.items():
        collection = {}
        # dictionary with seasons as keys and sub-dictionaries as values
        # the sub-dictionaries have club names as keys and sub-sub-dictionaries as values
        # the sub-sub-dictionaries have a key "club_info" and its corresponding value is a dictionary containing all club information
        # the sub-sub-dictionaries have another key "loan_record" and its corresponding value is a list with two dictionary components
        # corresponding to in and out loan records
        for season in seasons:
            print("Starting", league, "in season", season, "/", season + 1)
            url = "https://www.transfermarkt.com/" + keyword[0] + "/transfers/wettbewerb/" + keyword[1] + "/plus/?saison_id=" + str(season) + "&s_w=&leihe=2&intern=0&intern=1"
            res = open_url(url)
            data_loan = find_data_loan(res)
            collection[season] = data_loan
            print("Data of", league, "in season", season, "/", season + 1, "collected")
        write_json(league, collection)


if __name__ == '__main__':
    main()
