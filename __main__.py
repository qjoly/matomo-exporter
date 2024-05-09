#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a simple Prometheus exporter for Matomo.
# It uses the Matomo API (using the matomo_api library) to get the data.


import os
import time
import argparse
import matomo_api as ma
from prometheus_client import start_http_server
from geopy.geocoders import Nominatim

from metrics import (
    NUMBER_SITES,
    NUMBER_VISITS,
    NUMBER_UNIQ_VISITORS,
    NUMBER_VISITS,
    NUMBER_UNIQ_VISITORS,
    NUMBER_BOUNCING_RATE,
    NUMBER_ACTIONS,
    NUMBER_BOUNCING_RATE,
    NUMBER_ACTIONS,
    NUMBER_VISITS_PER_PAGE,
    NUMBER_VISITORS_PER_OS_VERSION,
    NUMBER_VISITORS_PER_COUNTRY,
    NUMBER_VISITORS_PER_REGION,
)

import logging

############
# LOGGING  #
############
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

if LOG_LEVEL == "DEBUG":
    LEVEL = 10
elif LOG_LEVEL == "INFO":
    LEVEL = 20
elif LOG_LEVEL == "WARNING":
    LEVEL = 30
elif LOG_LEVEL == "ERROR":
    LEVEL = 40
else:
    LEVEL = 20

logging.basicConfig(level=LEVEL, format="%(asctime)s - %(message)s")

#############
# CONSTANTS #
#############
DEFAULT_PORT = 9000
DEFAULT_SCRAPE_INTERVAL = 30
DEFAULT_IP = "0.0.0.0"

#############
# ARGUMENTS #
#############
parser = argparse.ArgumentParser()
parser.add_argument("--url", help="Specify the Matomo URL")
parser.add_argument("--token", help="Specify the Matomo token")
parser.add_argument("--port", help="Specify the port")
parser.add_argument("--ip", help="Specify the IP address")
parser.add_argument("--scrape_interval", help="Specify the scrape interval")
args = parser.parse_args()

URL = args.url if args.url else os.environ.get("MATOMO_URL")
TOKEN = args.token if args.token else os.environ.get("MATOMO_TOKEN")

#################
# SET VARIABLES #
#################

# Set the port and IP address
if args.port:
    PORT = int(args.port)
elif os.environ.get("PORT"):
    PORT = int(os.environ.get("PORT"))
else:
    PORT = DEFAULT_PORT

if args.ip:
    IP = args.ip
elif os.environ.get("IP"):
    IP = os.environ.get("IP")
else:
    IP = DEFAULT_IP

# Set the scrape interval
if args.scrape_interval:
    SCRAPE_INTERVAL = int(args.scrape_interval)
elif os.environ.get("SCRAPE_INTERVAL"):
    SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL"))
else:
    SCRAPE_INTERVAL = DEFAULT_SCRAPE_INTERVAL

if not URL or not TOKEN:
    print("Error: MATOMO_URL or MATOMO_TOKEN environment variables are not set.")
    exit(1)

api = ma.MatomoApi(URL, TOKEN)


def get_number_of_sites():
    """Get the number of sites in the Matomo instance"""
    logging.debug("Getting number of sites")
    pars = ma.format.json | ma.translateColumnNames()
    try:
        qry_result = api.SitesManager().getAllSites(pars)
        return len(qry_result.json())
    except Exception:
        return -1


def get_name_of_site(site_id):
    """Get the name of a site given its ID"""
    pars = ma.format.json | ma.translateColumnNames() | ma.idSite.one_or_more(site_id)
    try:
        qry_result = api.SitesManager().getSiteFromId(pars).json()
        return qry_result.get("name")
    except Exception as e:
        logging.error(e, "Error getting site name")
        return "Unknown"


def get_all_sites_ids():
    """Get the IDs of all sites in the Matomo instance"""
    pars = ma.format.json | ma.translateColumnNames()
    qry_result = api.SitesManager().getAllSites(pars)
    return [site.get("idsite") for site in qry_result.json()]


def get_number_of_visits(site_id, day, period=ma.period.day):
    """Get the number of visits yesterday for a given site"""
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | day
        | period
    )
    qry_result = api.VisitsSummary().get(pars)
    return qry_result.json()


def get_number_of_visits_current(site_id):
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | ma.date.today
        | ma.period.day
    )
    qry_result = api.VisitsSummary().get(pars)
    return qry_result.json()


def get_all_pages(site_id, period):
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | ma.date.today
        | period
        | ma.expanded(True)
    )
    qry_result = api.Actions().getPageUrls(pars)
    return qry_result.json()


def visitors_details_os_versions(site_id, period):
    """Get the details of OS used by visitors for a given site and period"""
    pars = ma.format.json | ma.idSite.one_or_more(site_id) | ma.date.today | period
    qry_result = api.DevicesDetection().getOsVersions(pars)

    return qry_result.json()


def visitors_details_country(site_id, period):
    """Get the details of country used by visitors for a given site and period"""
    pars = ma.format.json | ma.idSite.one_or_more(site_id) | ma.date.today | period
    qry_result = api.UserCountry().getCountry(pars)

    return qry_result.json()


def get_most_visited_pages(site_id, period):
    data = get_all_pages(site_id, period)

    dict_data = {}

    def print_data(data, parent=""):
        if isinstance(data, dict) and data.get("subtable"):
            print_data(data.get("subtable"), parent + "/" + data.get("label"))
            dict_data[parent + "/" + data.get("label")] = data.get("nb_visits")
        elif isinstance(data, dict):
            dict_data[parent + data.get("label")] = data.get("nb_visits")
        elif isinstance(data, list):
            for i in data:
                if i.get("subtable"):
                    print_data(i.get("subtable"), parent + "/" + i.get("label"))
                    dict_data[parent + "/" + i.get("label")] = i.get("nb_visits")

    logging.debug("Number of pages: %s", len(data))
    i = 0
    while i < len(data):
        print_data(data[i], "")
        i += 1
    return dict_data


def get_regions(site_id, period):
    """Get the details of country used by visitors for a given site and period"""
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | ma.date.today
        | period
    )
    qry_result = api.UserCountry().getRegion(pars)
    return qry_result.json()

def get_coordinates(country, region=None):
    geolocator = Nominatim(user_agent="geo_locator", timeout=300)
    location_query = country
    if region:
        location_query += f", {region}"
    try:
        location = geolocator.geocode(location_query)
    except TypeError:
        location = None
        logging.error("Error getting coordinates for %s", location_query)
        return 0, 0
    except Exception as e:
        logging.error("Error getting coordinates for %s, %s", location_query, e)
        return 0, 0
    if location:
        return location.latitude, location.longitude
    else:
        return 0, 0

def update_metrics():
    """Update the Prometheus metrics with the data from the Matomo API"""
    NUMBER_SITES.set(get_number_of_sites())
    for site_id in get_all_sites_ids():
        logging.debug("Getting data for site %s", site_id)
        try:
            site_name = get_name_of_site(site_id)

            for metric in [
                ["day", ma.date.today, ma.period.day],
                ["previous_day", ma.date.yesterday, ma.period.day],
                ["week", ma.date.today, ma.period.week],
                ["month", ma.date.today, ma.period.month],
                ["year", ma.date.today, ma.period.year],
            ]:
                site_data = get_number_of_visits(site_id, metric[1], metric[2])

                NUMBER_VISITS.labels(site_name, metric[0]).set(
                    site_data.get("nb_visits")
                )
                if isinstance(site_data.get("nb_uniq_visitors"), int):
                    NUMBER_UNIQ_VISITORS.labels(site_name, metric[0]).set(
                        site_data.get("nb_uniq_visitors")
                    )
                NUMBER_BOUNCING_RATE.labels(site_name, metric[0]).set(
                    site_data.get("bounce_count")
                )
                NUMBER_ACTIONS.labels(site_name, metric[0]).set(
                    site_data.get("nb_actions")
                )

            for metric in [
                ["day", ma.period.day],
                ["month", ma.period.month],
                ["week", ma.period.week],
                ["year", ma.period.year],
            ]:
                for country_visitor in visitors_details_country(site_id, metric[1]):
                    NUMBER_VISITORS_PER_COUNTRY.labels(
                        site_name, country_visitor.get("label"), metric[0]
                    ).set(country_visitor.get("nb_visits"))
                for os_visitor in visitors_details_os_versions(site_id, metric[1]):
                    NUMBER_VISITORS_PER_OS_VERSION.labels(
                        site_name, os_visitor.get("label"), metric[0]
                    ).set(os_visitor.get("nb_visits"))
                for page, visits in get_most_visited_pages(site_id, metric[1]).items():
                    NUMBER_VISITS_PER_PAGE.labels(site_name, page, metric[0]).set(
                        visits
                    )
                for region in get_regions(site_id, metric[1]):   
                    try: 
                        coords = get_coordinates(region.get("country_name"), region.get("region"))
                    except TypeError:
                        coords = (0, 0)
                        logging.error("Error getting coordinates for %s", region.get("region"))
                    NUMBER_VISITORS_PER_REGION.labels(
                        site_name,
                        region.get("region"),
                        metric[0],
                        region.get("country"),
                        coords[0],
                        coords[1],
                    ).set(region.get("nb_visits"))

        except FileExistsError as e:
            logging.error("Error getting data for site %s, %s", site_id, e)
            continue


if __name__ == "__main__":
    """Main function"""
    start_http_server(port=PORT, addr=IP)
    logging.info("Server started, listening on IP: %s:%s", IP, PORT)

    while True:
        update_metrics()
        time.sleep(SCRAPE_INTERVAL)
