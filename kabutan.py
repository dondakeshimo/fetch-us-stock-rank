"""Kabutan.

This script scrapes Stock ranking from kabutan and output CSV.

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
    name: str
    ticker: str
    value: float
    ratio_from_the_previous_day: float
    value_from_the_previous_day: float
    deal: int


def fetch(url: str) -> BeautifulSoup:
    res = requests.get(url)
    return BeautifulSoup(res.text, "html.parser")


def remove_header_and_footer(rows: List[Any]) -> List[Any]:
    return rows[1:-1]


def parse_ticker_cell(cell: str) -> str:
    """parse_name_cell.

    ex. 'UXIN'

    """
    return cell.strip()


def parse_name_cell(cell: str) -> str:
    """parse_name_cell.

    ex. 'ユーシンADR'

    """
    return cell.strip()


def parse_value_cell(cell: str) -> float:
    """parse_value_cell.

    ex. '0.70'

    """
    return float(cell)


def parse_ratio_cell(cell: str) -> float:
    """parse_ratio_cell.

    ex. '+15.25%'

    """
    ratio_str = re.findall(r"([-\+]*[-\d\.]+)%", cell)[0]

    if ratio_str == "-":
        ratio_str = "0"

    return float(ratio_str)


def parse_value_ratio_cell(cell: str) -> float:
    """parse_value_ratio_cell.

    ex. '+0.42'

    """
    value_str = re.findall(r"([-\+]*[-\d\.,]+)", cell)[0]
    return float(value_str)


def parse_deal_cell(cell: str) -> int:
    """parse_deal_cell.

    ex. '2,397,652'

    """
    deal_str = cell.replace(",", "")
    return int(deal_str)


def create_records(soup: BeautifulSoup) -> List[Record]:
    ranking_table = soup.find("table", {"class": "stock-table-pc"})
    rows = ranking_table.findAll("tr")
    rows = remove_header_and_footer(rows)

    records = []
    for row in rows:
        cells = row.findAll("td")
        ticker = parse_ticker_cell(cells[1].get_text())
        name = parse_name_cell(cells[3].get_text())
        value = parse_value_cell(cells[4].get_text())
        value_p = parse_value_ratio_cell(cells[5].get_text())
        ratio_p = parse_ratio_cell(cells[6].get_text())
        deal = parse_deal_cell(cells[7].get_text())
        records.append(Record(name, ticker, value, ratio_p, value_p, deal))

    return records


def dump_csv(path: pathlib.Path, records: List[Record]) -> None:
    with open(str(path), "w") as f:
        w = DataclassWriter(f, records, Record)
        w.write()


if __name__ == "__main__":
    records = []
    for i in tqdm(range(1, 10)):
        soup = fetch(f"https://us.kabutan.jp/tanken/adr?page={i}&size=50")
        records += create_records(soup)
        time.sleep(0.1)

    now_str = datetime.now().strftime("%Y%M%d%H%M%S")
    dump_csv(pathlib.Path(f"./kabutan_rank_{now_str}.csv"), records)
