
import httpx
import asyncio
import logging
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class SiteSpider:
    """
    Minimal site spider for detecting site-wide issues:
    - Duplicate content
    - Broken links
    """
    def __init__(self, max_pages: int = 15):
        self.max_pages = max_pages
        
    async def crawl_and_analyze(self, start_url: str):
        visited = {} # url -> {status, hash, title}
        queue = [start_url]
        domain = urlparse(start_url).netloc
        
        headers = {"User-Agent": "4SightBot/1.0"}
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, headers=headers, verify=False) as client:
            while queue and len(visited) < self.max_pages:
                # Process batch of up to 5
                batch = queue[:5]
                queue = queue[5:]
                
                tasks = [self._fetch(client, url) for url in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for res in results:
                    if isinstance(res, Exception) or not res:
                        continue
                        
                    url, status, content_hash, title, links = res
                    
                    visited[url] = {
                        "status": status,
                        "hash": content_hash,
                        "title": title
                    }
                    
                    # Enqueue internal links
                    for link in links:
                        # Normalize check
                        parsed = urlparse(link)
                        if parsed.netloc == domain or parsed.netloc == "":
                            # Ensure absolute
                            full = link if parsed.netloc else urljoin(url, link)
                            if full not in visited and full not in queue:
                                queue.append(full)
        
        return self._analyze(visited)

    async def _fetch(self, client, url):
        try:
            resp = await client.get(url)
            links = []
            
            if resp.status_code >= 400:
                return (url, resp.status_code, None, None, [])
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Content Hash (Strip whitespace to be robust)
            text = soup.get_text(separator=" ", strip=True)
            content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            title = soup.title.string.strip() if soup.title else ""
            
            for a in soup.find_all('a', href=True):
                links.append(urljoin(url, a['href']))
                
            return (url, resp.status_code, content_hash, title, links)
            
        except Exception as e:
            # logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _analyze(self, visited):
        duplicates = []
        hashes = {}
        for url, data in visited.items():
            h = data['hash']
            if not h: continue
            if h in hashes:
                duplicates.append({"original": hashes[h], "duplicate": url})
            else:
                hashes[h] = url
                
        broken_links = [url for url, data in visited.items() if data['status'] and data['status'] >= 400]
        
        return {
            "pages_scanned": len(visited),
            "duplicate_content_issues": duplicates,
            "broken_links": broken_links,
            "duplicate_count": len(duplicates),
            "broken_count": len(broken_links)
        }
