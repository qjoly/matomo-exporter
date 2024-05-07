#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a simple Prometheus exporter for Matomo.
# It uses the Matomo API (using the matomo_api library) to get the data.


import os
import time
import argparse
import matomo_api as ma
from prometheus_client import start_http_server
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
)
import logging

############
# LOGGING  #
############
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

if LOG_LEVEL == "DEBUG":
    level = 10
elif LOG_LEVEL == "INFO":
    level = 20
elif LOG_LEVEL == "WARNING":
    level = 30
elif LOG_LEVEL == "ERROR":
    level = 40
else:
    level = 20

logging.basicConfig(level=level, format="%(asctime)s - %(message)s")

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
    except:
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


def get_number_of_visits_yesterday(site_id):
    """Get the number of visits yesterday for a given site"""
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | ma.date.yesterday
        | ma.period.day
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


def get_most_visited_pages(site_id, period):
    data = get_all_pages(site_id, period)

    dict_data = {}

    def print_data(data, parent=""):
        if type(data) is dict and data.get("subtable"):
            print_data(data.get("subtable"), parent + "/" + data.get("label"))
            dict_data[parent + "/" + data.get("label")] = data.get("nb_visits")
        elif type(data) is dict:
            dict_data[parent + data.get("label")] = data.get("nb_visits")
        elif type(data) is list:
            for i in data:
                if i.get("subtable"):
                    print_data(i.get("subtable"), parent + "/" + i.get("label"))
                    dict_data[parent + "/" + i.get("label")] = i.get("nb_visits")

    logging.debug("Number of pages: %s", len(data))
    i = 0
    # While there are more pages to process, keep going
    while i < len(data):
        """Print the data recursively and store it in a dictionary"""
        print_data(data[i], "")
        i += 1
    return dict_data


def update_metrics():
    """Update the Prometheus metrics with the data from the Matomo API"""
    NUMBER_SITES.set(get_number_of_sites())
    for site_id in get_all_sites_ids():
        logging.debug(f"Getting data for site {site_id}")
        try:
            site_name = get_name_of_site(site_id)
            site_data_yesterday = get_number_of_visits_yesterday(site_id)

            NUMBER_VISITS.labels(site_name, "previous_day").set(
                site_data_yesterday.get("nb_visits")
            )
            NUMBER_UNIQ_VISITORS.labels(site_name, "previous_day").set(
                site_data_yesterday.get("nb_uniq_visitors")
            )
            NUMBER_BOUNCING_RATE.labels(site_name, "previous_day").set(
                site_data_yesterday.get("bounce_count")
            )
            NUMBER_ACTIONS.labels(site_name, "previous_day").set(
                site_data_yesterday.get("nb_actions")
            )

            site_data_current = get_number_of_visits_current(site_id)
            NUMBER_VISITS.labels(site_name, "day").set(
                site_data_current.get("nb_visits")
            )
            NUMBER_UNIQ_VISITORS.labels(site_name, "day").set(
                site_data_current.get("nb_uniq_visitors")
            )
            NUMBER_BOUNCING_RATE.labels(site_name, "day").set(
                site_data_current.get("bounce_count")
            )

            NUMBER_ACTIONS.labels(site_name, "day").set(
                site_data_current.get("nb_actions")
            )

            daily_visited_pages = get_most_visited_pages(site_id, ma.period.day)
            for page in daily_visited_pages.keys():
                NUMBER_VISITS_PER_PAGE.labels(site_name, page, "day").set(
                    daily_visited_pages[page]
                )

            monthly_visited_pages = get_most_visited_pages(site_id, ma.period.month)

            for page in monthly_visited_pages.keys():
                NUMBER_VISITS_PER_PAGE.labels(site_name, page, "month").set(
                    monthly_visited_pages[page]
                )

            yearly_visited_pages = get_most_visited_pages(site_id, ma.period.year)

            for page in yearly_visited_pages.keys():
                NUMBER_VISITS_PER_PAGE.labels(site_name, page, "year").set(
                    yearly_visited_pages[page]
                )

            for os in visitors_details_os_versions(site_id, ma.period.day):
                NUMBER_VISITORS_PER_OS_VERSION.labels(
                    site_name, os.get("label"), "day"
                ).set(os.get("nb_visits"))

            for os in visitors_details_os_versions(site_id, ma.period.month):
                NUMBER_VISITORS_PER_OS_VERSION.labels(
                    site_name, os.get("label"), "month"
                ).set(os.get("nb_visits"))

            for os in visitors_details_os_versions(site_id, ma.period.year):
                NUMBER_VISITORS_PER_OS_VERSION.labels(
                    site_name, os.get("label"), "year"
                ).set(os.get("nb_visits"))

        except FileExistsError as e:
            logging.error(f"Error getting data for site {site_id}, {e}")
            continue


if __name__ == "__main__":
    """Main function"""
    start_http_server(port=PORT, addr=IP)
    logging.info("Server started, listening on IP: %s:%s", IP, PORT)

    visitors_details_os_versions(1, ma.period.month)

    while True:
        update_metrics()
        time.sleep(SCRAPE_INTERVAL)
