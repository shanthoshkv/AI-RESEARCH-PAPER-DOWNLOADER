# Research Paper Downloader

An intelligent system for downloading and filtering research papers from legal and open-source repositories using AI-powered relevance checking with Ollama Qwen3:8B.

## Overview

This application automates the process of downloading research papers from multiple open-access repositories including arXiv, DOAJ, PubMed Central, and PLOS ONE. What makes this system unique is its integration with Ollama's Qwen3:8B model to intelligently filter papers based on relevance to your specific query.

The system downloads papers, extracts text content, and uses the Qwen3:8B language model to determine if each paper is relevant to your research query. Irrelevant papers are automatically rejected and logged, saving you time and storage space.

## Features

- **AI-Powered Filtering**: Utilizes Ollama Qwen3:8B to intelligently filter research papers based on relevance to your specific query
- **Multi-Source Discovery**: Searches across multiple academic repositories including arXiv, DOAJ, PubMed Central, and PLOS ONE
- **Privacy-First Design**: All processing happens locally on your machine with no data sent to external servers
- **Customizable Parameters**: Adjustable settings for page extraction limits, character limits, and processing delays
- **Detailed Logging**: Comprehensive logging of rejected papers with reasons for transparency
- **Organized Storage**: Automatically organizes downloaded papers into folders by query

## System Architecture

1. **Query Input**: User submits research query for paper discovery
2. **Source Search**: Query multiple academic repositories simultaneously
3. **Download & Extract**: Retrieve PDFs and extract text content
4. **AI Relevance Check**: Ollama Qwen3:8B analyzes paper relevance
5. **Filter & Save**: Organize relevant papers, reject irrelevant ones

## Technology Stack

### Core Language & Libraries
- **Python**: Primary programming language
- **Requests**: HTTP library for API calls and file downloads
- **BeautifulSoup**: HTML/XML parsing for extracting data from repository APIs
- **PyPDF2**: PDF text extraction

### AI & Machine Learning
- **Ollama Qwen3:8B**: Advanced language model for relevance checking and content analysis

### Research Sources
- **arXiv API**: Scientific papers across multiple disciplines
- **DOAJ API**: Directory of Open Access Journals
- **PubMed Central**: Free full-text archive of biomedical literature
- **PLOS ONE API**: Open access scientific publications

## Installation

1. Install Ollama from [https://ollama.com/](https://ollama.com/)
2. Pull the Qwen3:8B model:
   ```bash
   ollama pull qwen3:8b
