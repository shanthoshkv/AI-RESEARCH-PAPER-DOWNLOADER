# Contributing to Research Paper Downloader

Thanks for helping. Small, focused changes are easiest to review.

## Getting set up

```bash
git clone https://github.com/shanthoshkv/AI-RESEARCH-PAPER-DOWNLOADER
cd AI-RESEARCH-PAPER-DOWNLOADER
pip install -r requirements.txt
# also needs Ollama running locally with: ollama pull qwen3:8b
```

## Check your change

```bash
python -m py_compile research_paper_downloader.py
python -c "import research_paper_downloader"   # confirms dependencies import; no test suite exists yet
```

## Pull requests

1. Open an issue first for anything bigger than a bug fix or doc tweak.
2. Branch from `main`, keep the diff small, one concern per PR.
3. Make sure the check above passes and CI is green.
4. Describe what changed and why. Add a line to `CHANGELOG.md` under **Unreleased** for user-visible changes.

## Good first issues

Look for the [`good first issue`](https://github.com/shanthoshkv/AI-RESEARCH-PAPER-DOWNLOADER/labels/good%20first%20issue) label. Comment on one to claim it.

## Questions

Use [Discussions](https://github.com/shanthoshkv/AI-RESEARCH-PAPER-DOWNLOADER/discussions) for questions and ideas, Issues for bugs and concrete requests.

By contributing you agree your work is released under this repository's license.
