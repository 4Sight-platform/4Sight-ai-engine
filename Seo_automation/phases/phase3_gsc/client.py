"""
GSC API Client - Complete Data Fetching
Wrapper for Google Search Console API operations
"""

from googleapiclient.discovery import build
import httplib2
from datetime import datetime, timedelta

class GSCClient:
    """Client for interacting with Google Search Console API"""
    
    def __init__(self, credentials):
        """
        Initialize GSC client with credentials
        
        Args:
            credentials: OAuth2 credentials object
        """
        self.credentials = credentials
        self.service = self._build_service()
    
    def _build_service(self):
        """Build the GSC API service"""
        try:
            http = self.credentials.authorize(httplib2.Http())
            service = build('webmasters', 'v3', http=http)
            return service
        except Exception as e:
            raise ValueError(f"Failed to build GSC service: {str(e)}")
    
    # ========================================================================
    # 1. PROPERTIES
    # ========================================================================
    
    def list_properties(self):
        """
        List all GSC properties the user has access to
        
        Returns:
            list: List of property URLs
        """
        try:
            site_list = self.service.sites().list().execute()
            properties = []
            
            if 'siteEntry' in site_list:
                properties = [site['siteUrl'] for site in site_list['siteEntry']]
            
            return properties
        
        except Exception as e:
            print(f"Debug - Error listing properties: {str(e)}")
            print(f"Debug - Service type: {type(self.service)}")
            print(f"Debug - Service attributes: {dir(self.service)}")
            raise ValueError(f"Failed to list properties: {str(e)}")
    
    # ========================================================================
    # 2. KEYWORD PERFORMANCE (Specific Keywords)
    # ========================================================================
    
    def query_keyword(self, site_url, keyword, start_date=None, end_date=None):
        """
        Query performance data for a specific keyword
        
        Args:
            site_url: The GSC property URL
            keyword: The keyword to query
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            dict: Performance metrics or None if no data
        """
        # Set default date range (last 90 days)
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query"],
            "dimensionFilterGroups": [{
                "filters": [{
                    "dimension": "query",
                    "operator": "equals",
                    "expression": keyword
                }]
            }],
            "rowLimit": 1
        }
        
        try:
            response = self.service.searchanalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' in response and len(response['rows']) > 0:
                row = response['rows'][0]
                return {
                    "keyword": keyword,
                    "impressions": row.get('impressions', 0),
                    "clicks": row.get('clicks', 0),
                    "ctr": round(row.get('ctr', 0) * 100, 2),
                    "position": round(row.get('position', 0), 1)
                }
            else:
                # No data found - keyword doesn't rank
                return {
                    "keyword": keyword,
                    "impressions": 0,
                    "clicks": 0,
                    "ctr": 0.0,
                    "position": None
                }
        
        except Exception as e:
            raise ValueError(f"Failed to query keyword '{keyword}': {str(e)}")
    
    def batch_query_keywords(self, site_url, keywords, start_date=None, end_date=None):
        """
        Query performance data for multiple keywords
        
        Args:
            site_url: The GSC property URL
            keywords: List of keywords to query
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            dict: Mapping of keyword to performance metrics
        """
        results = {}
        
        for keyword in keywords:
            try:
                result = self.query_keyword(site_url, keyword, start_date, end_date)
                results[keyword] = result
            except Exception as e:
                print(f"Error querying '{keyword}': {str(e)}")
                results[keyword] = None
        
        return results
    
    # ========================================================================
    # 3. TOP QUERIES (All Keywords Site Ranks For)
    # ========================================================================
    
    def get_top_queries(self, site_url, limit=100, start_date=None, end_date=None):
        """
        Get top performing queries for a site
        
        Args:
            site_url: The GSC property URL
            limit: Number of queries to return (max 25000)
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            list: Top queries with performance metrics
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query"],
            "rowLimit": limit
        }
        
        try:
            response = self.service.searchanalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' in response:
                queries = []
                for row in response['rows']:
                    queries.append({
                        "keyword": row['keys'][0],
                        "impressions": row.get('impressions', 0),
                        "clicks": row.get('clicks', 0),
                        "ctr": round(row.get('ctr', 0) * 100, 2),
                        "position": round(row.get('position', 0), 1)
                    })
                return queries
            else:
                return []
        
        except Exception as e:
            raise ValueError(f"Failed to get top queries: {str(e)}")
    
    # ========================================================================
    # 4. TOP PAGES (Which Pages Get Traffic)
    # ========================================================================
    
    def get_top_pages(self, site_url, limit=50, start_date=None, end_date=None):
        """
        Get top performing pages for a site
        
        Args:
            site_url: The GSC property URL
            limit: Number of pages to return
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            list: Top pages with performance metrics
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["page"],
            "rowLimit": limit
        }
        
        try:
            response = self.service.searchAnalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' in response:
                pages = []
                for row in response['rows']:
                    pages.append({
                        "url": row['keys'][0],
                        "impressions": row.get('impressions', 0),
                        "clicks": row.get('clicks', 0),
                        "ctr": round(row.get('ctr', 0) * 100, 2),
                        "position": round(row.get('position', 0), 1)
                    })
                return pages
            else:
                return []
        
        except Exception as e:
            raise ValueError(f"Failed to get top pages: {str(e)}")
    
    # ========================================================================
    # 5. PERFORMANCE BY COUNTRY
    # ========================================================================
    
    def get_performance_by_country(self, site_url, limit=20, start_date=None, end_date=None):
        """
        Get performance breakdown by country
        
        Args:
            site_url: The GSC property URL
            limit: Number of countries to return
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            list: Performance metrics per country
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["country"],
            "rowLimit": limit
        }
        
        try:
            response = self.service.searchAnalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' in response:
                countries = []
                for row in response['rows']:
                    countries.append({
                        "country": row['keys'][0],
                        "impressions": row.get('impressions', 0),
                        "clicks": row.get('clicks', 0),
                        "ctr": round(row.get('ctr', 0) * 100, 2),
                        "position": round(row.get('position', 0), 1)
                    })
                return countries
            else:
                return []
        
        except Exception as e:
            raise ValueError(f"Failed to get country performance: {str(e)}")
    
    # ========================================================================
    # 6. PERFORMANCE BY DEVICE
    # ========================================================================
    
    def get_performance_by_device(self, site_url, start_date=None, end_date=None):
        """
        Get performance breakdown by device type
        
        Args:
            site_url: The GSC property URL
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            list: Performance metrics per device (MOBILE, DESKTOP, TABLET)
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["device"]
        }
        
        try:
            response = self.service.searchAnalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' in response:
                devices = []
                for row in response['rows']:
                    devices.append({
                        "device": row['keys'][0],
                        "impressions": row.get('impressions', 0),
                        "clicks": row.get('clicks', 0),
                        "ctr": round(row.get('ctr', 0) * 100, 2),
                        "position": round(row.get('position', 0), 1)
                    })
                return devices
            else:
                return []
        
        except Exception as e:
            raise ValueError(f"Failed to get device performance: {str(e)}")
    
    # ========================================================================
    # 7. TIME-SERIES DATA (Daily Trends)
    # ========================================================================
    
    def get_performance_over_time(self, site_url, start_date=None, end_date=None):
        """
        Get daily performance data over time
        
        Args:
            site_url: The GSC property URL
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            list: Daily performance metrics
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["date"],
            "rowLimit": 25000
        }
        
        try:
            response = self.service.searchAnalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' in response:
                timeline = []
                for row in response['rows']:
                    timeline.append({
                        "date": row['keys'][0],
                        "impressions": row.get('impressions', 0),
                        "clicks": row.get('clicks', 0),
                        "ctr": round(row.get('ctr', 0) * 100, 2),
                        "position": round(row.get('position', 0), 1)
                    })
                return timeline
            else:
                return []
        
        except Exception as e:
            raise ValueError(f"Failed to get time-series data: {str(e)}")
    
    # ========================================================================
    # 8. SITEMAP STATUS
    # ========================================================================
    
    def get_sitemap_status(self, site_url):
        """
        Get sitemap health and status
        
        Args:
            site_url: The GSC property URL
            
        Returns:
            list: Sitemap information
        """
        try:
            response = self.service.sitemaps().list(siteUrl=site_url).execute()
            
            if 'sitemap' in response:
                sitemaps = []
                for sm in response['sitemap']:
                    sitemap_data = {
                        "path": sm.get('path'),
                        "last_submitted": sm.get('lastSubmitted'),
                        "last_downloaded": sm.get('lastDownloaded'),
                        "is_pending": sm.get('isPending', False),
                        "is_index": sm.get('isSitemapsIndex', False),
                        "warnings": int(sm.get('warnings', 0)),
                        "errors": int(sm.get('errors', 0)),
                        "contents": sm.get('contents', [])
                    }
                    sitemaps.append(sitemap_data)
                return sitemaps
            else:
                return []
        
        except Exception as e:
            raise ValueError(f"Failed to get sitemap status: {str(e)}")
    
    # ========================================================================
    # 9. URL INSPECTION (Individual Page Status)
    # ========================================================================
    
    def inspect_url(self, site_url, inspection_url):
        """
        Inspect a specific URL for indexing status
        
        Note: URL Inspection API requires separate 'searchconsole' v1 service
        
        Args:
            site_url: The GSC property URL
            inspection_url: The specific URL to inspect
            
        Returns:
            dict: Indexing and crawl status
        """
        try:
            # URL Inspection uses different API (searchconsole v1, not webmasters v3)
            http = self.credentials.authorize(httplib2.Http())
            inspection_service = build('searchconsole', 'v1', http=http)
            
            request_body = {
                "inspectionUrl": inspection_url,
                "siteUrl": site_url
            }
            
            response = inspection_service.urlInspection().index().inspect(
                body=request_body
            ).execute()
            
            inspection_result = response.get('inspectionResult', {})
            index_status = inspection_result.get('indexStatusResult', {})
            mobile_usability = inspection_result.get('mobileUsabilityResult', {})
            
            return {
                "url": inspection_url,
                "verdict": index_status.get('verdict'),
                "coverage_state": index_status.get('coverageState'),
                "indexing_state": index_status.get('indexingState'),
                "page_fetch_state": index_status.get('pageFetchState'),
                "robots_txt_state": index_status.get('robotsTxtState'),
                "last_crawl_time": index_status.get('lastCrawlTime'),
                "google_canonical": index_status.get('googleCanonical'),
                "user_canonical": index_status.get('userCanonical'),
                "mobile_friendly": mobile_usability.get('verdict') == 'PASS',
                "mobile_issues": mobile_usability.get('issues', [])
            }
        
        except Exception as e:
            raise ValueError(f"Failed to inspect URL: {str(e)}")
    
    # ========================================================================
    # 10. COMPLETE DATA FETCH (All Data at Once)
    # ========================================================================
    
    def fetch_complete_data(self, site_url, keywords=None, start_date=None, end_date=None):
        """
        Fetch ALL available GSC data for a property
        
        Args:
            site_url: The GSC property URL
            keywords: Optional list of specific keywords to check
            start_date: Start date (defaults to 90 days ago)
            end_date: End date (defaults to today)
            
        Returns:
            dict: Complete dataset with all metrics
        """
        print("Fetching complete GSC data...")
        
        data = {
            "site_url": site_url,
            "fetch_date": datetime.now().isoformat(),
            "date_range": {
                "start": (start_date or (datetime.now().date() - timedelta(days=90))).isoformat(),
                "end": (end_date or datetime.now().date()).isoformat()
            }
        }
        
        # 1. Keyword performance (if specific keywords provided)
        if keywords:
            print("  → Fetching keyword performance...")
            data["keyword_performance"] = self.batch_query_keywords(site_url, keywords, start_date, end_date)
        
        # 2. Top queries
        print("  → Fetching top 100 queries...")
        data["top_queries"] = self.get_top_queries(site_url, limit=100, start_date=start_date, end_date=end_date)
        
        # 3. Top pages
        print("  → Fetching top 50 pages...")
        data["top_pages"] = self.get_top_pages(site_url, limit=50, start_date=start_date, end_date=end_date)
        
        # 4. Country performance
        print("  → Fetching country breakdown...")
        data["countries"] = self.get_performance_by_country(site_url, limit=20, start_date=start_date, end_date=end_date)
        
        # 5. Device performance
        print("  → Fetching device breakdown...")
        data["devices"] = self.get_performance_by_device(site_url, start_date=start_date, end_date=end_date)
        
        # 6. Time-series data
        print("  → Fetching daily trends...")
        data["timeline"] = self.get_performance_over_time(site_url, start_date=start_date, end_date=end_date)
        
        # 7. Sitemap status
        print("  → Fetching sitemap status...")
        data["sitemaps"] = self.get_sitemap_status(site_url)
        
        print("✓ Complete data fetch finished!")
        
        return data