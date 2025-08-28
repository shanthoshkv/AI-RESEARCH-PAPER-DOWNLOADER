import os
import requests
from urllib.parse import urljoin, quote_plus, urlencode
from bs4 import BeautifulSoup
import time
import re
import json
import PyPDF2

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)

def sanitize_filename(filename):
    """Remove invalid characters and clean up filename"""
    # Remove newlines, tabs, and other control characters
    filename = re.sub(r'[\n\r\t]', ' ', filename)
    # Remove invalid file characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Limit length and strip whitespace
    return filename.strip()[:150]

def download_file(url, filepath, headers=None):
    """Download file from URL with error handling"""
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True, filepath
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False, None

def extract_pdf_text(filepath):
    """Extract text content from PDF file"""
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            # Extract first few pages for relevance check (avoid huge files)
            pages_to_read = min(5, len(pdf_reader.pages))
            for page_num in range(pages_to_read):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            return text[:5000]  # Limit text size for LLM processing
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def check_relevance_with_llm(query, title, pdf_text, model="qwen3:8b"):
    """Check if PDF is relevant to query using Ollama LLM"""
    try:
        # Prepare prompt for LLM
        prompt = f"""
        Query: {query}
        Paper Title: {title}
        Paper Content (excerpt): {pdf_text[:2000]}...
        
        Based on the query and the paper title and content, is this paper relevant to the query?
        Answer ONLY with "YES" if relevant or "NO" if not relevant.
        """
        
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        answer = result.get('response', '').strip().upper()
        
        return answer == "YES"
        
    except Exception as e:
        print(f"Error checking relevance with LLM: {e}")
        return False  # Default to not relevant if LLM check fails

def log_rejection(rejection_log_path, filename, query, url, reason):
    """Log rejected papers to a text file"""
    try:
        with open(rejection_log_path, 'a', encoding='utf-8') as f:
            f.write(f"Filename: {filename}\n")
            f.write(f"Query: {query}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Reason: {reason}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        print(f"Error logging rejection: {e}")

def search_arxiv(query, max_results=None):
    """Search arXiv for papers - fetch all available"""
    search_query = quote_plus(query)
    
    if max_results is None:
        max_results = 1000
    
    papers = []
    start = 0
    batch_size = 100
    
    while len(papers) < max_results:
        remaining = max_results - len(papers)
        current_batch = min(batch_size, remaining)
        
        url = (f"http://export.arxiv.org/api/query?"
               f"search_query=all:{search_query}"
               f"&start={start}"
               f"&max_results={current_batch}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'xml')
            
            entries = soup.find_all('entry')
            if not entries:
                break
                
            for entry in entries:
                title = entry.title.text.strip()
                pdf_url = entry.find('link', {'type': 'application/pdf'})['href']
                papers.append({
                    'title': title,
                    'pdf_url': pdf_url
                })
            
            start += current_batch
            time.sleep(1)
            
            if len(entries) < current_batch:
                break
                
        except Exception as e:
            print(f"Error searching arXiv: {e}")
            break
    
    return papers[:max_results]

def search_doaj(query, max_results=None):
    """Search Directory of Open Access Journals - fetch all available"""
    search_query = quote_plus(query)
    
    papers = []
    page = 1
    page_size = 100
    
    while True:
        url = (f"https://doaj.org/api/search/articles/{search_query}?"
               f"pageSize={page_size}&page={page}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                break
                
            for item in results:
                title = item.get('bibjson', {}).get('title', 'Unknown Title')
                urls = item.get('bibjson', {}).get('link', [])
                pdf_url = None
                for link in urls:
                    if link.get('type') == 'fulltext' and link.get('url', '').endswith('.pdf'):
                        pdf_url = link['url']
                        break
                
                if pdf_url:
                    papers.append({
                        'title': title,
                        'pdf_url': pdf_url
                    })
            
            if len(results) < page_size:
                break
                
            page += 1
            time.sleep(1)
            
            if page > 50:
                break
                
        except Exception as e:
            print(f"Error searching DOAJ: {e}")
            break
    
    return papers

def search_pmc(query, max_results=50):
    """Search PubMed Central for open access papers"""
    params = {
        'term': query,
        'retmax': max_results,
        'format': 'json'
    }
    
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{urlencode(params)}"
    
    try:
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        id_list = data.get('esearchresult', {}).get('idlist', [])
        if not id_list:
            return []
        
        # Fetch paper details
        ids = ','.join(id_list[:max_results])
        summary_params = {
            'db': 'pmc',
            'id': ids,
            'retmode': 'json'
        }
        
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{urlencode(summary_params)}"
        summary_response = requests.get(summary_url, timeout=30)
        summary_response.raise_for_status()
        summary_data = summary_response.json()
        
        papers = []
        for uid in summary_data.get('result', {}).get('uids', []):
            paper_info = summary_data['result'][uid]
            title = paper_info.get('title', 'Unknown Title')
            pmcid = paper_info.get('pmcid')
            
            if pmcid:
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                papers.append({
                    'title': title,
                    'pdf_url': pdf_url
                })
        
        return papers
        
    except Exception as e:
        print(f"Error searching PMC: {e}")
        return []

def search_plos(query, max_results=30):
    """Search PLOS ONE for open access papers"""
    search_url = "https://api.plos.org/search"
    params = {
        'q': f'title:"{query}" OR abstract:"{query}"',
        'fl': 'id,title',
        'rows': max_results,
        'wt': 'json'
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        papers = []
        for doc in data.get('response', {}).get('docs', []):
            title = doc.get('title', 'Unknown Title')
            doc_id = doc.get('id')
            
            if doc_id:
                pdf_url = f"https://journals.plos.org/plosone/article/file?id={doc_id}&type=printable"
                papers.append({
                    'title': title,
                    'pdf_url': pdf_url
                })
        
        return papers
        
    except Exception as e:
        print(f"Error searching PLOS: {e}")
        return []

def search_core(query, max_results=30):
    """Search CORE (aggregator of open access research)"""
    # Note: CORE requires API key for full access, this is limited search
    search_url = "https://core.ac.uk:443/api-v2/articles/search"
    params = {
        'q': query,
        'pageSize': max_results
    }
    
    try:
        # This is a basic implementation - CORE has better results with API key
        response = requests.get(search_url, params=params, timeout=30)
        # CORE without API key has limited functionality
        return []
        
    except Exception as e:
        print(f"Error searching CORE: {e}")
        return []

def download_papers(query, base_folder, rejection_folder):
    """Main function to download ALL papers for a query with LLM relevance checking"""
    # Create subfolder for this query
    safe_query = sanitize_filename(query)
    query_folder = os.path.join(base_folder, safe_query)
    create_directory(query_folder)
    
    # Create rejection log file
    rejection_log_path = os.path.join(rejection_folder, f"rejections_{sanitize_filename(query)}.txt")
    create_directory(rejection_folder)
    
    print(f"Searching for ALL papers related to: {query}")
    
    # Search sources
    sources = [
        ("arXiv", search_arxiv),
        ("DOAJ", search_doaj),
        ("PMC", search_pmc),
        ("PLOS", search_plos),
        # ("CORE", search_core),  # Uncomment if you get API key
    ]
    
    total_downloaded = 0
    total_rejected = 0
    
    for source_name, search_func in sources:
        print(f"\nSearching {source_name}...")
        papers = search_func(query)
        
        if not papers:
            print(f"No papers found in {source_name}")
            continue
            
        print(f"Found {len(papers)} papers from {source_name}")
        downloaded_count = 0
        rejected_count = 0
        
        for i, paper in enumerate(papers):
            title = paper.get('title', 'Unknown')
            pdf_url = paper.get('pdf_url')
            
            if not pdf_url:
                continue
                
            # Create filename
            filename = f"{source_name}_{i+1}_{sanitize_filename(title)}.pdf"
            filepath = os.path.join(query_folder, filename)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                print(f"Already exists: {filename[:50]}...")
                downloaded_count += 1
                continue
                
            # Download file temporarily
            print(f"Downloading ({i+1}/{len(papers)}): {title[:60]}...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            success = False
            temp_filepath = None
            
            # Try original URL
            download_success, temp_filepath = download_file(pdf_url, filepath, headers)
            if download_success:
                success = True
            # Try modified URL for arXiv
            elif 'arxiv.org' in pdf_url and not pdf_url.endswith('.pdf'):
                modified_url = pdf_url.replace('/abs/', '/pdf/') + '.pdf'
                download_success, temp_filepath = download_file(modified_url, filepath, headers)
                if download_success:
                    success = True
            
            if success and temp_filepath:
                # Check relevance with LLM
                print(f"Checking relevance with LLM: {title[:60]}...")
                pdf_text = extract_pdf_text(temp_filepath)
                
                if pdf_text:  # Only check if we could extract text
                    is_relevant = check_relevance_with_llm(query, title, pdf_text)
                    
                    if is_relevant:
                        downloaded_count += 1
                        print(f"✓ Saved (relevant): {filename}")
                    else:
                        # Remove irrelevant file and log rejection
                        os.remove(temp_filepath)
                        log_rejection(rejection_log_path, filename, query, pdf_url, "Not relevant to query")
                        rejected_count += 1
                        print(f"✗ Rejected (not relevant): {filename[:50]}...")
                else:
                    # Keep file if we can't extract text (assume relevant)
                    downloaded_count += 1
                    print(f"✓ Saved (text extraction failed, assuming relevant): {filename}")
            elif not success:
                print(f"✗ Failed: {title[:60]}")
                log_rejection(rejection_log_path, filename, query, pdf_url, "Download failed")
            
            time.sleep(2)  # Longer delay for LLM processing
        
        total_downloaded += downloaded_count
        total_rejected += rejected_count
        print(f"From {source_name}: {downloaded_count} downloaded, {rejected_count} rejected")
    
    print(f"\nTOTAL for '{query}': {total_downloaded} downloaded, {total_rejected} rejected")

def main():
    # USER CONFIGURATION - MODIFY THESE VALUES
    QUERIES = [
        "rocket engine injector",
        "regen cooling",
        # Add more queries here
    ]
    
    BASE_DOWNLOAD_FOLDER = r"Research Papers"  # Change this path
    REJECTION_LOG_FOLDER = r"Rejection Logs"   # Change this path
    
    # Create base folder
    create_directory(BASE_DOWNLOAD_FOLDER)
    
    # Process each query
    for query in QUERIES:
        download_papers(query, BASE_DOWNLOAD_FOLDER, REJECTION_LOG_FOLDER)
        time.sleep(5)  # Longer delay between queries

if __name__ == "__main__":
    main()