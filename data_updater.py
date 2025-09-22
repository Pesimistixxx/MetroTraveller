import requests


line_translator = {1: '1',
                   2: '2',
                   3: '3',
                   4: '4',
                   5: '6',
                   6: '5',
                   7: '9',
                   8: '7',
                   9: '8',
                   10: '10',
                   11: '11',
                   12: '12',
                   13: '8A',
                   14: 'D1',
                   15: 'D2',
                   16: '14',
                   17: '15',
                   36: 'D3',
                   37: 'D4',
                   38: 'D4a',
                   75: '16'}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Content-Type': 'application/json',
    'Origin': 'https://mosmetro.ru',
    'Referer': 'https://mosmetro.ru/',
}

response = requests.get("https://prodapp.mosmetro.ru/api/schema/v1.0",
                        headers=headers)

response_json = response.json()
connections_data = response_json['data']['connections']
transitions_data = response_json['data']['transitions']
stations_data = response_json['data']['stations']


with open('transitions_data.txt', 'w') as file:
    for transition in transitions_data:
        file.write(f"{transition['stationFromId']} {transition['stationToId']} {transition['pathLength']}\n")

    for connection in connections_data:
        file.write(f"{connection['stationFromId']} {connection['stationToId']} {connection['pathLength']}\n")


with open('stations_data.txt', 'w') as file:
    for station in stations_data:
        station_str = f'{station['id']} {station['name']['ru'].replace(' ', '_')}_{line_translator[station['lineId']]}\n'
        file.write(station_str)
    with open('stations_d5.txt') as f:
        for line in f.readlines():
            print(f'"{line.split()[1]}": {line.split()[0]},', end=' ')
            file.write(line)
