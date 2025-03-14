from dotenv import load_dotenv
import os
from typing import Dict

# Load environment variables
load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL_NAME = "gpt-4o-2024-11-20"
MODEL_TEMPERATURE = 0  # Add explicit temperature setting

# Data configuration
INPUT_DATA_PATH = "data/Data-Extraction-Table.csv"
OUTPUT_DATA_PATH = "data/output.csv"
PROTOCOL_REFERENCE_PATH = "data/KGH-Protocols.xlsx"

# Remove EGFR_BORDERLINE since it's no longer used
EGFR_CONTRAINDICATED = 30

# System prompt with more specific guidance
SYSTEM_PROMPT = """You are a CT protocol assistant that makes recommendations based on a provided CT Protocol Reference Document. 
The protocols in this reference document serve as a foundation, but you can adapt recommendations based on specific clinical scenarios and patient factors.
Your goal is to provide appropriate and safe imaging protocols that best address the clinical question.

Important Considerations:
1. Always consider the clinical context when making recommendations:
   - For IV contrast use: While eGFR guides safety, the diagnostic necessity and risk-benefit should be evaluated
   - When eGFR data is not available, assume normal renal function (>30) unless clinical history suggests otherwise
   - For protocol selection: The clinical question should drive protocol choice
   - For priority assignment: Patient condition and setting influence urgency
2. When adapting protocols, clearly indicate any deviations from standard protocols in the recommendations"""

# Valid options with more specific descriptions
VALID_PRIORITIES = [1, 2, 3, 4]  # 1=STAT, 2=48h, 3=10d, 4=>10d
VALID_IV_CONTRAST = ["C+", "C-", "C+ and C-"]  # C+=with contrast, C-=without contrast
VALID_ORAL_CONTRAST = ["Water base", "Water Only", "Readi-Cat", "None", "Other", "Other (rectal)", "Other (3% sorbitol)"]

