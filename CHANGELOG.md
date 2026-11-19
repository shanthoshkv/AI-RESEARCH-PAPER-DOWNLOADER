# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-11-19
### Added
- `research_paper_downloader.py`: searches arXiv, DOAJ, PubMed Central and PLOS ONE for each query and downloads the PDFs it finds.
- Relevance check: extracts the first pages of each PDF with PyPDF2 and asks a local Ollama model (`qwen3:8b`) whether it matches the query; rejected files are deleted and logged with a reason.
- Pixel-art demo GIF (`docs/demo.gif`), MIT `LICENSE`, `CONTRIBUTING.md`, issue templates and a CI workflow.

### Fixed
- `requirements.txt` listed standard-library modules (`os`, `urllib`, `time`, `re`, `json`) and omitted `lxml`; it now lists `requests`, `beautifulsoup4`, `lxml` and `PyPDF2`.
