# USD-Minsk

Web application that compares USD exchange rates across banks in Minsk and shows the best rate with branch addresses.

Live demo: https://usd-minsk.onrender.com (access is protected by a password)

## Features

- Buy and sell modes: the best rate for buying or selling USD
- Banks sorted by rate, with the best one highlighted
- Calculator: how many BYN you need or receive, and how much you save compared to the worst bank
- Branch addresses with rates, loaded on demand
- Rates cached for 5 minutes; if the source is unavailable, the last saved data is shown
- HTTP Basic authentication

## Tech stack

- Python, Flask
- requests and BeautifulSoup for collecting data from myfin.by
- HTML, CSS, JSON endpoint for branches
- Gunicorn, deployed on Render

## Run locally

pip install -r requirements.txt
python app.py

Then open http://127.0.0.1:5000. The password is set with the SITE_PASSWORD environment variable.

## Project structure

- app.py: Flask routes, authentication
- rates.py: scraping, parsing and caching of rates and branches
- templates/: HTML template
- static/: CSS

Rates are for reference only.
