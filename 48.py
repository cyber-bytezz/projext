import logging
import os
from datetime import datetime
import re
from bs4 import BeautifulSoup

# Ensure a 'logs' directory exists to store log files for each run.
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up logging to both a uniquely named file (per run) and the console.
# This helps with debugging and tracking application runs.
log_file_path = f"logs/application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),  # Log to file for later review
        logging.StreamHandler()              # Log to console for immediate feedback
    ]
)

logger = logging.getLogger(__name__)

def check_appraisal_comparables(html_path):
    """
    Parses the HTML file to find the appraisal section and extract the number of comparable properties currently listed and sold in the neighborhood.
    Returns a dictionary with the extracted numbers or a failure message if not found.
    """
    try:
        # Open and parse the HTML file using BeautifulSoup for easy HTML traversal.
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Find all tables, as appraisal data is expected to be in table format.
        appraisal_tables = soup.find_all('table')
        listed = None
        sold = None
        for table in appraisal_tables:
            # Extract all text from the table for pattern searching.
            text = table.get_text(separator=' ', strip=True)
            # Use regex to find the number of comparable properties listed for sale.
            listed_match = re.search(r'There are\s*(\d+)\s*comparable properties currently offered for sale', text, re.I)
            # Use regex to find the number of comparable properties sold in the neighborhood.
            sold_match = re.search(r'There are\s*(\d+)\s*comparable sales in the subject neighborhood', text, re.I)
            if listed_match:
                listed = int(listed_match.group(1))
                logger.info(f"'Listed' comparable properties found: {listed}")
            if sold_match:
                sold = int(sold_match.group(1))
                logger.info(f"'Sold' comparable properties found: {sold}")
            # Stop searching if both values are found to avoid unnecessary processing.
            if listed is not None and sold is not None:
                break

        # Return success if both numbers are found, otherwise indicate failure.
        if listed is not None and sold is not None:
            logger.info(f"Validation passed: Appraisal indicates listed={listed}, sold={sold} comparable properties in the neighborhood.")
            return {'rule_appraisal': 'success', 'appraisal_comparables': {'listed': listed, 'sold': sold}}
        else:
            logger.info("Validation failed: Number of comparable properties currently listed and sold in the neighborhood is NOT indicated.")
            return {'rule_appraisal': 'failed'}
    except Exception as e:
        # Log any unexpected errors for troubleshooting.
        logger.error(f"An error occurred while checking the appraisal comparables: {e}")
        return {'rule_appraisal': 'error'}

def start_rule_appraisal(html_file_path, json_file_path=None):
    # Entry point for the rule appraisal check; can be extended to use json_file_path if needed.
    return check_appraisal_comparables(html_file_path)

if __name__ == '__main__':
    # Example usage: specify the HTML file to process.
    html_file_path = "./10_vlm.html"
    result = start_rule_appraisal(html_file_path)
    logger.info(f"Appraisal comparables result: {result}")
