import logging
from flyflyt import app
from flask import render_template
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

AIRPORT_XML_CACHE_TIMEOUT = 60 * 60 * 24
AIRLINE_XML_CACHE_TIMEOUT = 60 * 60 * 24
STATUS_XML_CACHE_TIMEOUT = 60 * 60 * 24
FLIGHT_XML_CACHE_TIMEOUT = 60
AIRPORT_HTML_CACHE_TIMEOUT = 60 * 60 * 24
FLIGHT_HTML_CACHE_TIMEOUT = 60 

def generate_airport_factory():
    airports_xml = memcache.get("airports_xml")
    if airports_xml is None:
        airports_xml = FlightInformationService.download_airport_xml()
        memcache.set("airports_xml", airports_xml, AIRPORT_XML_CACHE_TIMEOUT)

    airports = AirPortParser.parse_airports(airports_xml)
    airport_factory = AirPortFactory(airports)

    return airport_factory

def generate_airline_factory():
    airlines_xml = memcache.get("airlines_xml")
    if airlines_xml is None:
        airlines_xml = FlightInformationService.download_airline_xml()
        memcache.set("airlines_xml", airlines_xml, AIRLINE_XML_CACHE_TIMEOUT)

    airlines = AirlineParser.parse_airlines(airlines_xml)
    airline_factory = AirlineFactory(airlines)
    return airline_factory

def generate_status_factory():
    status_xml = memcache.get("status_xml")
    if status_xml is None:
        status_xml = FlightInformationService.download_flight_status_xml()
        memcache.set("status_xml", status_xml, STATUS_XML_CACHE_TIMEOUT)

    statuses = FlightStatusParser.parse_statuses(status_xml)
    status_factory = FlightStatusFactory(statuses)
    return status_factory


def get_flights(airport, airline_factory, airport_factory, status_factory):
    flights_xml_name = airport.code + "_xml"
    xml = memcache.get(flights_xml_name)
    if xml is None:
        query = Query(airport)
        xml = FlightInformationService.download_flight_xml(query)
        memcache.set(flights_xml_name, xml, FLIGHT_XML_CACHE_TIMEOUT)

    return FlightParser.parse_flights(xml, airline_factory, airport_factory,
                                      status_factory)


def generate_airport_html():
    airport_factory = generate_airport_factory()
    airports = airport_factory.get_norwegian_airports()
    airports_html = render_template('list_airports.html', airports=airports)
    return airports_html



def is_departure(flight):
    return flight.direction == Flight.Directions.DEPARTURE

def is_arrival(flight):
    return flight.direction == Flight.Directions.ARRIVAL



def generate_flight_html(code):

    airport_factory = generate_airport_factory()
    airline_factory = generate_airline_factory()
    status_factory = generate_status_factory()

    airport = airport_factory.get_airport_by_code(code)    
    flights = get_flights(airport, airline_factory, 
                          airport_factory, status_factory)

    departures = filter(is_departure, flights)
    arrivals = filter(is_arrival, flights)

    return render_template('list_flights.html', 
                           airport=airport,
                           departures=departures,
                           arrivals=arrivals)




@app.route('/')
def list_airports():
    airports_html = memcache.get("airports_html")
    if airports_html is None:
        airports_html = generate_airport_html()
        memcache.set("airports_html", airports_html, AIRPORT_HTML_CACHE_TIMEOUT)
    else:
        logging.info("Found airport list in memcache.")

    return airports_html

@app.route('/airport/<code>')
def list_flights(code):
    airport_html_id = "airport_html_" + code
    flight_html = memcache.get(airport_html_id)
    if flight_html is None:
        flight_html = generate_flight_html(code)
        memcache.set(airport_html_id, flight_html, FLIGHT_HTML_CACHE_TIMEOUT)
    else:
        logging.info("Found html for airport " + code + " in memcache.")
        
    return flight_html

