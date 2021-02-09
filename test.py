import sqlite3
from datetime import datetime
import random
from nltk.corpus import stopwords
from nltk.tag import StanfordNERTagger, pos_tag
from nltk.tokenize import word_tokenize
from dateparser.search import search_dates
import discord
from discord.ext import commands
import queueBot
st = StanfordNERTagger('stanford-ner-2020-11-17/classifiers/english.all.3class.distsim.crf.ser.gz',
                       'stanford-ner-2020-11-17/stanford-ner.jar',
                       encoding='utf-8')

conn = sqlite3.connect('database.db')
c = conn.cursor()


def contains_date(text):
    date_time = search_dates(text, settings={'REQUIRE_PARTS': ['day', 'month']})
    # print(date_time)

    d = 'empty'
    if date_time is not None:
        date = date_time[0][1].date()
        d = date

    return d


def contains_time(text):
    date_time = search_dates(text)
    # print(date_time)
    time = 'empty'
    if date_time is not None:
        date = date_time[0][1].time()
        time = date.strftime("%H:%M")
        # print(time)
        if time == "00:00":
            time = 'empty'

    return time


def compare_to_now(include_time, date_time):
    now = datetime.now()
    # passed param  example  datetime(2020,12,30)

    if include_time:  # compare with time
        if date_time < now:
            return True
    else:  # compare without
        if date_time < now.date():
            return True

    return False


def compare_dates(include_time, outbound_date, return_date):
    if include_time:
        '''
        print("time only")
        compare two datetime.datetime obj
        '''
        if return_date > outbound_date:
            return True
    else:
        '''
        print("date only")
        compare two datetime.date obj
        '''
        if return_date > outbound_date or return_date == outbound_date:
            return True

    return False


def remove_stop_words(text):
    tokenized = word_tokenize(text)
    tokens_without_sw = [word for word in tokenized if not word in stopwords.words()]

    filtered = (" ").join(tokens_without_sw)

    return filtered


class myBooking:

    def __init__(self):
        self.from_outbound = 'empty'  # default value
        self.to_inbound = 'empty'  # default value
        self.journey_type = 'single'  # default value
        self.outbound_date = 'empty'
        self.return_date = 'empty'
        self.outbound_time = 'empty'
        self.return_time = 'empty'

    def __init__(self, text_input):
        tokenized_text = word_tokenize(text_input)
        classified_text = st.tag(tokenized_text)
        # print(classified_text)
        tagged = pos_tag(tokenized_text)
        # print(tagged)
        self.from_outbound = 'empty'  # default value
        self.to_inbound = 'empty'  # default value
        self.journey_type = 'single'  # default value
        counter = 0
        for x in tagged:
            if x[1] == "IN":
                next_word = classified_text[counter + 1]
                if next_word[1] == 'LOCATION' or next_word[1] == 'ORGANIZATION':
                    self.from_outbound = self.findRailwayStation(classified_text, counter + 1)
            counter = counter + 1

        while self.from_outbound == 'empty':
            print("22")
            queueBot.outputq.put("Please specify outbound station.")
            user_input = queueBot.inputq.get()
            self.from_outbound = self.find_railway_station(user_input)

        counter = 0
        for x in tagged:
            if x[1] == "TO":
                next_word = classified_text[counter + 1]
                if next_word[1] == 'LOCATION' or next_word[1] == 'ORGANIZATION':
                    self.to_inbound = self.findRailwayStation(classified_text, counter + 1)
            counter = counter + 1

        while self.to_inbound == 'empty':
            print("23")
            queueBot.outputq.put("Please specify inbound station.")
            user_input = queueBot.inputq.get()
            self.to_inbound = self.find_railway_station(user_input)

        filtered_text = remove_stop_words(text_input)
        # print(filtered_text)
        date_list = search_dates(filtered_text, settings={'REQUIRE_PARTS': ['day']})
        # print(date_list)

        self.outbound_date = 'empty'
        self.return_date = 'empty'
        self.outbound_time = 'empty'
        self.return_time = 'empty'

        now = datetime.now()
        if date_list is not None:
            length = len(date_list)
            if length > 1:
                self.journey_type = 'return'
                first = date_list[0][1]
                second = date_list[1][1]
                if second > first > now:
                    self.return_date = second.date()
                    self.outbound_date = first.date()
                    t1 = first.strftime("%H:%M")
                    if t1 != "00:00":
                        self.outbound_time = t1
                    t2 = second.strftime("%H:%M")
                    if t2 != "00:00":
                        self.return_time = t2
            if length == 1:
                date = date_list[0][1]
                if date > now:
                    self.outbound_date = date.date()
                    t1 = date.strftime("%H:%M")
                    if t1 != "00:00":
                        self.outbound_time = t1

    def confirm_details(self):
        if self.journey_type == 'return':
            sentence = "You want a " + self.journey_type+" journey ticket to "+ self.to_inbound +" from "+self.from_outbound+" on "+ str(self.outbound_date)+" at "+ str(self.outbound_time)+", and come back on "+ str(self.return_date)+" at "+ str(self.return_time) + " (Yes/No)"
            queueBot.outputq.put(sentence)
        if self.journey_type == 'single':
            singleSentence = "You want a " + self.journey_type+" journey ticket to "+ self.to_inbound +" from "+self.from_outbound+" on "+ str(self.outbound_date)+" at "+ str(self.outbound_time)+ " (Yes/No)"
            queueBot.outputq.put(singleSentence)

    def findRailwayStation(self, classified_text, counter):
        # print(classified_text[counter])
        word = classified_text[counter][0]
        station = 'empty'
        self.choices = []
        self.choices.clear()

        for i in range(1, len(classified_text) - counter):
            next_word = classified_text[counter + i][0]

            c.execute('SELECT * FROM railway_stations WHERE station_name LIKE ?', ('%' + word + '%',))
            row = c.fetchall()
            for i in range(len(row)):
                self.choices.append(row[i][0])
            if len(row) == 1:
                station = row[0][0]
            elif not row:
                if station == 'empty' and len(self.choices) != 0:
                    random.shuffle(self.choices)
                    queueBot.outputq.put("Do you mean...")
                    length = len(self.choices)
                    if length == 2:
                        for choice in self.choices:
                            queueBot.outputq.put(choice)
                    if length == 3:
                        for i in range(0, 3):
                            queueBot.outputq.put(self.choices[i])
                    if length > 3:
                        for i in range(0, 4):
                            queueBot.outputq.put(self.choices[i])
                break

            word = word + " " + next_word

        return station.strip()

    def find_railway_station(self, word):
        self.choices = []
        self.choices.clear()
        station_name = 'empty'

        c.execute('SELECT * FROM railway_stations WHERE station_name LIKE ?', ('%' + word + '%',))
        row = c.fetchall()
        if len(row) == 1:
            station_name = row[0][0]
        else:
            word_token = word.split(" ")
            # print(word_token)
            str = ''
            for w in word_token:
                str = str + " " + w
                str = str.strip()
                # print(str.strip())
                c.execute('SELECT * FROM railway_stations WHERE station_name LIKE ?', ('%' + str + '%',))
                row = c.fetchall()
                # print(row)
                if not row:
                    continue
                if len(row) > 1:
                    for i in range(len(row)):
                        self.choices.append(row[i][0])
        # print(self.choices)
        if station_name == 'empty' and len(self.choices) != 0:
            random.shuffle(self.choices)
            queueBot.outputq.put("Do you mean...")
            length = len(self.choices)
            if length == 2:
                for choice in self.choices:
                    str = ">>" + choice
                    queueBot.outputq.put(str)
            elif length == 3:
                for i in range(0, 3):
                    str = ">>" + self.choices[i]
                    queueBot.outputq.put(str)
            elif length > 3:
                for i in range(0, 4):
                    str = ">>" + self.choices[i]
                    queueBot.outputq.put(str)

        return station_name.strip()

    def get_outbound(self):
        return self.from_outbound

    def get_outbound_date(self):
        return self.outbound_date

    def get_outbound_time(self):
        return self.outbound_time

    def get_inbound(self):
        return self.to_inbound

    def get_return_date(self):
        return self.return_date

    def get_return_time(self):
        return self.return_time

    def get_journey_type(self):
        return self.journey_type

    def get_choices(self):
        return self.choices

    def set_outbound(self, location):
        self.from_outbound = location

    def set_outbound_date(self, date_time):
        self.outbound_date = date_time

    def set_outbound_time(self, date_time):
        self.outbound_time = date_time

    def set_inbound(self, location):
        self.to_inbound = location

    def set_return_date(self, date_time):
        self.return_date = date_time

    def set_return_time(self, date_time):
        self.return_time = date_time

    def set_journey_type(self, type):
        self.journey_type = type

    def roundMinutes(self, minutes):
        min = '00'
        if 0 < int(minutes) <= 15:
            min = '15'
        if 15 < int(minutes) <= 30:
            min = '30'
        if 30 < int(minutes) <= 45:
            min = '45'

        return min


def sample_test_myBooking_init(text):
    booking = myBooking(text)
    print(">> User text input: ", text)
    print(">> Unit test for myBooking __init__() method")
    place1 = booking.get_outbound()
    print("Outbound: ", place1, type(place1))
    place2 = booking.get_inbound()
    print("Inbound: ", place2, type(place2))
    date = booking.get_outbound_date()
    print("Outbound date: ", date, type(date))
    time = booking.get_outbound_time()
    print("Outbound time: ", time, type(time))
    r_date = booking.get_return_date()
    print("Return date: ", r_date, type(r_date))
    r_time = booking.get_return_time()
    print("Return time: ", r_time, type(r_time))
    journey = booking.get_journey_type()
    print("Journey type: ", journey, type(journey))
    print(">> Unit test for myBooking confirm_details() method")
    booking.confirm_details()


def sample_test_find_railway_station(booking):
    print(">> Unit test for myBooking find_railway_station() method")
    for i in range(0, 3):
        print(">> Type station name..")
        word = input()
        result = myBooking.find_railway_station(booking, word)
        print("Function return result.. ", result, type(result))


def sample_test_remove_stop_words(text):
    print(">> Unit test for remove_stop_words() method")
    print(">> Text: ", text)
    print(">> Filtered text: ", remove_stop_words(text))


def sample_test_compare_dates():
    date1 = datetime(2021, 2, 10, 10, 00)
    date2 = datetime(2021, 2, 10, 15, 00)
    print(">> Unit test for compare_dates(include_time, outbound_date, return_date) method")
    print("Comparing two date time object.. \n")
    print("param 1: True,", "param 2: ", date1, ",param 3: ", date2)
    print("Function return result..", compare_dates(True, date1, date2))
    print("param 1: False,", "param 2: ", date1.date(), ",param 3: ", date2.date())
    print("Function return result..", compare_dates(False, date1.date(), date2.date()))
    date1 = datetime(2021, 2, 10, 10, 00)
    date2 = datetime(2021, 1, 9, 12, 00)
    print("param 1: True,", "param 2: ", date1, ",param 3: ", date2)
    print("Function return result..", compare_dates(True, date1, date2))
    print("param 1: False,", "param 2: ", date1.date(), ",param 3: ", date2.date())
    print("Function return result..", compare_dates(False, date1.date(), date2.date()))


def sample_test_compare_to_now():
    print(">> Unit test for compare_to_now(include_time, date_time) method")
    now = datetime.now()
    print("Date and time now..", now)
    date1 = datetime(2021, 1, 21, 15, 00)
    date2 = datetime(2021, 1, 21, 18, 00)
    print("param 1: True,", "param 2: ", date1)
    print("Function return result..", compare_to_now(True, date1))
    print("param 1: True,", "param 2: ", date2)
    print("Function return result..", compare_to_now(True, date2))
    date1 = datetime(2021, 1, 20, 12, 00)
    print("param 1: False,", "param 2: ", date1.date())
    print("Function return result..", compare_to_now(False, date1.date()))
    date2 = datetime(2021, 1, 21, 12, 00)
    print("param 1: False,", "param 2: ", date2.date())
    print("Function return result..", compare_to_now(False, date2.date()))
    date2 = datetime(2021, 1, 22, 12, 00)
    print("param 1: False,", "param 2: ", date2.date())
    print("Function return result..", compare_to_now(False, date2.date()))


def sample_test_contains_time(text):
    print(">> Unit test for contains_time() method")
    print(">> User text input: ", text)
    result = contains_time(text)
    print("Function return result..", result, type(result))


def sample_test_contains_date(text):
    print(">> Unit test for contains_date() method")
    print(">> User text input: ", text)
    result = contains_date(text)
    print("Function return result..", result, type(result), "\n")


def sample_test_myBooking_round_minutes(booking):
    print(">> Unit test for myBooking roundMinutes(self, minutes) method")
    min = 14
    print("int: ", min, "rounded int: ", myBooking.roundMinutes(booking, min))
    min = 26
    print("int: ", min, "rounded int: ", myBooking.roundMinutes(booking, min))
    min = 32
    print("int: ", min, "rounded int: ", myBooking.roundMinutes(booking, min))
    min = 43
    print("int: ", min, "rounded int: ", myBooking.roundMinutes(booking, min))
    min = 51
    print("int: ", min, "rounded int: ", myBooking.roundMinutes(booking, min))


if __name__ == '__main__':
    '''======== Unit testing ========
    text = "I want to go from Norwich to London King's Cross on February 10th at 07:00 and return on February " \
           "13th. "
    booking = myBooking(text)
    # sample_test_myBooking_init(text) #done
    # sample_test_find_railway_station(booking) #done
    # sample_test_remove_stop_words(text) #done
    # sample_test_compare_dates() #done
    # sample_test_compare_to_now() #done
    # sample_test_contains_date(remove_stop_words(text)) #done
    # sample_test_contains_time(remove_stop_words(text)) #done
    # sample_test_myBooking_round_minutes(booking) #done
    '''
