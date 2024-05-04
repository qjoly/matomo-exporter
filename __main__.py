#!/usr/bin/env python

import os, time
import matomo_api as ma
import argparse
from prometheus_client import start_http_server, Counter, REGISTRY, Gauge
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")

parser = argparse.ArgumentParser()
parser.add_argument("--url", help="Specify the Matomo URL")
parser.add_argument("--token", help="Specify the Matomo token")
parser.add_argument("--refresh", help="Specify the refresh rate")
parser.add_argument("--port", help="Specify the port")
args = parser.parse_args()

URL = args.url if args.url else os.environ.get("MATOMO_URL")
TOKEN = args.token if args.token else os.environ.get("MATOMO_TOKEN")
REFRESH = (
    int(args.refresh) if args.refresh else 30
)  # Default refresh rate is 30 seconds
PORT = int(args.port) if args.port else 9000
if not URL or not TOKEN:
    print("Error: MATOMO_URL or MATOMO_TOKEN environment variables are not set.")
    exit(1)

api = ma.MatomoApi(URL, TOKEN)

NUMBER_SITES = Gauge("number_of_sites", "Number of sites")
NUMBER_VISITS_YESTERDAY = Gauge(
    "number_of_visits_yesterday", "Number of visits", ["site_name"]
)
NUMBER_UNIQ_VISITORS_YESTERDAY = Gauge(
    "number_uniq_visitors_yesterday", "Number of visits", ["site_name"]
)
NUMBER_VISITS_TODAY = Gauge("number_of_visits_today", "Number of visits", ["site_name"])
NUMBER_UNIQ_VISITORS_TODAY = Gauge(
    "number_uniq_visitors_today", "Number of visits", ["site_name"]
)


def get_number_of_sites():
    logging.debug("Getting number of sites")
    pars = ma.format.json | ma.translateColumnNames()
    try:
        qry_result = api.SitesManager().getAllSites(pars)
        return len(qry_result.json())
    except Exception as e:
        return -1


def get_name_of_site(site_id):
    pars = ma.format.json | ma.translateColumnNames() | ma.idSite.one_or_more(site_id)
    try:
        qry_result = api.SitesManager().getSiteFromId(pars).json()
        return qry_result.get("name")
    except Exception as e:
        logging.error(e, "Error getting site name")
        return "Unknown"


def get_all_sites_ids():
    pars = ma.format.json | ma.translateColumnNames()
    qry_result = api.SitesManager().getAllSites(pars)
    return [site.get("idsite") for site in qry_result.json()]


def get_number_of_visits_yesterday(site_id):
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | ma.date.yesterday
        | ma.period.day
    )
    qry_result = api.VisitsSummary().get(pars)
    return qry_result.json()


def get_number_of_visits_today(site_id):
    pars = (
        ma.format.json
        | ma.translateColumnNames()
        | ma.idSite.one_or_more(site_id)
        | ma.date.today
        | ma.period.day
    )
    qry_result = api.VisitsSummary().get(pars)
    return qry_result.json()


if __name__ == "__main__":
    start_http_server(PORT)
    logging.debug("Server started")
    while True:
        NUMBER_SITES.set(get_number_of_sites())
        print(get_all_sites_ids())
        for site_id in get_all_sites_ids():
            logging.debug(f"Getting data for site {site_id}")
            try:
                site_name = get_name_of_site(site_id)
                site_data = get_number_of_visits_yesterday(site_id)
                print(site_data)
                NUMBER_VISITS_YESTERDAY.labels(site_name).set(
                    site_data.get("nb_visits")
                )
                NUMBER_UNIQ_VISITORS_YESTERDAY.labels(site_name).set(
                    site_data.get("nb_uniq_visitors")
                )
                site_data = get_number_of_visits_today(site_id)
                NUMBER_VISITS_TODAY.labels(site_name).set(site_data.get("nb_visits"))
                NUMBER_UNIQ_VISITORS_TODAY.labels(site_name).set(
                    site_data.get("nb_uniq_visitors")
                )
            except:
                logging.error(f"Error getting data for site {site_id}")
                continue
        time.sleep(REFRESH)


