import csv
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

INDEX = "https://mainlynorfolk.info/folk/songs/index.html"


def get_soup(url):
    return BeautifulSoup(requests.get(url, timeout=30).content, "html.parser")


def find_key(pattern, text):
    m = re.search(pattern + r"\s+([^\s;,\]]+)", text)
    return m.group(1) if m and m.group(1) != "-" else ""


# every song page linked from the index
index = get_soup(INDEX)
urls = []
for a in index.select("article a[href$='.html']"):
    url = urljoin(INDEX, a["href"])
    if "/songs/" in url and not url.endswith("index.html") and url not in urls:
        urls.append(url)

with open("all_songs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["roud", "gd", "henry", "title", "version", "lyrics"])

    for i, url in enumerate(urls, 1):
        time.sleep(2)
        try:
            soup = get_soup(url)
            h1 = soup.select_one("article h1")
        except requests.RequestException as e:
            print(f"[{i}/{len(urls)}] FAILED {url}: {e}")
            continue
        if h1 is None:
            print(f"[{i}/{len(urls)}] SKIPPED {url}: no title")
            continue
        title = h1.get_text(" ", strip=True)

        # the "[ Roud 291 ; G/D 4:834 ; Henry H123 ; ... ]" line under the title
        keys = h1.find_next("p").get_text(" ", strip=True)
        roud = find_key(r"Roud", keys)
        gd = find_key(r"G/D", keys)
        henry = find_key(r"Henry", keys)

        # each <h3> after the "Lyrics" heading is one version
        lyrics_h2 = soup.find("h2", string=re.compile("Lyrics"))
        versions = lyrics_h2.find_next_siblings("h3") if lyrics_h2 else []
        if lyrics_h2 and not versions:
            versions = [lyrics_h2]  # only one version, no <h3> headings
        for n, h3 in enumerate(versions, 1):
            lines = []
            for tag in h3.find_next_siblings():
                if tag.name in ("h2", "h3"):
                    break
                lines.append(tag.get_text("\n", strip=True))
            writer.writerow([roud, gd, henry, title, n, "\n\n".join(lines).strip()])

        print(f"[{i}/{len(urls)}] {title} - Roud {roud} - {len(versions)} versions")
