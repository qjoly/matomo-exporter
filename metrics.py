from prometheus_client import Gauge

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
    "number_bouncing_rate_yesterday", "Bouncing rate", ["site_name"]
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
    "number_of_visited_pages_current_year",
    "Number of visited pages",
    ["site_name", "page"],
)

