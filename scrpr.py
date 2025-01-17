import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from typing import List, Dict, Optional, Tuple
import re
import logging
import os
import csv
from datetime import datetime
import sys
import platform
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StatementAnalyzer:
    def __init__(self, search_term: str):
        self.search_term = search_term
        self.driver_path = self._get_chromedriver_path()
        self.service = Service(self.driver_path)
        
        # Set up Chrome options for headless operation
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize Chrome with options
        self.driver = webdriver.Chrome(
            service=self.service,
            options=chrome_options
        )
        
        # Create timestamp for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Directory for saving evidence
        self.evidence_dir = f"statement_evidence_{self.timestamp}"
        os.makedirs(self.evidence_dir, exist_ok=True)
        
        # Stage 1: Primary identification patterns
        self.primary_patterns = [
            # Add your primary identification patterns here
            r"",
            r"",
            r""
        ]
        
        # Stage 2: Organization/grouping patterns
        self.organization_patterns = [
            # Add patterns that identify the organization/group context
            r"",
            r"",
            r""
        ]

    def _get_chromedriver_path(self) -> str:
        """
        Find the chromedriver in the script's directory, accounting for different OS platforms
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        system = platform.system().lower()
        
        driver_names = ['chromedriver.exe'] if system == 'windows' else ['chromedriver']
        
        for root, dirs, files in os.walk(script_dir):
            for driver_name in driver_names:
                if driver_name in files:
                    driver_path = os.path.join(root, driver_name)
                    logger.info(f"Found chromedriver at: {driver_path}")
                    
                    if system != 'windows':
                        try:
                            os.chmod(driver_path, 0o755)
                            logger.info("Set executable permissions for chromedriver")
                        except Exception as e:
                            logger.warning(f"Could not set executable permissions: {e}")
                    
                    return driver_path
        
        raise FileNotFoundError(
            "ChromeDriver not found. Please ensure chromedriver is in the script directory "
            "or a subdirectory. The filename should be 'chromedriver' (Unix) or "
            "'chromedriver.exe' (Windows)."
        )

    def get_page_urls(self, page: int) -> List[str]:
        """
        Get URLs from a search results page
        """
        encoded_search = self.search_term.replace(' ', '+')
        url = (f"https://www.scribd.com/search?query={encoded_search}&"
               f"ct_lang=0&filters=%7B%22new_release%22%3A%223month%22%7D&page={page}")
        
        self.driver.get(url)
        self.driver.implicitly_wait(2)
        
        elements = self.driver.find_elements(By.CLASS_NAME, 'FluidCell-module_linkOverlay__v8dDs')
        return [element.get_attribute('href') for element in elements]

    def _check_patterns(self, text: str, patterns: List[str]) -> Dict[str, List[str]]:
        """
        Check text against a list of patterns and return matches with captured groups
        """
        matches = {}
        for pattern in patterns:
            if pattern and (found := re.findall(pattern, text, re.IGNORECASE)):
                # For patterns with capture groups, store the captured value
                if '(' in pattern:
                    matches[pattern] = [match if isinstance(match, str) else match[0] for match in found]
                else:
                    matches[pattern] = found
        return matches

    def _validate_primary_match(self, matches: List[str]) -> bool:
        """
        Validate that primary matches meet the required criteria
        Add your validation logic here
        """
        # Example validation - override this method with your specific validation rules
        return bool(matches)  # By default, return True if there are any matches

    def _analyze_text_progressive(self, text: str) -> Optional[Dict]:
        """
        Analyze text in stages: first primary identifiers, then organization context
        """
        # Stage 1: Look for primary identifiers first
        primary_matches = self._check_patterns(text, self.primary_patterns)
        if not primary_matches:
            return None
            
        # Validate primary matches if needed
        valid_primary_matches = {}
        for pattern, matches in primary_matches.items():
            if self._validate_primary_match(matches):
                valid_primary_matches[pattern] = matches
                
        if not valid_primary_matches:
            return None
            
        # Stage 2: Verify organization/grouping context
        org_matches = self._check_patterns(text, self.organization_patterns)
        if not org_matches:
            return None
            
        # Return evidence dictionary
        return {
            'primary_matches': {
                'primary': valid_primary_matches,
                'organization': org_matches
            }
        }

    def process_document(self, url: str) -> Optional[Dict]:
        """
        Process a single document URL and return evidence if found
        """
        try:
            self.driver.get(url)
            
            # Remove CSS to get cleaner text
            self.driver.execute_script("""
                var links = document.getElementsByTagName('link');
                for (var i = links.length - 1; i >= 0; i--) {
                    if (links[i].rel === 'stylesheet') {
                        links[i].parentNode.removeChild(links[i]);
                    }
                }
                var styles = document.getElementsByTagName('style');
                for (var i = styles.length - 1; i >= 0; i--) {
                    styles[i].parentNode.removeChild(styles[i]);
                }
            """)
            
            page_text = self.driver.find_element("tag name", "body").text
            evidence = self._analyze_text_progressive(page_text)
            
            if evidence:
                return {
                    'url': url,
                    'evidence': evidence,
                    'full_text': page_text
                }
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
        
        return None

    def analyze_documents(self, max_pages: int = 10) -> Dict:
        """
        Analyze multiple pages of search results and save evidence
        """
        all_evidence = []
        statement_urls = []
        
        logger.info("Starting document analysis...")
        
        # Create CSV file for evidence
        csv_path = os.path.join(self.evidence_dir, 'evidence_summary.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['URL', 'Primary Matches', 'Organization References'])
        
        for page in range(1, max_pages + 1):
            logger.info(f"\nProcessing page {page} of search results...")
            urls = self.get_page_urls(page)
            
            for url in urls:
                try:
                    logger.info(f"Processing document: {url}")
                    result = self.process_document(url)
                    
                    if result:
                        all_evidence.append(result)
                        statement_urls.append(url)

                        # Save detailed evidence to file
                        filename = f"evidence_{len(all_evidence)}.txt"
                        with open(os.path.join(self.evidence_dir, filename), 'w', encoding='utf-8') as f:
                            f.write(f"URL: {url}\n\nEvidence:\n")
                            
                            # Write primary matches
                            f.write("\nPRIMARY MATCHES FOUND:\n")
                            for pattern, matches in result['evidence']['primary_matches']['primary'].items():
                                f.write(f"Match: {matches}\n")
                            
                            # Write organization verification
                            f.write("\nORGANIZATION VERIFICATION:\n")
                            for pattern, matches in result['evidence']['primary_matches']['organization'].items():
                                f.write(f"Match: {matches}\n")
                            
                            f.write("\nFull Text:\n" + result['full_text'])
                        
                        # Update CSV with evidence summary
                        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow([
                                url,
                                '; '.join([m for matches in result['evidence']['primary_matches']['primary'].values() for m in matches]),
                                '; '.join([m for matches in result['evidence']['primary_matches']['organization'].values() for m in matches])
                            ])
                        
                        logger.info(f"Found evidence - saved to {filename}")
                        
                except Exception as e:
                    logger.error(f"Error processing document {url}: {str(e)}")
                    continue

        # Save all URLs to file
        with open(os.path.join(self.evidence_dir, 'all_statements.txt'), 'w', encoding='utf-8') as f:
            for url in statement_urls:
                f.write(f"{url}\n")

        return {
            'total_statements': len(statement_urls),
            'evidence_found': len(all_evidence),
            'evidence': all_evidence,
            'evidence_dir': self.evidence_dir
        }

    def cleanup(self):
        """
        Clean up resources
        """
        self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Analyze documents on Scribd')
    parser.add_argument('-s', '--search', type=str, required=True,
                      help='Search term to use on Scribd')
    parser.add_argument('-p', '--pages', type=int, default=10,
                      help='Number of pages to analyze (default: 10)')
    
    args = parser.parse_args()
    
    try:
        analyzer = StatementAnalyzer(args.search)
        results = analyzer.analyze_documents(max_pages=args.pages)
        
        print("\nAnalysis Results:")
        print(f"Processed {results['total_statements']} total URLs")
        print(f"Found evidence in {results['evidence_found']} documents")
        print(f"Evidence saved in directory: {results['evidence_dir']}")
        print("\nOutput files:")
        print(f"- all_statements.txt: List of all statements URLs")
        print(f"- evidence_summary.csv: CSV file with all matches")
        print(f"- evidence_N.txt: Detailed evidence files for each matching document")
        
    except FileNotFoundError as e:
        logger.error(f"ChromeDriver Error: {str(e)}")
        print("\nPlease ensure chromedriver is in the script directory or a subdirectory:")
        print("- Windows: 'chromedriver.exe'")
        print("- Unix/Mac: 'chromedriver'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if 'analyzer' in locals():
            analyzer.cleanup()

if __name__ == "__main__":
    main()
