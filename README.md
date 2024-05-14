<p align="center">
    <img src="https://avatars.githubusercontent.com/u/82603435?v=4" width="140px" alt="Helm LOGO"/>
</p>

<div align="center">

  [![Blog](https://img.shields.io/badge/Blog-blue?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://une-tasse-de.cafe/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Matomo](https://img.shields.io/badge/Matomo-3776AB?style=for-the-badge&logo=world&logoColor=white)](https://matomo.org)
  
</div>

## Matomo Exporter

This project is a Python script that exports data from a Matomo instance to Prometheus. It is designed to be as simple as possible to use and deploy in a container.

Since Matomo works with 'period' (day, week, month, year), the exporter will export the data for all types of periods and use labels to differentiate them.

## How to run

- Create a docker-compose file with the following content:

```yaml
services:
  matomo-exporter:
    build:
      context: .
      dockerfile: Dockerfile
    image: ghcr.io/qjoly/matomo-exporter:1.0.0
    restart: always
    ports:
      - 9000:9000
    env_file: .env
    environment:
      - LOG_LEVEL=DEBUG
      - SCRAPE_INTERVAL=60
```

- Create a `.env` file with the following content using your Matomo URL and token:

```conf
MATOMO_URL=https://matomo.yourdomain.com
MATOMO_TOKEN=yourtoken
```

Note: You can get your token by going to your Matomo instance on path `/index.php?module=UsersManager&action=userSecurity` or in the `Auth tokens` section of the `Security` tab.

- Run the container with the following command:

```bash
docker-compose up -d
```

- Access the metrics on `http://localhost:9000/metrics`.

## Configuration

You can configure the exporter using environment variables or arguments.

The following environment variables are available:

| Environment variable | Argument | Description | Default |
| --- | --- | --- | --- |
| `MATOMO_URL` | `--url` | Matomo URL | None |
| `MATOMO_TOKEN` | `--token` | Matomo token | None |
| `LOG_LEVEL` | None | Log level | `INFO` |	
| `SCRAPE_INTERVAL` | `--scrape-interval` | Scrape interval in seconds | `60` |
| `PORT` | `--port` | Port to expose the metrics | `9000` |
| `IP` | `--ip` | IP to expose the metrics | `0.0.0.0` |
| `CONCURRENT_THREADS` | `--concurrent-threads` | Number of concurrent threads | `4` |

## Exported metrics

The following metrics are exported:

| Metric | Description | Labels |
| --- | --- | --- |
| `number_of_sites` | Number of sites | |
| `number_of_visits` | Number of visits | `site_name`, `period` |
| `number_uniq_visitors` | Number of unique visitors | `site_name`, `period` |
| `number_bouncing_rate` | Bouncing rate | `site_name`, `period` |
| `number_of_actions` | Number of actions | `site_name`, `period` |
| `number_of_visits_per_page` | Number of visits per page | `site_name`, `page`, `period` |
| `number_of_visitors_per_os_version` | Number of visitors per OS version | `site_name`, `os_version`, `period` |
| `number_of_visitors_per_country` | Number of visitors per country | `site_name`, `country`, `period` |
| `number_of_visitors_per_region` | Number of visitors per region | `site_name`, `region`, `period`, `country`, `latitude`, `longitude` |


##  Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Report Issues](https://local//issues)**: Submit bugs found or log feature requests for the `.` project.
- **[Submit Pull Requests](https://local//blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Join the Discussions](https://local//discussions)**: Share your insights, provide feedback, or ask questions.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your local account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/qjoly/matomo-exporter.git
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to local**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="center">
   <a href="https://github.com/qjoly/matomo-exporter/graphs/contributors">
      <img src="https://contrib.rocks/image?repo=qjoly/matomo-exporter">
   </a>
</p>
</details>

---


```python
""" Metrics for the Matomo exporter """

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
    "number_of_visits_per_page",
    "Number of visits per page",
    ["site_name", "page", "period"],
)

NUMBER_VISITORS_PER_OS_VERSION = Gauge(
    "number_of_visitors_per_os_version",
    "Number of visitors per OS version",
    ["site_name", "os_version", "period"],
)

NUMBER_VISITORS_PER_COUNTRY = Gauge(
    "number_of_visitors_per_country",
    "Number of visitors per country",
    ["site_name", "country", "period"],
)

NUMBER_VISITORS_PER_REGION = Gauge(
    "number_of_visitors_per_region",
    "Number of visitors per region",
    ["site_name", "region", "period", "country", "latitude", "longitude"],
)
```