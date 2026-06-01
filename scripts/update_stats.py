#!/usr/bin/env python3
"""Refresh assets/stats.json with live metrics.

Sources:
  - Google Scholar  -> headline citations / h-index / i10-index + per-paper counts
  - GitHub API      -> repository stars
  - pypistats.org   -> PyPI downloads (last month)

Designed to FAIL SOFT: if any source errors (e.g. Scholar rate-limits or blocks
the CI runner), the previously stored value is kept rather than overwritten.

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

SCHOLAR_ID = "2GJlykYAAAAJ"

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


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "ignore")


def _get_json(url, headers=None):
    return json.loads(_get(url, headers))


def load_stats():
    try:
        with open(STATS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def update_scholar(stats):
    page = _get(
        "https://scholar.google.com/citations?user=%s&hl=en&cstart=0&pagesize=100" % SCHOLAR_ID
    )
    if "gsc_rsb_std" not in page:
        raise RuntimeError("Scholar response missing stats table (blocked or layout change)")

    # Summary table: citations(all), citations(since), h(all), h(since), i10(all), i10(since)
    nums = [int(x) for x in re.findall(r'class="gsc_rsb_std">(\d+)<', page)]
    sc = stats.setdefault("scholar", {})
    sc["id"] = SCHOLAR_ID
    if len(nums) >= 5:
        sc["citations"], sc["h_index"], sc["i10_index"] = nums[0], nums[2], nums[4]

    # Per-paper citation counts
    parsed = []
    for row in page.split('class="gsc_a_tr"')[1:]:
        title_m = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', row)
        cite_m = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)<', row)
        if title_m:
            title = html.unescape(re.sub("<[^>]*>", "", title_m.group(1))).lower()
            parsed.append((title, int(cite_m.group(1)) if cite_m else 0))

    papers = stats.setdefault("papers", {})
    for slug, keyword in PAPER_KEYWORDS.items():
        match = next((count for (title, count) in parsed if keyword in title), None)
        if match is not None:
            papers[slug] = match


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


def main():
    stats = load_stats()
    for name, fn in [("scholar", update_scholar), ("github", update_github), ("pypi", update_pypi)]:
        try:
            fn(stats)
            print("%-8s ok" % name)
        except Exception as e:
            print("%-8s FAILED: %s -- keeping previous values" % (name, e), file=sys.stderr)

    stats["updated"] = datetime.date.today().isoformat()
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print("wrote", STATS_PATH)


if __name__ == "__main__":
    main()
