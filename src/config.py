from dotenv import load_dotenv
import os
from typing import Dict
import logging

# Load environment variables
load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

MODEL_NAME = "gpt-4-2024-11-20"
MODEL_TEMPERATURE = 0
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Data configuration
INPUT_DATA_PATH = "data/Data-Extraction-Table.csv"
OUTPUT_DATA_PATH = "data/output.csv"
PROTOCOL_REFERENCE_PATH = "data/Institutional-Protocols.xlsx"
EGFR_CONTRAINDICATED = 30

# Data processing configuration
NO_DATA_VARIANTS = ["no data", "No data", "NO DATA", "No Data", ""]

# Column names configuration
COLUMN_NAMES = {
    'STUDY_ID': 'Study ID #',
    'LOCATION': 'Location [IP, ER, OP]',
    'AGE': 'Age',
    'SEX': 'Sex',
    'CT_EXAM': 'CT Exam Requested',
    'CLINICAL_INFO': 'Clinical Information/Reason for Scan',
    'PRIOR_REACTION': 'Previous adverse reaction to contrast (if YES, what type)',
    'EGFR': 'eGFR (mL/min)',
    'CREATININE': 'Creatinine (umol/L)'
}

# Protocol reference column mapping
PROTOCOL_COLUMN_MAPPING = {
    'Protocol': 'Protocol',
    'IV Contrast': 'IV_Contrast',
    'Oral Contrast': 'Oral_Contrast',
    'Acquisitions': 'Acquisitions',
    'Example Indications': 'Example_Indications',
    'Notes': 'Notes'
}

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'ct_protocol.log'

# System prompt
SYSTEM_PROMPT = """You are a CT protocol assistant that makes recommendations based on the provided CT Protocol Reference Document, rules and guidelines. 
The referenced protocols serve as a foundation, but you can adapt recommendations based on specific clinical scenarios and patient factors.
Your goal is to provide appropriate and safe imaging protocols that best address the clinical question.

Important Considerations:
1. Always consider the clinical context when making recommendations:
   - Oral contast is typically not needed unless specifically requested or indicated
   - For IV contrast: While eGFR guides safety, the diagnostic necessity and risk-benefit should be evaluated
   - When eGFR data is not available, assume normal renal function (eGFR >90) unless clinical history suggests otherwise
   - For protocol selection: The clinical information should drive protocol choice
   - When in doubt regarding protocol selection, default to A/P unless chest imaging (C/A/P) is specifically requested"""

# Protocol selection guidance
PROTOCOL_SELECTION_GUIDANCE = """
1. PROTOCOL SELECTION RULES/GUIDELINES:

   A. SPECIFIC PROTOCOLS:
   First check if the exam matches specific protocols in the reference document:
   * Renal mass protocols
   * Renal colic protocols
   * Other specialized protocols
   
   Follow the exact specifications from the protocol reference document for:
   - IV contrast requirements
   - Oral contrast requirements
   - Specific acquisition parameters
   - Any special instructions

   B. GENERAL PROTOCOL SELECTION (C/A/P vs A/P):
   When in doubt, default to A/P unless chest imaging (C/A/P) is specifically requested.
   
   USE C/A/P ONLY IF:
   A. CT Exam EXPLICITLY requests chest imaging:
      * Written as "C/A/P" or "CAP"
      * Specifically mentions "chest" or "thorax"
      * Clearly indicates need for chest imaging
   
   OR
   
   B. Clinical information STRONGLY indicates chest involvement:
      * Known metastatic cancer requiring chest imaging
      * Major trauma with potential chest injury
      * Symptoms/pathology explicitly involving both chest AND abdomen
      * Staging for specific cancers that require chest imaging

   USE A/P AS THE DEFAULT PROTOCOL, especially when:
   - CT Exam only mentions abdomen/pelvis
   - Clinical symptoms are isolated to abdomen/pelvis
   - Follow-up of known abdominal/pelvic pathology
   - No specific indication for chest imaging
   - Routine abdominal/pelvic complaints

2. ORAL CONTRAST GUIDELINES:
   -DEFAULT TO "NONE" unless there is a specific indication for oral contrast, as indicated below.
   
    Water base:
    -Specific request for oral contrast for ovarian or gastrointestinal primary malignancy followup  
    -Recent abdominal surgery and request for contrast to rule out injury versus perforation/leak.
    -Specific request for oral contrast to look for very proximal bowel leak (stomach, duodenum e.g. peptic ulcer disease, post RNY gastric bypass).

    Rectal contrast:
    -Specific request for rectal contrast to rule out anastomotic leak (e.g colorectal, sigmoid colon)
    -Specific request for rectal contrast to rule out rectal or sigmoid injury/perforation

    Water only:
    -CT urogram

    Sorbitol 3%:
    -Specific request for oral contrast to evaluate inflammatory bowel disease (IBD)
    -Iron deficiency anemia (IDA) and history of negative scope

3. IV CONTRAST GUIDELINES:
   
   DEFAULT TO "C+" FOR MOST CASES, especially:
   - Most abdominal/pelvic imaging
   - Cancer staging
   - Vascular studies
   - Suspected inflammatory conditions
   
   USE "C-" FOR:
   - Renal stone protocols
   - Patients with contraindications to contrast (eGFR < 30)
   - When specifically requested without contrast
   - Follow-up of known conditions where contrast is not needed
   
   USE "C+ and C-" FOR:
   - Renal mass characterization
   - Adrenal mass characterization
   - Specific protocols requiring both phases
   
   IMPORTANT: When in doubt, default to "C+" unless there is a specific clinical indication for "C-"

4. PRIORITY GUIDELINES:
   
Priority 1:
   -LOCATION "ER" ALWAYS GETS PRIORITY 1
   -Urgent IP indications (e.g., ICU rule out bowel ischemia)

Priority 2:
   -Most inpatients (IP)
   -Selected urgent OP (e.g., rule out renal colic, diverticulitis as OP)

Priority 3:
   -Most initial staging exams
   -Malignancy workup
   -Acute semi-urgent (e.g., stable, abdominal pain xdays)

Priority 4:
   -Most OP studies
   -Most malignancy follow-up
   -Chronic/non-urgent (e.g., abdominal xmonths or years)
"""

# Valid options with more specific descriptions
VALID_PRIORITIES = [1, 2, 3, 4]  # 1=STAT, 2=48h, 3=10d, 4=>10d
VALID_IV_CONTRAST = ["C+", "C-", "C+ and C-"]  # C+ = with contrast, C- = without contrast
VALID_ORAL_CONTRAST = ["Water base", "Water Only", "Readi-Cat", "None", "Other", "Other (rectal)", "Other (3% sorbitol)"]

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

