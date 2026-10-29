import time
import requests
from bs4 import BeautifulSoup

URL = "https://myfin.by/currency/minsk"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TTL = 300  # кэш 5 минут

# только те названия, в которых я уверен; остальные берутся с самой страницы
BANK_NAMES = {
    "mtbank": "МТБанк",
    "bnbank": "БНБ-Банк",
    "rrb-bank": "РРБ-Банк",
    "belarusbank": "Беларусбанк",
    "statusbank": "Статусбанк",
    "alfabank": "Альфа-Банк",
    "belagroprombank": "Белагропромбанк",
    "belgazprombank": "Белгазпромбанк",
    "belinvestbank": "Белинвестбанк",
    "belswissbank": "Белсвиссбанк",
    "priorbank": "Приорбанк",
    "bps-sberbank": "БПС-Сбербанк",
    "paritetbank": "Паритетбанк",
    "technobank": "Технобанк",
    "zepterbank": "Зептер Банк",
    "bvebank": "Банк БелВЭБ",
}

_cache = {"data": None, "time": 0}


def _to_float(text):
    try:
        return float(text.strip().replace(",", "."))
    except ValueError:
        return None


def fetch_from_myfin():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    banks = {}
    # берём только обычную таблицу, без рекламных строк (data-row-type="ad")
    for row in soup.select('tr.currencies-courses__row-main[data-row-type="default"]'):
        alias = row.get("data-bank-sef-alias")
        if not alias or alias in banks:
            continue

        cells = row.find_all("td", class_="currencies-courses__currency-cell")
        if len(cells) < 2:
            continue

        buy = _to_float(cells[0].get_text())    # банк покупает USD («Сдать»)
        sell = _to_float(cells[1].get_text())   # банк продаёт USD («Купить»)
        if not sell:
            continue

        name = BANK_NAMES.get(alias)
        if not name:
            first = row.find("td")
            name = first.get_text(" ", strip=True) if first else alias
        banks[alias] = {
            "alias": alias,
            "bank": name,
            "buy": buy,
            "sell": sell,
            "address": "Адреса отделений добавим на следующем шаге",
        }

    if not banks:
        raise RuntimeError("Не удалось найти банки на странице myfin")
    return list(banks.values())


def get_rates():
    if _cache["data"] and time.time() - _cache["time"] < TTL:
        return _cache["data"]
    try:
        data = fetch_from_myfin()
        _cache.update(data=data, time=time.time())
        return data
    except Exception:
        if _cache["data"]:
            return _cache["data"]   # если сайт не ответил, показываем старые курсы
        raise

_branch_cache = {}
BRANCH_TTL = 600  # 10 минут


def fetch_branches(alias):
    url = f"https://myfin.by/bank/{alias}/usd"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    result = []
    for item in soup.select("div.currency-courses__list-item[data-currency-rates-item]"):
        addr_cell = item.select_one("[data-currency-rates-item-adress]")
        if not addr_cell:
            continue
        address = addr_cell["data-currency-rates-item-adress"].strip()
        if not address.startswith("г. Минск"):
            continue

        sell_el = item.select_one('[data-currency-rates-buy="usd"]')   # банк продаёт USD («Купить»)
        buy_el = item.select_one('[data-currency-rates-sell="usd"]')   # банк покупает USD («Сдать»)
        sell = _to_float(sell_el.get_text()) if sell_el else None
        buy = _to_float(buy_el.get_text()) if buy_el else None
        if not sell and not buy:
            continue
        result.append({"address": address, "sell": sell, "buy": buy})
    return result


def get_branches(alias):
    entry = _branch_cache.get(alias)
    if entry and time.time() - entry["time"] < BRANCH_TTL:
        return entry["data"]
    try:
        data = fetch_branches(alias)
        _branch_cache[alias] = {"data": data, "time": time.time()}
        return data
    except Exception:
        if entry:
            return entry["data"]
        raise
def last_update():
    return _cache["time"]


def refresh():
    _cache["time"] = 0


if __name__ == "__main__":
    for b in sorted(fetch_from_myfin(), key=lambda x: x["sell"]):
        print(b["alias"], "|", b["bank"], "|", b["buy"], "|", b["sell"])