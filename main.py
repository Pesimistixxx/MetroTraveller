import os

import telebot
from telebot import TeleBot, StateMemoryStorage, types
from dotenv import load_dotenv
from telebot.custom_filters import StateFilter
from telebot.states import StatesGroup, State
from telebot.types import BotCommandScopeChat

from root_handler import dijkstra
from input_handler import find_closest_matches

load_dotenv()


class UserStates(StatesGroup):
    waiting_stations = State()
    final = State()


commands = [
    telebot.types.BotCommand("/start", "Запустить бота"),
    telebot.types.BotCommand("/info", "Информация о боте")
]

id_to_stations_dict = {}
stations_to_id_dict = {}

BOT_TOKEN = os.getenv('BOT_TOKEN')
edges_data = []
stations_data = []
graph = {i: [] for i in range(1000)}

state_storage = StateMemoryStorage()
bot = TeleBot(token=BOT_TOKEN, state_storage=state_storage)
bot.add_custom_filter(StateFilter(bot))

with open('transitions_data.txt', 'r') as f:
    for line in f.readlines():
        edges_data.append(list(map(int, line.strip().split(' '))))

with open('stations_data.txt', 'r') as f:
    for line in f.readlines():
        stations_data.append(line.strip())
        stations_to_id_dict[line.split()[1]] = int(line.split()[0])
        id_to_stations_dict[int(line.split()[0])] = line.split()[1]

for edge in edges_data:
    graph[edge[0]].append((edge[1], edge[2]))
    graph[edge[1]].append((edge[0], edge[2]))


def create_stop_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton('Стоп'))
    return markup


def format_time(minutes, declension=1):
    hours = minutes // 60
    mins = minutes % 60

    def format_units(value, forms_1, forms_2=None):
        if forms_2 is None:
            forms_2 = forms_1

        if declension == 1:
            forms = forms_1
        else:
            forms = forms_2

        if value % 10 == 1 and value % 100 != 11:
            return f"{value} {forms[0]}"
        elif 2 <= value % 10 <= 4 and not (12 <= value % 100 <= 14):
            return f"{value} {forms[1]}"
        else:
            return f"{value} {forms[2]}"

    hours_forms_1 = ["час", "часа", "часов"]
    mins_forms_1 = ["минута", "минуты", "минут"]

    hours_forms_2 = ["час", "часа", "часов"]
    mins_forms_2 = ["минуту", "минуты", "минут"]

    hours_str = format_units(hours, hours_forms_1, hours_forms_2) if hours > 0 else ""
    mins_str = format_units(mins, mins_forms_1, mins_forms_2) if mins > 0 else ""

    if hours_str and mins_str:
        return f"{hours_str} {mins_str}"
    return hours_str or mins_str or "0 минут"


def create_station_keyboard(stations):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    for station in stations:
        markup.add(types.KeyboardButton(station))
    return markup


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.from_user.id,
                     text="Бот, строящий оптимальный маршрут в Московском Метро с возможность прокладывать маршрут до 10 точек одновременно пиши /start и попробуй сам",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id,
                     text='Привет, выбери начальную станцию, после ввода станций напиши "Стоп"',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.set_state(message.from_user.id, UserStates.waiting_stations, message.chat.id)
    bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeChat(message.from_user.id)
    )
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['stations_id'] = []
        data['stations'] = []


@bot.message_handler(func=lambda message: message.text == 'Стоп', state=UserStates.waiting_stations)
def calculate_root(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        station_id_list = data['stations_id']
        station_list = data['stations']

    if len(station_id_list) < 2:
        bot.send_message(
            message.chat.id,
            'Недостаточно станций для расчета. Нужно как минимум 2 станции.',
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.delete_state(message.from_user.id, message.chat.id)
        return

    status_message = bot.send_message(
        message.chat.id,
        'Начинаю расчет маршрута...',
        reply_markup=types.ReplyKeyboardRemove()
    )
    total_time = 0
    route_times = []
    total_route = []

    for i in range(len(station_id_list) - 1):
        start_id = station_id_list[i]
        end_id = station_id_list[i + 1]
        route_segment = dijkstra(graph, start_id, end_id)
        total_time += route_segment[0]
        route_times.append(total_time)
        if i == 0:
            total_route.append(route_segment[2][0])
        for station_i in route_segment[2][1:]:
            total_route.append(station_i)

    prev_line_num = total_route[0].split('_')[-1]
    first_line_station = total_route[0]
    prev_station = total_route[0]
    bot_text = []
    route_sequences = []

    for station in total_route[1:]:
        line_num = station.split('_')[-1]
        if line_num != prev_line_num:
            if first_line_station != prev_station:
                route_sequences.append([stations_to_id_dict[first_line_station], stations_to_id_dict[prev_station], 0])
            route_sequences.append([stations_to_id_dict[prev_station], stations_to_id_dict[station], 1])
            first_line_station = station

        if station in station_list[:-1]:
            if prev_line_num == line_num:
                route_sequences.append([stations_to_id_dict[first_line_station], stations_to_id_dict[station] , 0])
            first_line_station = station
            route_sequences.append([stations_to_id_dict[station], 1])
        prev_line_num = station.split('_')[-1]
        prev_station = station

    if line_num != prev_line_num:
        if first_line_station != prev_station:
            route_sequences.append([stations_to_id_dict[first_line_station], stations_to_id_dict[prev_station], 1])
        route_sequences.append([stations_to_id_dict[prev_station], stations_to_id_dict[station], 1])
    else:
        if first_line_station != prev_station:
            route_sequences.append([stations_to_id_dict[first_line_station], stations_to_id_dict[station], 0])
    for i in range(len(route_sequences)):
        if len(route_sequences[i]) == 3:
            start, end, route_type = route_sequences[i]
            time = dijkstra(graph, start, end)[0]
            route_sequences[i].append(time)
            if route_type == 1:
                bot_text.append(
                    f'Пересадка с {id_to_stations_dict[start]} на {id_to_stations_dict[end]} ({format_time(minutes=time // 60)})')
            elif route_type == 0:
                bot_text.append(
                    f'Проезд с {id_to_stations_dict[start]} - {id_to_stations_dict[end]} ({format_time(minutes=time // 60)})')
        else:
            control_station_index = station_list.index(id_to_stations_dict[route_sequences[i][0]])
            bot_text.append(
                f'Достигнута {control_station_index}-я контрольная точка {id_to_stations_dict[route_sequences[i][0]]} за {format_time(route_times[control_station_index - 1] // 60, 2)}')

    bot.send_message(chat_id=message.chat.id,
                     text=f'Итоговый маршрут:\n\n{"\n".join(bot_text)}\n\n'
                          f'Время в пути: {format_time(total_time // 60)}')


@bot.message_handler(state=UserStates.waiting_stations)
def add_station(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        stations_arr = data['stations']

    stations = find_closest_matches(stations_data, message.text)
    if len(stations) >= 2:
        markup = create_station_keyboard(stations)
        bot.send_message(message.from_user.id,
                         text='Выбери конкретную станцию',
                         reply_markup=markup)
        return
    else:
        station = stations[0]
        if station in stations_arr:
            bot.send_message(message.from_user.id,
                             'Данная станция уже есть в маршруте, пожалуйста введите станцию заново')
            return

    station_id = stations_to_id_dict[station]

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['stations_id'].append(station_id)
        data['stations'].append(station)
        station_count = len(data['stations'])
    total_text = f'Твоя выбранная станция: {station}\n\nТекущий маршрут: {' -> '.join(data['stations'])}\n'

    if station_count < 2:
        bot.send_message(message.from_user.id,
                         text=total_text + '\nОтлично, введи следующую станцию',
                         reply_markup=types.ReplyKeyboardRemove())
    elif station_count >= 10:
        bot.send_message(message.from_user.id,
                         text=total_text + '\nДостигнут лимит количества контрольных точек, переходим к расчету маршрута')
        calculate_root(message)
        return
    elif station_count >= 2:
        bot.send_message(chat_id=message.from_user.id,
                         text=total_text + '\nОтлично, введи следующую станцию или заверши вывод словом "Стоп"',
                         reply_markup=create_stop_keyboard())


if __name__ == "__main__":
    bot.infinity_polling()
