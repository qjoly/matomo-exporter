import os
import matomo_api as ma
import argparse

TOKEN = os.environ.get('MATOMO_TOKEN')

parser = argparse.ArgumentParser()
parser.add_argument('--url', help='Specify the Matomo URL')
parser.add_argument('--token', help='Specify the Matomo token')
args = parser.parse_args()

URL = args.url if args.url else os.environ.get('MATOMO_URL')
TOKEN = args.token if args.token else os.environ.get('MATOMO_TOKEN')

if not URL or not TOKEN:
    print("Error: MATOMO_URL or MATOMO_TOKEN environment variables are not set.")
    exit(1)

api = ma.MatomoApi(URL, TOKEN)

def get_number_of_sites():
    pars = ma.format.json | ma.translateColumnNames()
    try:
        qry_result = api.SitesManager().getAllSites(pars)
        return len(qry_result.json())
    except Exception as e:
        print(e)
        return -1

def get_name_of_site(site_id):
    pars = ma.format.json | ma.translateColumnNames() | ma.idSite.one_or_more(site_id)
    qry_result = api.SitesManager().getAllSites(pars)
    print(qry_result.json())
    return qry_result
    

get_name_of_site(1)

# pars = ma.format.json | ma.language.fr | ma.translateColumnNames() \
#        | ma.idSite.one_or_more(1) | ma.date.yesterday | ma.period.day

# qry_result = api.VisitsSummary().get(pars)

# print(qry_result.json())
