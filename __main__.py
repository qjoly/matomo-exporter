#!/usr/bin/env python

import os, time
import matomo_api as ma
import argparse
from prometheus_client import start_http_server, Counter, REGISTRY, Gauge
import logging

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


DEFAULT_PORT = 9000
DEFAULT_SCRAPE_INTERVAL = 30
DEFAULT_IP = "0.0.0.0"

parser = argparse.ArgumentParser()
parser.add_argument("--url", help="Specify the Matomo URL")
parser.add_argument("--token", help="Specify the Matomo token")
parser.add_argument("--port", help="Specify the port")
parser.add_argument("--ip", help="Specify the IP address")
parser.add_argument("--scrape_interval", help="Specify the scrape interval")
args = parser.parse_args()

URL = args.url if args.url else os.environ.get("MATOMO_URL")
TOKEN = args.token if args.token else os.environ.get("MATOMO_TOKEN")

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

NUMBER_SITES = Gauge("number_of_sites", "Number of sites")
NUMBER_VISITS_YESTERDAY = Gauge(
    "number_of_visits_yesterday", "Number of visits", ["site_name"]
)
NUMBER_UNIQ_VISITORS_YESTERDAY = Gauge(
    "number_uniq_visitors_yesterday", "Number of visits", ["site_name"]
)
NUMBER_VISITS_CURRENT = Gauge(
    "number_of_visits_current_day", "Number of visits", ["site_name"]
)
NUMBER_UNIQ_VISITORS_CURRENT = Gauge(
    "number_uniq_visitors_current_day", "Number of visits", ["site_name"]
)

NUMBER_BOUNCING_RATE_CURRENT = Gauge(
    "percentage_bouncing_rate_current_day", "Bouncing rate", ["site_name"]
)
NUMBER_ACTIONS_CURRENT = Gauge(
    "number_of_actions_current_day", "Number of actions", ["site_name"]
)

NUMBER_BOUNCING_RATE_YESTERDAY = Gauge(
    "percentage_bouncing_rate_yesterday", "Bouncing rate", ["site_name"]
)
NUMBER_ACTIONS_YESTERDAY = Gauge(
    "number_of_actions_yesterday", "Number of actions", ["site_name"]
)

NUMBER_VISITS_PER_PAGE_CURRENT_MONTH = Gauge(
    "number_of_visited_pages_current_month",
    "Number of visited pages",
    ["site_name", "page"],
)

NUMBER_VISITS_PAR_PAGE_CURRENT_YEAR = Gauge(
    "number_of_visited_pages_current_yearly",
    "Number of visited pages",
    ["site_name", "page"],
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


def get_monthly_most_visited_pages(site_id, period):
    data = get_all_pages(site_id, period)

    dict_data = {}

    def print_data(data, parent=""):
        type_data = type(data)
        if type(data) is dict and data.get("subtable"):
            print_data(data.get("subtable"), parent + "/" + data.get("label"))
            dict_data[parent + "/" + data.get("label")] = data.get("nb_visits")
        elif type(data) is list:
            for i in data:
                if i.get("subtable"):
                    print_data(i.get("subtable"), parent + "/" + i.get("label"))
                    dict_data[parent + "/" + i.get("label")] = i.get("nb_visits")

    i = 0
    while i < len(data):
        print_data(data[i], "")
        i += 1
    return dict_data


if __name__ == "__main__":
    start_http_server(port=PORT, addr=IP)
    logging.info("Server started, listening on IP: %s:%s", IP, PORT)

    while True:
        NUMBER_SITES.set(get_number_of_sites())
        for site_id in get_all_sites_ids():
            logging.debug(f"Getting data for site {site_id}")
            try:
                site_name = get_name_of_site(site_id)
                site_data_yesterday = get_number_of_visits_yesterday(site_id)

                NUMBER_VISITS_YESTERDAY.labels(site_name).set(
                    site_data_yesterday.get("nb_visits")
                )
                NUMBER_UNIQ_VISITORS_YESTERDAY.labels(site_name).set(
                    site_data_yesterday.get("nb_uniq_visitors")
                )
                NUMBER_BOUNCING_RATE_YESTERDAY.labels(site_name).set(
                    site_data_yesterday.get("bounce_count")
                )
                NUMBER_ACTIONS_YESTERDAY.labels(site_name).set(
                    site_data_yesterday.get("nb_actions")
                )

                site_data_current = get_number_of_visits_current(site_id)
                NUMBER_VISITS_CURRENT.labels(site_name).set(
                    site_data_current.get("nb_visits")
                )
                NUMBER_UNIQ_VISITORS_CURRENT.labels(site_name).set(
                    site_data_current.get("nb_uniq_visitors")
                )
                NUMBER_BOUNCING_RATE_CURRENT.labels(site_name).set(
                    site_data_current.get("bounce_count")
                )

                NUMBER_ACTIONS_CURRENT.labels(site_name).set(
                    site_data_current.get("nb_actions")
                )

                monthly_visited_pages = get_monthly_most_visited_pages(
                    site_id, ma.period.month
                )

                for page in monthly_visited_pages.keys():
                    NUMBER_VISITS_PER_PAGE_CURRENT_MONTH.labels(site_name, page).set(
                        monthly_visited_pages[page]
                    )

                yearly_visited_pages = get_monthly_most_visited_pages(
                    site_id, ma.period.year
                )

                for page in yearly_visited_pages.keys():
                    NUMBER_VISITS_PAR_PAGE_CURRENT_YEAR.labels(site_name, page).set(
                        yearly_visited_pages[page]
                    )

            except FileExistsError as e:
                logging.error(f"Error getting data for site {site_id}, {e}")
                continue
        time.sleep(SCRAPE_INTERVAL)
