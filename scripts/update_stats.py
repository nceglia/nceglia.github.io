#!/usr/bin/env python3
"""Refresh assets/stats.json and assets/publications.json with live metrics.

Sources:
  - Google Scholar  -> headline citations / h-index / i10-index, per-paper
                       counts, and the full publication list
  - GitHub API      -> repository stars
  - pypistats.org   -> PyPI downloads (last month)

Designed to FAIL SOFT: if any source errors (e.g. Scholar rate-limits or blocks
the CI runner), the previously stored value/file is kept rather than overwritten.

Run locally with `python3 scripts/update_stats.py`, or on a schedule via
.github/workflows/update-stats.yml. Pure standard library — no pip installs.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_PATH = os.path.join(ROOT, "assets", "stats.json")
PUBS_PATH = os.path.join(ROOT, "assets", "publications.json")

SCHOLAR_ID = "2GJlykYAAAAJ"
# Scholar lists up to 100 papers per page; bump with pagination if the
# profile ever exceeds that.
SCHOLAR_URL = (
    "https://scholar.google.com/citations?user=%s&hl=en&cstart=0&pagesize=100" % SCHOLAR_ID
)

# slug -> lowercase substring that uniquely identifies the paper's Scholar title
PAPER_KEYWORDS = {
    "tcri": "tcri: information",
    "genevector": "with genevector",
    "neoantigen-prime": "neoantigen vaccines prime",
    "ovarian-evasion": "ovarian cancer mutational",
    "circadiomics": "circadiomics: circadian omic web",
}
REPOS = ["nceglia/tcri", "nceglia/genevector"]
PYPI_PACKAGES = ["genevector"]

UA = "Mozilla/5.0 (compatible; nceglia-site-stats/1.0; +https://nceglia.github.io)"
SCHOLAR_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "ignore")


def _get_json(url, headers=None):
    return json.loads(_get(url, headers))


def _strip(s):
    return html.unescape(re.sub("<[^>]*>", "", s)).strip()


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def fetch_scholar_page():
    page = _get(SCHOLAR_URL, headers={"User-Agent": SCHOLAR_UA})
    if "gsc_rsb_std" not in page and "gsc_a_tr" not in page:
        raise RuntimeError("Scholar response missing expected markup (blocked or layout change)")
    return page


def update_scholar(stats, page):
    # Summary table: citations(all), citations(since), h(all), h(since), i10(all), i10(since)
    nums = [int(x) for x in re.findall(r'class="gsc_rsb_std">(\d+)<', page)]
    sc = stats.setdefault("scholar", {})
    sc["id"] = SCHOLAR_ID
    if len(nums) >= 5:
        sc["citations"], sc["h_index"], sc["i10_index"] = nums[0], nums[2], nums[4]

    # Per-paper citation counts for the curated fallback cards
    parsed = []
    for row in page.split('class="gsc_a_tr"')[1:]:
        title_m = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', row)
        cite_m = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)<', row)
        if title_m:
            parsed.append((_strip(title_m.group(1)).lower(), int(cite_m.group(1)) if cite_m else 0))
    papers = stats.setdefault("papers", {})
    for slug, keyword in PAPER_KEYWORDS.items():
        match = next((count for (title, count) in parsed if keyword in title), None)
        if match is not None:
            papers[slug] = match


def parse_publications(page):
    pubs = []
    for row in page.split('class="gsc_a_tr"')[1:]:
        title_m = re.search(r'<a [^>]*class="gsc_a_at"[^>]*>(.*?)</a>', row)
        href_m = re.search(r'<a href="([^"]*)"[^>]*class="gsc_a_at"', row)
        grays = re.findall(r'class="gs_gray">(.*?)</div>', row)
        cite_m = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d*)<', row)
        year_m = re.search(r'class="gsc_a_h[^"]*"[^>]*>(\d{4})<', row)
        if not title_m:
            continue
        pubs.append({
            "title": _strip(title_m.group(1)),
            "authors": _strip(grays[0]) if len(grays) >= 1 else "",
            "venue": _strip(grays[1]) if len(grays) >= 2 else "",
            "year": int(year_m.group(1)) if year_m else None,
            "citations": int(cite_m.group(1)) if (cite_m and cite_m.group(1)) else 0,
            "url": ("https://scholar.google.com" + href_m.group(1)) if href_m else "",
        })
    if not pubs:
        raise RuntimeError("No publications parsed")
    return pubs


def update_github(stats):
    gh = stats.setdefault("github", {})
    errors = []
    for repo in REPOS:
        try:
            gh[repo] = _get_json("https://api.github.com/repos/%s" % repo).get(
                "stargazers_count", gh.get(repo)
            )
        except Exception as e:
            errors.append("%s (%s)" % (repo, e))
    if errors:
        raise RuntimeError("; ".join(errors))


def update_pypi(stats):
    pypi = stats.setdefault("pypi", {})
    errors = []
    for pkg in PYPI_PACKAGES:
        try:
            data = _get_json("https://pypistats.org/api/packages/%s/recent" % pkg).get("data", {})
            if data.get("last_month") is not None:
                pypi[pkg] = data["last_month"]
        except Exception as e:
            errors.append("%s (%s)" % (pkg, e))
    if errors:
        raise RuntimeError("; ".join(errors))


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    today = datetime.date.today().isoformat()
    stats = load_json(STATS_PATH)

    page = None
    try:
        page = fetch_scholar_page()
    except Exception as e:
        print("scholar  FETCH FAILED: %s -- keeping previous values" % e, file=sys.stderr)

    if page:
        try:
            update_scholar(stats, page)
            print("scholar  ok")
        except Exception as e:
            print("scholar  FAILED: %s" % e, file=sys.stderr)
        try:
            pubs = parse_publications(page)
            write_json(PUBS_PATH, {"updated": today, "count": len(pubs), "papers": pubs})
            print("pubs     ok (%d)" % len(pubs))
        except Exception as e:
            print("pubs     FAILED: %s -- keeping previous file" % e, file=sys.stderr)

    for name, fn in [("github", update_github), ("pypi", update_pypi)]:
        try:
            fn(stats)
            print("%-8s ok" % name)
        except Exception as e:
            print("%-8s FAILED: %s -- keeping previous values" % (name, e), file=sys.stderr)

    stats["updated"] = today
    write_json(STATS_PATH, stats)
    print("wrote", STATS_PATH)


if __name__ == "__main__":
    main()
