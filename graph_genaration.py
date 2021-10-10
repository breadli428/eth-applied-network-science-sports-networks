import json
import pandas as pd
import networkx as nx


leagues = ['Bundesliga', 'Premier League', 'La Liga', 'Serie A', 'Ligue 1']
seasons = list(range(2018, 2021))

def load_data(league):
    filename = './json/' + league + '.json'
    with open(filename, 'r') as file:
        collection = json.load(file)
    return collection


def get_relevant_clubs(season):
    relevant_clubs = []
    for league in leagues:
        collection = load_data(league)
        league_clubs = list(collection[str(season)].keys())
        relevant_clubs.extend(league_clubs)
    return relevant_clubs


transfer_collection = []
for season in seasons:
    relevant_clubs = get_relevant_clubs(season)
    for league in leagues:
        collection = load_data(league)
        data_loan = collection[str(season)]
        for key, value in data_loan.items():
            loan_record = value['loan_record']
            for table in loan_record:
                header = list(table.keys())
                flag = header[0]
                if flag == 'In':
                    for club, fee in zip(table['Left'], table['Fee']):
                        if 'End' not in fee and club not in relevant_clubs:
                            transfer = [club, key]
                            transfer_collection.append(transfer)
                else:
                    for club, fee in zip(table['Joined'], table['Fee']):
                        if 'End' not in fee:
                            transfer = [key, club]
                            transfer_collection.append(transfer)
df = pd.DataFrame(transfer_collection, columns=['From', 'To'])
df['weight'] = df.groupby(['From', 'To'])['From'].transform('size')
df = df.drop_duplicates(ignore_index=True)
print(df)

graph_path = './graphs/' + 'from_' + str(seasons[0]) + '_to_' + str(seasons[-1]) + '.gexf' 
G = nx.from_pandas_edgelist(df, 'From', 'To', create_using=nx.DiGraph(), edge_attr=True)
nx.write_gexf(G, graph_path)