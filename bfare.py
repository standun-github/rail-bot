import json

import requests
from bs4 import BeautifulSoup
import test
import discord
from discord.ext import commands
import queueBot


class trainFinder():

    def __init__(self, myJourney):
        # URL_param
        self.arr_code = ""
        self.dep_code = ""
        self.out_date_param = ""
        self.out_time_param = ""
        self.in_date_param = ""
        self.in_time_param = ""
        self.URL_str = ""

        self.originStation = myJourney.get_outbound()
        self.destinationStation = myJourney.get_inbound()
        self.journeyTypeGroup = myJourney.get_journey_type()
        self.outwardDate = myJourney.get_outbound_date().strftime("%d-%m-%y")
        outward_time = myJourney.get_outbound_time()
        self.outwardHour = outward_time.split(":")[0]
        self.outwardMinute = myJourney.roundMinutes(outward_time.split(":")[1])

        if self.journeyTypeGroup == 'return':
            self.returnDate = myJourney.get_return_date().strftime("%d-%m-%y")
            return_time = myJourney.get_return_time()
            self.returnHour = return_time.split(":")[0]
            self.returnMinute = myJourney.roundMinutes(return_time.split(":")[1])

        ''' Testing use only
        print("Origin station.. ", self.originStation)
        print("Destination station.. ", self.destinationStation)
        print("Journey type.. ", self.journeyTypeGroup)
        print("Outward date.. ", self.outwardDate)
        print("Outward hour.. ", self.outwardHour)
        print("Outward min.. ", self.outwardMinute)
        print("Return date.. ", self.returnDate)
        print("Return hour.. ", self.returnHour)
        print("Return min.. ", self.returnMinute)
        '''

    def makeQuery(self):
        postURL = 'https://www.thetrainline.com/buytickets/'

        if self.journeyTypeGroup == 'return':
            predata = {'OriginStation': self.originStation,
                       'DestinationStation': self.destinationStation,
                       'RouteRestriction': 'NULL',
                       'ViaAvoidStation': '',
                       'journeyTypeGroup': self.journeyTypeGroup,
                       'outwardDate': self.outwardDate,
                       'OutwardLeaveAfterOrBefore': 'A',
                       'OutwardHour': self.outwardHour,
                       'OutwardMinute': self.outwardMinute,
                       'returnDate': self.returnDate,
                       'InwardLeaveAfterOrBefore': 'A',
                       'ReturnHour': self.returnHour,
                       'ReturnMinute': self.returnMinute,
                       'AdultsTravelling': '1',
                       'ChildrenTravelling': '0',
                       'railCardsType_0': '',
                       'railCardNumber_0': '',
                       'ExtendedSearch': 'Get times & tickets'}

        elif self.journeyTypeGroup == 'single':
            predata = {'OriginStation': self.originStation,
                       'DestinationStation': self.destinationStation,
                       'RouteRestriction': 'NULL',
                       'ViaAvoidStation': '',
                       'journeyTypeGroup': self.journeyTypeGroup,
                       'outwardDate': self.outwardDate,
                       'OutwardLeaveAfterOrBefore': 'A',
                       'OutwardHour': self.outwardHour,
                       'OutwardMinute': self.outwardMinute,
                       'returnDate': '',
                       'InwardLeaveAfterOrBefore': 'A',
                       'ReturnHour': '',
                       'ReturnMinute': '',
                       'AdultsTravelling': '1',
                       'ChildrenTravelling': '0',
                       'railCardsType_0': '',
                       'railCardNumber_0': '',
                       'ExtendedSearch': 'Get times & tickets'}

        postform = requests.post(postURL, data=predata)
        # print(postform.status_code)

        soup = BeautifulSoup(postform.text, 'html.parser')
        # print(soup)

        try:
            table = soup.find(id='timetable')
            train_schedule = json.loads(table.get('data-defaults'))
            # for key, value in train_schedule.items():
            # print(key, value)

            outbound_prices = train_schedule['fullJourneys'][0]
            # print("1", outbound_prices['cheapestTickets'])
            # for key,value in outbound_prices.items():
            #    print(key,value)

            if self.journeyTypeGroup == 'return':
                inbound_prices = train_schedule['fullJourneys'][1]
                # print("2", inbound_prices['cheapestTickets'])
                # for key,value in inbound_prices.items():
                #    print(key,value)
                # print("Finding cheapest ticket.. ")
                result1 = self.findCheapest(outbound_prices)
                result2 = self.findCheapest(inbound_prices)

                if result1 == "not found" or result2 == "not found":
                    queueBot.outputq.put("Sorry we can't find the right ticket for you! It may be sold out.")
                else:
                    if self.journeyTypeGroup == 'return':
                        self.out_date_param = self.outwardDate.replace("-", '')
                        self.out_time_param = result1.replace(":", '')
                        self.in_date_param = self.returnDate.replace("-", '')
                        self.in_time_param = result2.replace(":", '')
                        self.URL_str = self.dep_code + "/" + self.arr_code + "/" + self.out_date_param + "/" + \
                                       self.out_time_param + "/dep/" + self.in_date_param + "/" + self.in_time_param + "/dep"

                        self.URL_str = "https://ojp.nationalrail.co.uk/service/timesandfares/" + self.URL_str
                        queueBot.set_URL(self.URL_str)
                        # queueBot.outputq.put(self.URL_str)
                    elif self.journeyTypeGroup == 'single':
                        print("single")
                        self.out_date_param = self.outwardDate.replace("-", '')
                        self.out_time_param = result1.replace(":", '')
                        self.URL_str = self.dep_code + "/" + self.arr_code + "/" + self.out_date_param + "/" + \
                                       self.out_time_param + "/dep/"
                        self.URL_str = "https://ojp.nationalrail.co.uk/service/timesandfares/" + self.URL_str
                        queueBot.set_URL(self.URL_str)
                        # queueBot.outputq.put(self.URL_str)

            else:
                result = self.findCheapest(outbound_prices)
                if result == "not found":
                    queueBot.outputq.put("Sorry we can't find the right ticket for you! It may be sold out.")
        except:
            queueBot.outputq.put("Sorry we could not process your request.")
            return "not found"

    def findCheapest(self, fullJourneys):
        cheapestTickets = fullJourneys['cheapestTickets'][0]
        journeys = fullJourneys['journeys']
        first_class = fullJourneys['cheapestTickets'][1]
        tickets = cheapestTickets['tickets']
        price = 99999

        index = -1
        for i in range(len(tickets)):
            ticket = tickets[i]
            if ticket.get("soldOut") or ticket.get("notAvailable"):
                continue  # skip
            if float(ticket['price']) < price:
                price = float(ticket['price'])
                index = i

        # print(len(tickets))
        # print(len(journeys))
        # print(index)
        # print(journeys[index])

        arrival_date = journeys[index]['arrivalDateTime']
        arr_date = arrival_date[:10]
        arr_date = test.contains_date(arr_date)
        departure_time = journeys[index]['departureTime']
        departure_station = journeys[index]['departureCode']
        self.arr_code = departure_station
        arrival_time = journeys[index]['arrivalTime']
        arrival_station = journeys[index]['arrivalCode']
        self.dep_code = arrival_station
        if departure_time is None:
            return "not found"
        elif price == 99999:
            return "not found"
        else:
            if arr_date != 'empty':
                print("print")
                result = departure_station + "-" + arrival_station + " " + str(arr_date) + " " + departure_time + "-" + arrival_time + " £" + str(price)
                queueBot.outputq.put(result)
            elif arr_date == 'empty':
                result = departure_station + "-" + arrival_station + " " + departure_time + "-" + arrival_time + " £" + str(
                    price)
                queueBot.outputq.put(result)
            return departure_time


if __name__ == '__main__':
    # ======== Unit testing ========
    # print(">> Unit test for trainFinder(self, myJourney) __init__() method")

    text = "I want a return journey ticket to London Victoria from Norwich on 2021-10-02 at 09:00, and come back on 2021-10-02 at 12:00"
    # print("User input text.. ")
    # print(">>", text)
    booking1 = test.myBooking(text)
    finder = trainFinder(booking1)
    # print(">> Unit test for makeQuery() method.. ")
    # print("Opening on Trainline webpage.. ")
    finder.makeQuery()

# https://stackoverflow.com/questions/42932168/scraping-data-off-thetrainline-com-for-tickets-and-fares
# https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python
# https://raufer.github.io/2017/05/10/scrapping-around-with-python/
