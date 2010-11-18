import logging
from flyflyt import app
from flask import render_template, make_response
from flightinfo.airport import AirPort
from flightinfo.flightinformationservice import FlightInformationService
from flightinfo.airportparser import AirPortParser
from flightinfo.airlinefactory import AirlineFactory
from flightinfo.airlineparser import AirlineParser
from flightinfo.airport import AirPort
from flightinfo.airportfactory import AirPortFactory
from flightinfo.airportparser import AirPortParser
from flightinfo.flight import Flight
from flightinfo.flightinformationservice import FlightInformationService
from flightinfo.flightparser import FlightParser
from flightinfo.flightstatusparser import FlightStatusParser
from flightinfo.flightstatusfactory import FlightStatusFactory
from flightinfo.query import Query
from google.appengine.api import memcache


def datetimeformat(value, format='%H:%M'):
    return value.strftime(format)

app.jinja_env.filters['datetimeformat'] = datetimeformat

def generate_airport_html():
    airports_xml = memcache.get("airports_xml")
    if airports_xml is None:
        airports_xml = FlightInformationService.download_airport_xml()
        memcache.set("airports_xml", airports_xml, 6000)
        
    airports = AirPortParser.parse_airports(airports_xml)
    airport_factory = AirPortFactory(airports)

    airports = airport_factory.get_norwegian_airports()
    airports_html = render_template('list_airports.html', airports=airports)

    return airports_html


def generate_flight_html(code):
    airports_xml = memcache.get("airports_xml")
    if airports_xml is None:
        airports_xml = FlightInformationService.download_airport_xml()
        memcache.set("airports_xml", airports_xml, 6000)

    airports = AirPortParser.parse_airports(airports_xml)
    airport_factory = AirPortFactory(airports)
    
    airlines_xml = memcache.get("airlines_xml")
    if airlines_xml is None:
        airlines_xml = FlightInformationService.download_airline_xml()
        memcache.set("airlines_xml", airlines_xml, 6000)

    airlines = AirlineParser.parse_airlines(airlines_xml)
    airline_factory = AirlineFactory(airlines)
    
    status_xml = memcache.get("status_xml")
    if status_xml is None:
        status_xml = FlightInformationService.download_flight_status_xml()
        memcache.set("status_xml", status_xml, 6000)

    statuses = FlightStatusParser.parse_statuses(status_xml)
    status_factory = FlightStatusFactory(statuses)


    flights_xml_name = code + "_xml"
    xml = memcache.get(flights_xml_name)
    airport = airport_factory.get_airport_by_code(code)
    if xml is None:
        query = Query(airport)
        xml = FlightInformationService.download_flight_xml(query)
        memcache.set(flights_xml_name, xml, 60)
    
    flights = FlightParser.parse_flights(xml, airline_factory, airport_factory,
                                         status_factory)


    def is_departure(flight):
        return flight.direction == Flight.Directions.DEPARTURE

    def is_arrival(flight):
        return flight.direction == Flight.Directions.ARRIVAL

    departures = filter(is_departure, flights)
    arrivals = filter(is_arrival, flights)

    return render_template('list_flights.html', 
                           airport=airport,
                           departures=departures,
                           arrivals=arrivals)




@app.route('/')
def list_airports():
    airports_html = memcache.get("list_airports_html")
    if airports_html is None:
        airports_html = generate_airport_html()
        memcache.set("list_airports_html", airports_html, 6000)
    else:
        logging.info("Found airport list in memcache.")

    return airports_html

@app.route('/airport/<code>')
def list_flights(code):
    airport_html_id = "airport_html" + code
    flight_html = memcache.get(airport_html_id)
    if flight_html is None:
        flight_html = generate_flight_html(code)
        memcache.set(airport_html_id, flight_html, 60)
    else:
        logging.info("Found html for " + code + " in memcache.")
        
    return flight_html

