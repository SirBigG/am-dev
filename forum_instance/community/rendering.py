import re
import json
from urllib.parse import urlparse

from django.conf import settings
from django.utils.html import escape, urlize, strip_tags
from django.utils.safestring import mark_safe


def render_publication_body(value):
    """Render the editor's small, explicitly allowlisted block syntax."""
    try:
        document = json.loads(value)
    except (TypeError, ValueError):
        document = None
    if isinstance(document, dict) and isinstance(document.get("blocks"), list):
        rendered = []
        for block in document["blocks"]:
            kind, data = block.get("type"), block.get("data", {})
            text = escape(strip_tags(str(data.get("text", ""))))
            if kind == "paragraph": rendered.append(f"<p>{urlize(text)}</p>")
            elif kind == "header" and int(data.get("level", 2)) in {2, 3}: rendered.append(f"<h{int(data.get('level', 2))}>{text}</h{int(data.get('level', 2))}>")
            elif kind == "quote": rendered.append(f"<blockquote>{text}</blockquote>")
            elif kind == "delimiter": rendered.append("<hr>")
            elif kind == "list":
                style = "ol" if data.get("style") == "ordered" else "ul"
                items = data.get("items", [])
                rendered.append(f"<{style}>" + "".join(f"<li>{escape(strip_tags(str(item.get('content', '') if isinstance(item, dict) else item)))}</li>" for item in items) + f"</{style}>")
            elif kind == "image":
                file_data = data.get("file", {}); image_url = str(file_data.get("url", "")); caption = escape(strip_tags(str(data.get("caption", ""))))
                if urlparse(image_url).scheme in {"http", "https"} or image_url.startswith(settings.MEDIA_URL):
                    rendered.append(f'<figure><img src="{escape(image_url)}" alt="{caption}" loading="lazy"><figcaption>{caption}</figcaption></figure>')
        return mark_safe("".join(rendered))
    lines = value.replace("\r\n", "\n").split("\n")
    html, paragraph, items, list_type = [], [], [], None

    def flush_paragraph():
        if paragraph:
            html.append(f"<p>{urlize(escape(' '.join(paragraph)))}</p>")
            paragraph.clear()

    def flush_list():
        nonlocal list_type
        if items:
            html.append(f"<{list_type}>" + "".join(f"<li>{urlize(escape(item))}</li>" for item in items) + f"</{list_type}>")
            items.clear()
        list_type = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph(); flush_list(); continue
        if line == "---":
            flush_paragraph(); flush_list(); html.append("<hr>"); continue
        image = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
        image_url = image.group(2) if image else ""
        safe_image = urlparse(image_url).scheme in {"http", "https"} or image_url.startswith(settings.MEDIA_URL)
        if image and safe_image:
            flush_paragraph(); flush_list()
            html.append(f'<figure><img src="{escape(image.group(2))}" alt="{escape(image.group(1))}" loading="lazy"><figcaption>{escape(image.group(1))}</figcaption></figure>')
            continue
        if line.startswith("## "):
            flush_paragraph(); flush_list(); html.append(f"<h2>{escape(line[3:])}</h2>"); continue
        if line.startswith("### "):
            flush_paragraph(); flush_list(); html.append(f"<h3>{escape(line[4:])}</h3>"); continue
        if line.startswith("> "):
            flush_paragraph(); flush_list(); html.append(f"<blockquote>{urlize(escape(line[2:]))}</blockquote>"); continue
        bullet = re.match(r"^[-*] (.+)$", line)
        numbered = re.match(r"^\d+\. (.+)$", line)
        if bullet or numbered:
            flush_paragraph()
            wanted = "ul" if bullet else "ol"
            if list_type and list_type != wanted: flush_list()
            list_type = wanted; items.append((bullet or numbered).group(1)); continue
        flush_list(); paragraph.append(line)
    flush_paragraph(); flush_list()
    return mark_safe("".join(html))
