# Research Paper Downloader

Bulk-downloads open-access research papers for a query and uses a local LLM to throw out the ones that aren't actually relevant.

## Overview

Point it at a query like `"rocket engine injector"` and it hits four open-access sources (arXiv, DOAJ, PubMed Central, PLOS ONE), downloads every PDF it can find, extracts the first few pages of text, and asks a local Ollama model ("is this paper relevant to the query, yes or no") before keeping the file. Anything rejected gets deleted and logged with a reason instead of just piling up in a folder.

Everything runs locally except the actual paper downloads, which hit public APIs. No API keys, no accounts, no data sent to a third-party LLM. The relevance check is the whole point: a plain keyword search on any of these sources returns a lot of near-misses (same terms, wrong domain), and reading the abstract of every hit by hand doesn't scale past a handful of queries.

## Architecture

One script, no classes, just functions, called in this order per query:

```
search_arxiv / search_doaj / search_pmc / search_plos
        |  returns [{title, pdf_url}, ...]
        v
   download_file(pdf_url)          -- browser UA + 60s timeout, one retry on arXiv /abs/ -> /pdf/
        |
        v
   extract_pdf_text(pdf)           -- PyPDF2, first 5 pages, truncated to 5000 chars
        |
        v
   check_relevance_with_llm(query, title, text)   -- POST to localhost:11434/api/generate (Ollama)
        |
   YES ----------------------------------- NO
    |                                       |
   kept in Research Papers/<query>/    deleted, reason appended to
                                        Rejection Logs/rejections_<query>.txt
```

### Function reference

| Function | Source | Pagination |
|---|---|---|
| `search_arxiv` | arXiv API | batches of 100, up to `max_results` (default 1000) |
| `search_doaj` | DOAJ API | up to 50 pages |
| `search_pmc` | PubMed Central | flat `max_results` |
| `search_plos` | PLOS ONE | flat `max_results` |
| `search_core` | CORE API | stub, commented out of the source list, CORE needs an API key this repo doesn't have |

- `download_file` uses a browser User-Agent because a lot of these endpoints block the default `requests` UA outright.
- `check_relevance_with_llm` defaults to "not relevant" on any error (timeout, malformed model response, Ollama not running) rather than silently keeping a file it couldn't actually check.
- If text extraction fails on a PDF (scanned image, malformed file, no extractable text layer), the file is kept rather than dropped, since there's no way to check relevance without text and the failure mode of a scanned paper isn't "irrelevant."
- `download_papers` is the orchestrator: makes a subfolder per query, downloads, checks relevance, deletes rejects, appends rejection reasons to a per-query log.

## Installation

```bash
git clone https://github.com/shanthoshkv/AI-RESEARCH-PAPER-DOWNLOADER
cd AI-RESEARCH-PAPER-DOWNLOADER
pip install -r requirements.txt
pip install lxml   # required by search_arxiv's XML parser, missing from requirements.txt, see Known Issues
```

You also need Ollama running locally with the model pulled:

```bash
# install Ollama from https://ollama.com/
ollama pull qwen3:8b
ollama serve
```

## Usage

Edit the config block at the bottom of `research_paper_downloader.py`:

```python
QUERIES = [
    "rocket engine injector",
    "regen cooling",
]
BASE_DOWNLOAD_FOLDER = r"Research Papers"
REJECTION_LOG_FOLDER = r"Rejection Logs"
```

Then run:

```bash
python research_paper_downloader.py
```

| Output | Location | Naming |
|---|---|---|
| Kept papers | `Research Papers/<query>/` | `<Source>_<index>_<title>.pdf` |
| Rejections | `Rejection Logs/rejections_<query>.txt` | one line per rejected/failed download, with reason |

There's a default `max_results=1000` on the arXiv search and no cap on DOAJ beyond its own pagination limit, so a broad query can mean hundreds of downloads and LLM relevance checks. Narrow the query if you just want a handful of papers, or expect a long first run.

## Known issues

- `requirements.txt` lists `os`, `urllib`, `time`, `re`, and `json` as dependencies. These are Python stdlib modules and don't need to be (and in some cases can't be) installed via pip. The real third-party dependencies are `requests`, `beautifulsoup4`, and `PyPDF2`.
- `search_arxiv` parses the response with `BeautifulSoup(response.content, 'xml')`, which requires `lxml`. `lxml` isn't listed in `requirements.txt`, so a clean `pip install -r requirements.txt` will fail on arXiv search unless installed separately.
- No retry/backoff beyond the one arXiv URL-format fallback. A flaky connection just gets logged as a failed download, not retried.
- Rate limiting is a flat `time.sleep()` between requests, not adaptive to each API's actual rate limit.
- `search_core` is dead code as shipped (needs a key this repo doesn't provide), left in for anyone who wants to wire in their own CORE API key.

## Requirements

- Python 3.x
- Ollama running locally with `qwen3:8b` (or another model, change the `model` argument in `check_relevance_with_llm`)
- `requests`, `beautifulsoup4`, `lxml`, `PyPDF2`
