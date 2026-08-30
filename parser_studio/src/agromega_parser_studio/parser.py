import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import requests
from lxml import html

CONFIG_KEYS = {"item", "max_pages", "next_page", "snapshot_complete"}
PRICE_KEYS = {"price", "min_price", "max_price"}
SOURCE_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AgroMegaParser/1.0; +https://agromega.com.ua/)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.7",
}


def extract_price(value):
    if value is None:
        return None
    compact = re.sub(r"[\s\u00a0\u202f]", "", str(value))
    match = re.search(r"[-+]?\d[\d.,]*", compact)
    if not match:
        return None
    number = match.group()
    if "," in number and "." in number:
        decimal_separator = "," if number.rfind(",") > number.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        number = number.replace(thousands_separator, "").replace(decimal_separator, ".")
    elif "," in number:
        number = number.replace(",", ".")
    try:
        return float(Decimal(number))
    except InvalidOperation:
        return None


def xpath_value(value):
    if hasattr(value, "text_content"):
        value = value.text_content()
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return " ".join(value.split()) if isinstance(value, str) else value


def parse_html(content: bytes | str, parser_map: dict) -> list[dict]:
    tree = html.fromstring(content)
    item_xpath = parser_map.get("item")
    if item_xpath:
        parsed = []
        for node in tree.xpath(item_xpath):
            product = {}
            for key, xpath in parser_map.items():
                if key in CONFIG_KEYS:
                    continue
                relative_xpath = f".{xpath}" if xpath.startswith("//") else xpath
                values = node.xpath(relative_xpath)
                value = xpath_value(values[0]) if values else None
                product[key] = extract_price(value) if key in PRICE_KEYS else value
            parsed.append(product)
        return parsed

    extracted = {}
    for key, xpath in parser_map.items():
        if key in CONFIG_KEYS:
            continue
        values = [xpath_value(value) for value in tree.xpath(xpath)]
        extracted[key] = [extract_price(value) for value in values] if key in PRICE_KEYS else values
    name_count = len(extracted.get("name", []))
    for key, values in extracted.items():
        if values and len(values) != name_count:
            raise ValueError(f"XPath count mismatch: name={name_count}, {key}={len(values)}")
    return [
        {key: values[index] if values else None for key, values in extracted.items()} for index in range(name_count)
    ]


def next_page_url(content: bytes | str, current_url: str, parser_map: dict) -> str | None:
    xpath = parser_map.get("next_page")
    if not xpath:
        return None
    values = html.fromstring(content).xpath(xpath)
    value = xpath_value(values[0]) if values else None
    return urljoin(current_url, value) if value else None


def max_pages(parser_map: dict) -> int:
    value = parser_map.get("max_pages") or (10 if parser_map.get("next_page") else 1)
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Parser max_pages must be an integer.") from exc
    if not 1 <= value <= 50:
        raise ValueError("Parser max_pages must be between 1 and 50.")
    return value


class StaticSourceRunner:
    def __init__(self, timeout=30, session=None):
        self.timeout = timeout
        self.session = session or requests.Session()
        if session is None:
            self.session.headers.update(SOURCE_REQUEST_HEADERS)

    def preview(self, source: dict) -> list[dict]:
        if source.get("source_type") != "static":
            raise ValueError("Phase 1 supports static HTML sources only.")
        parser_map = source.get("parser_map") or {}
        if not parser_map:
            raise ValueError("Parser source has no parser configuration.")
        products = []
        current_url = source["url"]
        visited = set()
        page_limit = max_pages(parser_map)
        for page_number in range(page_limit):
            if current_url in visited:
                raise ValueError(f"Pagination loop detected at {current_url}")
            visited.add(current_url)
            response = self.session.get(current_url, timeout=self.timeout)
            response.raise_for_status()
            for raw in parse_html(response.content, parser_map):
                name = raw.get("name")
                if not name:
                    continue
                product_url = raw.get("product_url") or raw.get("link") or raw.get("url") or ""
                products.append(
                    {
                        "name": name,
                        "description": raw.get("description") or "",
                        "product_url": urljoin(current_url, product_url) if product_url else "",
                        "price": raw.get("price"),
                        "min_price": raw.get("min_price"),
                        "max_price": raw.get("max_price"),
                        "currency": raw.get("currency") or "UAH",
                        "raw_price": str(raw.get("raw_price") or raw.get("price") or ""),
                        "raw": raw,
                    }
                )
            following_url = next_page_url(response.content, current_url, parser_map)
            if not following_url:
                break
            if page_number + 1 == page_limit:
                raise ValueError(f"Pagination exceeded configured max_pages={page_limit}.")
            current_url = following_url
        return products
