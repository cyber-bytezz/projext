import logging
import os
from datetime import datetime
import re
from bs4 import BeautifulSoup

# Create a logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure the logger with a unique log file per run
log_file_path = f"logs/application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_comparable_sales_history(html_path):
    """
    Checks if three comparable sales were provided and each reflects the prior sales history.
    Logs all relevant findings and returns a pass/fail result.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        tables = soup.find_all('table')
        comparables_found = 0
        prior_history_found = 0

        for table in tables:
            table_text = table.get_text(separator=' ', strip=True)
            # Look for comparable sale sections
            for i in range(1, 4):
                pattern = rf'COMPARABLE SALE #? ?{i}'
                if re.search(pattern, table_text, re.I):
                    comparables_found += 1
                    # Now, look for prior sales history in the same table
                    prior_patterns = [
                        r'Date of Prior Sale/Transfer',
                        r'Price of Prior Sale/Transfer',
                        r'Prior Sale',
                        r'Prior Transfer',
                        r'Sales History',
                        r'Sales Comparison',
                        r'Data Source\(s\)'
                    ]
                    if any(re.search(pat, table_text, re.I) for pat in prior_patterns):
                        prior_history_found += 1
                        logger.info(f"Comparable Sale #{i}: Prior sales history found.")
                    else:
                        logger.info(f"Comparable Sale #{i}: Prior sales history NOT found.")
            # If all three found, no need to continue
            if comparables_found >= 3:
                break

        if comparables_found >= 3 and prior_history_found >= 3:
            logger.info("Validation passed: Three comparable sales were provided and each reflects the prior sales history.")
            return {'rule61': 'success'}
        elif comparables_found >= 3:
            logger.info("Validation failed: Three comparable sales provided, but not all have prior sales history fields.")
            return {'rule61': 'failed'}
        else:
            logger.info("Validation failed: Less than three comparable sales found.")
            return {'rule61': 'failed'}
    except Exception as e:
        logger.error(f"An error occurred while checking comparable sales history: {e}")
        return {'rule61': 'error'}

def start_rule_61(html_file_path, json_file_path=None):
    return check_comparable_sales_history(html_file_path)

if __name__ == '__main__':
    html_file_path = "./10_vlm.html"
    result = start_rule_61(html_file_path)
    logger.info(f"Rule 61 result: {result}")
