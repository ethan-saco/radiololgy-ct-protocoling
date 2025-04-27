import openai
from openai import OpenAI
import pandas as pd
import os
from typing import Dict, Union, List, Optional
import logging
from config import (
    PROTOCOL_REFERENCE_PATH,
    VALID_PRIORITIES,
    VALID_IV_CONTRAST,
    VALID_ORAL_CONTRAST,
    EGFR_CONTRAINDICATED,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    SYSTEM_PROMPT,
    PROTOCOL_SELECTION_GUIDANCE,
    PROTOCOL_COLUMN_MAPPING,
    NO_DATA_VARIANTS,
    API_TIMEOUT,
    MAX_RETRIES,
    logger
)

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not a valid CSV
    """
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {str(e)}")
        raise ValueError(f"Invalid CSV file: {file_path}")

def load_protocol_reference(protocol_file: str) -> pd.DataFrame:
    """
    Load and process the protocol reference data.
    
    Args:
        protocol_file (str): Path to the institutional protocols Excel file
        
    Returns:
        pd.DataFrame: Processed protocol reference data
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not a valid Excel file
    """
    try:
        # Read the Excel file
        df = pd.read_excel(protocol_file)
        
        # Rename columns according to mapping
        df = df.rename(columns=PROTOCOL_COLUMN_MAPPING)
        
        return df
    except FileNotFoundError:
        logger.error(f"Protocol reference file not found: {protocol_file}")
        raise
    except Exception as e:
        logger.error(f"Error loading protocol reference file {protocol_file}: {str(e)}")
        raise ValueError(f"Invalid protocol reference file: {protocol_file}")

def generate_protocol_recommendations(patient_info: dict, egfr: Union[float, str, int]) -> Dict:
    """
    Generate CT protocol recommendations using OpenAI model.
    
    Args:
        patient_info (dict): Dictionary containing patient information
        egfr (Union[float, str, int]): Patient's eGFR value or "no data"
        
    Returns:
        dict: Dictionary containing protocol recommendations
        
    Raises:
        ValueError: If required fields are missing
        Exception: If there's an error generating recommendations
    """
    # Simplified input validation - only check essential fields
    essential_fields = ['Study_ID', 'Location', 'CT_Exam', 'Clinical_Info', 'eGFR']
    for field in essential_fields:
        if field not in patient_info:
            logger.error(f"Missing required field: {field}")
            raise ValueError(f"Missing required field: {field}")

    # Get reference protocols with error handling
    try:
        reference_protocols = load_protocol_reference(PROTOCOL_REFERENCE_PATH)
    except Exception as e:
        logger.error(f"Error loading protocol reference: {str(e)}")
        return {
            "priority": "no data",
            "protocol": "no data",
            "iv_contrast": "no data",
            "oral_contrast": "no data"
        }

    # Update contrast guidance to handle eGFR
    egfr_value = patient_info['eGFR']
    egfr_contraindicated = False
    
    if isinstance(egfr_value, str) and any(egfr_value.lower() == variant.lower() for variant in NO_DATA_VARIANTS):
        contrast_guidance = "eGFR data not available - assuming normal renal function."
        egfr_contraindicated = False
    elif isinstance(egfr_value, (int, float)) and egfr_value < EGFR_CONTRAINDICATED:
        contrast_guidance = "Due to eGFR < 30, IV contrast is typically contraindicated."
        egfr_contraindicated = True
    else:
        contrast_guidance = "eGFR > 30, IV contrast can be administered with low risk."
        egfr_contraindicated = False

    # Make protocol guidance more structured
    protocol_guidance = "CT Protocol Reference Document Specifications:\n"
    relevant_protocols = reference_protocols.to_dict('records')
    
    for row in relevant_protocols:
        protocol_guidance += (
            f"Protocol: {row['Protocol']}\n"
            f"- IV Contrast: {row['IV_Contrast']}\n"
            f"- Oral Contrast: {row['Oral_Contrast']}\n"
            f"- Example Indications: {row['Example_Indications']}\n"
        )

    # Generate recommendations with retry logic
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
Patient Information:
Study ID: {patient_info['Study_ID']}
Location: {patient_info['Location']}
CT Exam Requested: {patient_info['CT_Exam']}
Clinical Info: {patient_info['Clinical_Info']}
Prior Contrast Reaction: {patient_info.get('Prior_Reaction', 'None')}
eGFR: {patient_info['eGFR']} mL/min

{PROTOCOL_SELECTION_GUIDANCE}

{protocol_guidance}

Provide your recommendation in this exact JSON format:
{{
    "priority": 1 or 2 or 3 or 4,
    "protocol": "A/P or C/A/P or specific protocol",
    "iv_contrast": "C+ or C- or C+ and C-",
    "oral_contrast": "None or Water base or Water Only or Readi-Cat or Other"
}}"""}
                ],
                temperature=MODEL_TEMPERATURE,
                timeout=API_TIMEOUT
            )
            
            recommendations = eval(response.choices[0].message.content)
            
            # Validate recommendations
            if not all(key in recommendations for key in ['priority', 'protocol', 'iv_contrast', 'oral_contrast']):
                raise ValueError("Invalid recommendation format")
                
            if recommendations['priority'] not in VALID_PRIORITIES:
                raise ValueError(f"Invalid priority: {recommendations['priority']}")
                
            if recommendations['iv_contrast'] not in VALID_IV_CONTRAST:
                raise ValueError(f"Invalid IV contrast: {recommendations['iv_contrast']}")
                
            if recommendations['oral_contrast'] not in VALID_ORAL_CONTRAST:
                raise ValueError(f"Invalid oral contrast: {recommendations['oral_contrast']}")
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error(f"All attempts failed to generate recommendations: {str(e)}")
                raise
            continue

def get_standard_protocols(protocol_file: str) -> Dict:
    """
    Load protocols from the protocol reference Excel file and convert to standard format
    
    Args:
        protocol_file (str): Path to the protocol reference Excel file
        
    Returns:
        Dict: Dictionary of standardized protocols
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not a valid Excel file
    """
    try:
        df = pd.read_excel(protocol_file)
        
        protocols = {}
        for _, row in df.iterrows():
            protocols[row['Protocol']] = {
                "iv_contrast": row['IV Contrast'],
                "oral_contrast": row['Oral Contrast'],
                "acquisitions": row['Acquisitions'],
                "example_indications": row['Example Indications'],
                "notes": row['Notes']
            }
        
        return protocols
    except FileNotFoundError:
        logger.error(f"Protocol reference file not found: {protocol_file}")
        raise
    except Exception as e:
        logger.error(f"Error loading protocol reference file {protocol_file}: {str(e)}")
        raise ValueError(f"Invalid protocol reference file: {protocol_file}")
