from agromega_parser_studio.parser import StaticSourceRunner, extract_price, parse_html


def test_item_scoped_parser_preserves_missing_optional_price():
    products = parse_html(
        ("<section><article><h2>Golden</h2><span>42,50 грн</span></article><article><h2>Gala</h2></article></section>"),
        {"item": "//article", "name": ".//h2/text()", "price": ".//span/text()"},
    )

    assert products == [{"name": "Golden", "price": 42.5}, {"name": "Gala", "price": None}]


def test_price_normalization_supports_ukrainian_format():
    assert extract_price("1 234,56 грн") == 1234.56


def test_static_runner_uses_source_friendly_request_headers():
    runner = StaticSourceRunner()

    assert "AgroMegaParser" in runner.session.headers["User-Agent"]
    assert runner.session.headers["Accept-Language"].startswith("uk-UA")


class FakeResponse:
    content = b'<article><h2>Golden</h2><a href="/golden">Open</a></article>'

    @staticmethod
    def raise_for_status():
        return None


class FakeSession:
    def get(self, url, timeout):
        assert url == "https://shop.example/apples"
        assert timeout == 30
        return FakeResponse()


def test_static_runner_normalizes_relative_product_url():
    source = {
        "url": "https://shop.example/apples",
        "source_type": "static",
        "parser_map": {"item": "//article", "name": ".//h2/text()", "link": ".//a/@href"},
    }

    products = StaticSourceRunner(session=FakeSession()).preview(source)

    assert products[0]["name"] == "Golden"
    assert products[0]["product_url"] == "https://shop.example/golden"


class PaginatedResponse:
    def __init__(self, content):
        self.content = content

    @staticmethod
    def raise_for_status():
        return None


class PaginatedSession:
    def __init__(self):
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        pages = {
            "https://shop.example/apples": (
                b'<article><h2>Golden</h2><a class="product" href="/golden">Open</a></article>'
                b'<a class="next" href="/apples/page/2">Next</a>'
            ),
            "https://shop.example/apples/page/2": (
                b'<article><h2>Gala</h2><a class="product" href="/gala">Open</a></article>'
            ),
        }
        return PaginatedResponse(pages[url])


def test_static_runner_follows_configured_next_page():
    session = PaginatedSession()
    source = {
        "url": "https://shop.example/apples",
        "source_type": "static",
        "parser_map": {
            "item": "//article",
            "name": ".//h2/text()",
            "link": ".//a[contains(@class, 'product')]/@href",
            "next_page": "//a[contains(@class, 'next')]/@href",
            "max_pages": 3,
        },
    }

    products = StaticSourceRunner(session=session).preview(source)

    assert [product["name"] for product in products] == ["Golden", "Gala"]
    assert session.urls == ["https://shop.example/apples", "https://shop.example/apples/page/2"]


def test_encoding_override_handles_wrong_meta_and_pagination():
    from agromega_parser_studio.parser import next_page_url

    for encoding in ("utf-8", "windows-1251"):
        content = (
            '<meta charset="iso-8859-1"><article><h2>Яблуня Айдаред</h2></article><a href="/next">Далі</a>'
        ).encode(encoding)
        config = {
            "encoding": encoding,
            "item": "//article",
            "name": ".//h2/text()",
            "next_page": "//a[text()='Далі']/@href",
        }
        assert parse_html(content, config) == [{"name": "Яблуня Айдаред"}]
        assert next_page_url(content, "https://shop.example", config) == "https://shop.example/next"
        assert parse_html(content.decode(encoding), config) == [{"name": "Яблуня Айдаред"}]


def test_invalid_encoding_fails_explicitly():
    import pytest

    with pytest.raises(LookupError):
        parse_html(b"<p>name</p>", {"encoding": "invalid-encoding", "name": "//p/text()"})


def test_runner_applies_encoding_override_to_response_bytes():
    from unittest.mock import Mock

    session = Mock()
    session.get.return_value.content = "<article><h2>Яблуня Айдаред</h2></article>".encode("windows-1251")
    products = StaticSourceRunner(session=session).preview(
        {
            "url": "https://shop.example",
            "source_type": "static",
            "parser_map": {"encoding": "windows-1251", "item": "//article", "name": ".//h2/text()"},
        }
    )
    assert products[0]["name"] == "Яблуня Айдаред"


def test_duplicate_products_merge_but_conflicting_prices_fail():
    import pytest

    from agromega_parser_studio.parser import deduplicate_products

    product = {"product_url": "https://shop.example/apple", "name": "Apple", "price": 650}
    assert deduplicate_products([product, dict(product)]) == [product]
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        deduplicate_products([product, {**product, "price": 700}])
    assert len(deduplicate_products([product, {**product, "product_url": "https://shop.example/apple-2"}])) == 2


def test_runner_merges_repeated_cards_and_counts_them():
    from unittest.mock import Mock

    session = Mock()
    session.get.return_value.content = b'<article><h2>Apple</h2><a href="/apple">Link</a></article>' * 2
    runner = StaticSourceRunner(session=session)
    products = runner.preview(
        {
            "url": "https://shop.example",
            "source_type": "static",
            "parser_map": {"item": "//article", "name": ".//h2/text()", "link": ".//a/@href"},
        }
    )
    assert len(products) == 1
    assert runner.duplicates_removed == 1
