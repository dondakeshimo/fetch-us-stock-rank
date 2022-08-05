"""Main.

This script scrapes US Stock ranking and output CSV.

"""

from datetime import datetime
import pathlib
import re
import time
from dataclasses import dataclass
from typing import Any, List, Tuple

import requests
from bs4 import BeautifulSoup
from dataclass_csv import DataclassWriter
from tqdm import tqdm


@dataclass(frozen=True)
class Record:
    rank: int
    name: str
    ticker: str
    market: str
    value: float
    ratio_from_the_previous_day: float
    value_from_the_previous_day: float
    deal: int


def fetch(url: str) -> BeautifulSoup:
    res = requests.get(url)
    return BeautifulSoup(res.text, "html.parser")


def remove_header_and_footer(rows: List[Any]) -> List[Any]:
    return rows[1:-1]


def parse_name_cell(cell: str) -> Tuple[str, str, str]:
    """parse_name_cell.

    ex. 'テスラ[TSLA] - NASDAQ'

    """
    ret = re.findall(r"(.+)\[([-\w]+)\] - (\w+)", cell)[0]
    return ret


def parse_value_cell(cell: str) -> float:
    """parse_value_cell.

    ex. '925.90(17:20)'

    """
    return float(re.findall(r"([\d\.]+)\(.+\)", cell)[0])


def parse_ratio_cell(cell: str) -> Tuple[float, float]:
    """parse_ratio_cell.

    ex. '+0.40%(+3.71)'
    ex. '-%(---)'

    """
    ratio_str, value_str = re.findall(r"([-\+]*[-\d\.]+)%\(([-\+]*[-\d\.,]+)\)", cell)[0]

    if ratio_str == "-":
        ratio_str = "0"

    value_str = value_str.replace(",", "").replace("---", "0")

    return float(ratio_str), float(value_str)


def parse_deal_cell(cell: str) -> int:
    """parse_deal_cell.

    ex. '22,143,885千'

    """
    deal_str = cell.replace(",", "").replace("千", "")
    return int(deal_str) * 1000


def create_records(soup: BeautifulSoup) -> List[Record]:
    ranking_table = soup.find("table", {"class": "dsRanking_list"})
    rows = ranking_table.findAll("tr")
    rows = remove_header_and_footer(rows)

    records = []
    for row in rows:
        cells = row.findAll("td")
        rank = int(cells[0].get_text())
        name, ticker, market = parse_name_cell(cells[1].get_text())
        value = parse_value_cell(cells[2].get_text())
        ratio_p, value_p = parse_ratio_cell(cells[3].get_text())
        deal = parse_deal_cell(cells[4].get_text())
        records.append(Record(rank, name, ticker, market, value, ratio_p, value_p, deal))

    return records


def dump_csv(path: pathlib.Path, records: List[Record]) -> None:
    with open(str(path), "w") as f:
        w = DataclassWriter(f, records, Record)
        w.write()


if __name__ == "__main__":
    records = []
    for i in tqdm(range(1, 112)):
        soup = fetch(f"https://stocks.finance.yahoo.co.jp/us/ranking/?kd=31&tm=d&mk=&adr=&cg=&idx=&brk=&p={i}")
        records += create_records(soup)
        time.sleep(0.1)

    now_str = datetime.now().strftime("%Y%M%d%H%M%S")
    dump_csv(pathlib.Path(f"./us_rank_{now_str}.csv"), records)
