import logging
from flyflyt import app
from flyflyt.decorators import cached, cached_route
from flask import render_template, redirect, url_for, request, abort
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
from flightinfo.position import Position
from google.appengine.api import memcache


def datetimeformat(value, format='%H:%M'):
    return value.strftime(format)

app.jinja_env.filters['datetimeformat'] = datetimeformat

AIRPORT_XML_CACHE_TIMEOUT = 60 * 60 * 24
AIRLINE_XML_CACHE_TIMEOUT = 60 * 60 * 24
STATUS_XML_CACHE_TIMEOUT = 60 * 60 * 24
AIRPORT_HTML_CACHE_TIMEOUT = 60 * 60 * 24
FLIGHT_HTML_CACHE_TIMEOUT = 60

@cached(cache_key="airports_xml", timeout=AIRPORT_XML_CACHE_TIMEOUT)
def download_airport_xml():
    return FlightInformationService.download_airport_xml()

@cached(cache_key="airlines_xml", timeout=AIRLINE_XML_CACHE_TIMEOUT)
def download_airline_xml():
    return FlightInformationService.download_airline_xml()

@cached(cache_key="status_xml", timeout=STATUS_XML_CACHE_TIMEOUT)
def download_status_xml():
    return FlightInformationService.download_flight_status_xml()


def generate_airport_factory():
    airports_xml = download_airport_xml()
    airports = AirPortParser.parse_airports(airports_xml)
    airport_factory = AirPortFactory(airports)
    return airport_factory

def generate_airline_factory():
    airlines_xml = download_airline_xml()
    airlines = AirlineParser.parse_airlines(airlines_xml)
    airline_factory = AirlineFactory(airlines)
    return airline_factory

def generate_status_factory():
    status_xml = download_status_xml()
    statuses = FlightStatusParser.parse_statuses(status_xml)
    status_factory = FlightStatusFactory(statuses)
    return status_factory


def get_flights(airport, airline_factory, airport_factory, status_factory):
    query = Query(airport)
    xml = FlightInformationService.download_flight_xml(query)
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
@cached("airport_list_html", timeout = AIRPORT_HTML_CACHE_TIMEOUT)
def list_airports():
    return generate_airport_html()

@app.route('/airport/<code>')
@cached_route(timeout = FLIGHT_HTML_CACHE_TIMEOUT)
def list_flights(code):
    return generate_flight_html(code)

@app.route('/closest')
def find_closest_airport():
    try:
        latitude = float(request.args["latitude"])
        longitude = float(request.args["longitude"])
    except ValueError:
        logging.error("Position is not float: [%s, %s]",
                      request.args["latitude"],
                      request.args["longitude"])
        abort(400)

    factory = generate_airport_factory()
    airport = factory.get_closest_norwegian_airport(Position(latitude, longitude))

    logging.info("Airport %s found for location [%s, %s]", airport.code,
                 latitude, longitude)

    return redirect(url_for('list_flights', code=airport.code))
