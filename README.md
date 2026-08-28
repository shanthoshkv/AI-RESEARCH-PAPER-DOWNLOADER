# Research Paper Downloader

Bulk-downloads open-access research papers for a query and uses a local LLM to throw out the ones that aren't actually relevant.

## What it does

Point it at a query like `"rocket engine injector"` and it hits four open-access sources (arXiv, DOAJ, PubMed Central, PLOS ONE), downloads every PDF it can find, extracts the first few pages of text, and asks a local Ollama model ("is this paper relevant to the query, yes or no") before keeping the file. Anything rejected gets deleted and logged with a reason instead of just piling up in a folder.

Everything runs locally except the actual paper downloads, which hit public APIs. No API keys, no accounts, no data sent to a third-party LLM.

## How it works

`research_paper_downloader.py` is one script, no classes, just functions:

- `search_arxiv`, `search_doaj`, `search_pmc`, `search_plos` — each hits its source's public API/search endpoint and returns `[{title, pdf_url}, ...]`. arXiv paginates in batches of 100 up to `max_results` (default 1000); DOAJ paginates up to 50 pages; PMC and PLOS take a flat `max_results`.
- `search_core` exists but is a stub — CORE's article search needs an API key, so it's commented out of the source list in `download_papers` and just returns `[]` if called directly.
- `download_file` fetches each PDF with a browser User-Agent (a lot of these endpoints block the default `requests` UA) and a 60s timeout. If it's an arXiv `/abs/` link that failed, it retries once against the `/pdf/` variant.
- `extract_pdf_text` reads the first 5 pages via PyPDF2 and truncates to 5000 characters, just enough for the relevance prompt without shipping the whole paper to the model.
- `check_relevance_with_llm` posts the query, title, and text excerpt to `http://localhost:11434/api/generate` (Ollama's local API) and expects a bare `YES`/`NO` back. Any error here defaults to "not relevant" rather than silently keeping garbage.
- `download_papers` orchestrates all of the above per query: makes a subfolder per query, downloads, checks relevance, deletes rejects, and appends rejection reasons to a log file per query.

If text extraction fails on a PDF (scanned image, malformed file, etc.) the file is kept rather than dropped, since there's no way to check relevance without text.

## Installation

```bash
git clone https://github.com/shanthoshkv/AI-RESEARCH-PAPER-DOWNLOADER
cd AI-RESEARCH-PAPER-DOWNLOADER
pip install -r requirements.txt
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

Papers land in `Research Papers/<query>/`, named `<Source>_<index>_<title>.pdf`. Rejections (both "downloaded but not relevant" and "download failed") go to `Rejection Logs/rejections_<query>.txt` with the reason.

There's a default `max_results=1000` on the arXiv search and no cap on DOAJ beyond its own pagination limit, so a broad query can mean hundreds of downloads and LLM relevance checks. Narrow the query if you just want a handful of papers.

## Known issues

- `requirements.txt` lists `os`, `urllib`, `time`, `re`, and `json` as dependencies — these are all Python stdlib modules and don't need to be (and in some cases can't be) installed via pip. The only real third-party dependencies are `requests`, `beautifulsoup4`, and `PyPDF2`.
- `search_arxiv` parses the response with `BeautifulSoup(response.content, 'xml')`, which requires `lxml` to be installed. `lxml` isn't listed in `requirements.txt`, so a clean `pip install -r requirements.txt` will fail on arXiv search unless you install it separately (`pip install lxml`).
- No retry/backoff beyond the one arXiv URL-format fallback — a flaky connection just gets logged as a failed download, not retried.
- Rate limiting is a flat `time.sleep()` between requests, not adaptive to each API's actual limits.

## Requirements

- Python 3.x
- Ollama running locally with `qwen3:8b` (or another model — change the `model` argument in `check_relevance_with_llm`)
- `requests`, `beautifulsoup4`, `lxml`, `PyPDF2`
