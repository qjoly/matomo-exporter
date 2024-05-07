from prometheus_client import Gauge

NUMBER_SITES = Gauge("number_of_sites", "Number of sites")

NUMBER_VISITS = Gauge("number_of_visits", "Number of visits", ["site_name", "period"])
NUMBER_UNIQ_VISITORS = Gauge(
    "number_uniq_visitors", "Number of visits", ["site_name", "period"]
)

NUMBER_BOUNCING_RATE = Gauge(
    "number_bouncing_rate", "Bouncing rate", ["site_name", "period"]
)
NUMBER_ACTIONS = Gauge(
    "number_of_actions", "Number of actions", ["site_name", "period"]
)

NUMBER_VISITS_PER_PAGE = Gauge(
    "number_of_visit_per_page",
    "Number of visits per page",
    ["site_name", "page", "period"],
)

NUMBER_VISITORS_PER_OS_VERSION = Gauge(
    "number_of_visitors_per_os_version",
    "Number of visitors per OS version",
    ["site_name", "os_version", "period"],
)
