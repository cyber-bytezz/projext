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

def check_sales_history(html_path):
    """
    Checks if the appraiser researched the transfer/sales history for three (3) years prior to the effective date of the appraisal for the subject property or has provided an explanation.
    Logs all relevant findings and returns a pass/fail result.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Extract effective date of appraisal
        effective_date = None
        date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4})')
        for tag in soup.find_all(string=date_pattern):
            if 'appraisal' in tag.lower() or 'effective date' in tag.lower():
                match = date_pattern.search(tag)
                if match:
                    effective_date = match.group(1)
                    break
        if effective_date:
            logger.info(f"Effective date of appraisal found: {effective_date}")
        else:
            logger.info("Effective date of appraisal not found.")

        # Look for a statement about researching sales/transfer history for 3 years
        found_statement = False
        explanation_found = False
        statement_pattern = re.compile(r'(research|analyz|report).{0,80}(sale|transfer).{0,80}three.{0,10}year', re.I)
        explanation_pattern = re.compile(r'(if this information was available|no prior sale|not available|not found|explanation)', re.I)
        for tag in soup.find_all(string=True):
            if statement_pattern.search(tag):
                logger.info(f"Found statement: {tag.strip()}")
                found_statement = True
            if explanation_pattern.search(tag):
                logger.info(f"Found explanation: {tag.strip()}")
                explanation_found = True
            if found_statement and explanation_found:
                break
        if found_statement:
            logger.info("Validation passed: Appraiser researched transfer/sales history for three years or provided an explanation.")
            return {'rule_sales_history': 'success'}
        else:
            logger.info("Validation failed: No evidence of three-year sales history research or explanation found.")
            return {'rule_sales_history': 'failed'}
    except Exception as e:
        logger.error(f"An error occurred while checking sales history: {e}")
        return {'rule_sales_history': 'error'}

def start_rule_sales_history(html_file_path, json_file_path=None):
    return check_sales_history(html_file_path)

if __name__ == '__main__':
    html_file_path = "./10_vlm.html"
    result = start_rule_sales_history(html_file_path)
    logger.info(f"Sales history rule result: {result}")
