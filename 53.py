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

def check_comparable_sales_dates(html_path):
    """
    Checks if all comparable sales show a sold date of twelve (12) months or less from the date of the appraisal.
    Logs detailed results and returns a pass/fail result.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Extract appraisal date
        appraisal_date = None
        date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4})')
        for tag in soup.find_all(string=date_pattern):
            if 'appraisal' in tag.lower() or 'effective date' in tag.lower():
                match = date_pattern.search(tag)
                if match:
                    appraisal_date = match.group(1)
                    break
        if not appraisal_date:
            # Fallback: look for any date near "Uniform Residential Appraisal Report"
            for tag in soup.find_all(['td', 'p', 'span'], string=date_pattern):
                parent = tag.find_parent(['table', 'div', 'section'])
                if parent and 'appraisal' in parent.get_text().lower():
                    match = date_pattern.search(tag)
                    if match:
                        appraisal_date = match.group(1)
                        break
        if not appraisal_date:
            logger.info("Appraisal date not found.")
            return {'rule_comparable_sales_dates': 'failed'}
        logger.info(f"Appraisal date found: {appraisal_date}")
        try:
            appraisal_dt = datetime.strptime(appraisal_date, '%m/%d/%Y')
        except ValueError:
            try:
                appraisal_dt = datetime.strptime(appraisal_date, '%m/%d/%y')
            except Exception:
                logger.info("Appraisal date format not recognized.")
                return {'rule_comparable_sales_dates': 'failed'}

        # Extract all comparable sale dates
        sale_dates = []
        # Look for sale dates in tables with 'comparable' and 'sale' in their text
        for table in soup.find_all('table'):
            table_text = table.get_text(separator=' ', strip=True)
            if 'comparable' in table_text.lower() and 'sale' in table_text.lower():
                for match in date_pattern.findall(table_text):
                    sale_dates.append(match)
        # Also look for sale dates in any text mentioning 'sale' or 'sold'
        for tag in soup.find_all(string=date_pattern):
            if 'sale' in tag.lower() or 'sold' in tag.lower():
                for match in date_pattern.findall(tag):
                    sale_dates.append(match)
        # Remove duplicates
        sale_dates = list(set(sale_dates))
        if not sale_dates:
            logger.info("No comparable sale dates found.")
            return {'rule_comparable_sales_dates': 'failed'}
        logger.info(f"Comparable sale dates found: {sale_dates}")
        all_within_12_months = True
        for sale_date in sale_dates:
            try:
                sale_dt = datetime.strptime(sale_date, '%m/%d/%Y')
            except ValueError:
                try:
                    sale_dt = datetime.strptime(sale_date, '%m/%d/%y')
                except Exception:
                    logger.info(f"Sale date format not recognized: {sale_date}")
                    all_within_12_months = False
                    continue
            diff_months = (appraisal_dt.year - sale_dt.year) * 12 + (appraisal_dt.month - sale_dt.month)
            if diff_months > 12 or diff_months < 0:
                logger.info(f"Sale date {sale_date} is NOT within 12 months of appraisal date {appraisal_date}.")
                all_within_12_months = False
            else:
                logger.info(f"Sale date {sale_date} is within 12 months of appraisal date {appraisal_date}.")
        if all_within_12_months:
            logger.info("Validation passed: All comparable sales show a sold date of twelve (12) months or less from the date of the appraisal.")
            return {'rule_comparable_sales_dates': 'success'}
        else:
            logger.info("Validation failed: Not all comparable sales are within 12 months of the appraisal date.")
            return {'rule_comparable_sales_dates': 'failed'}
    except Exception as e:
        logger.error(f"An error occurred while checking comparable sales dates: {e}")
        return {'rule_comparable_sales_dates': 'error'}

def start_rule_comparable_sales_dates(html_file_path, json_file_path=None):
    return check_comparable_sales_dates(html_file_path)

if __name__ == '__main__':
    html_file_path = "./10_vlm.html"
    result = start_rule_comparable_sales_dates(html_file_path)
    logger.info(f"Comparable sales dates rule result: {result}")
