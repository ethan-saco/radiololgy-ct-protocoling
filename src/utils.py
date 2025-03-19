import openai
import pandas as pd
from typing import Dict, Union
from config import PROTOCOL_REFERENCE_PATH, VALID_PRIORITIES, VALID_IV_CONTRAST, VALID_ORAL_CONTRAST, EGFR_CONTRAINDICATED, MODEL_NAME, MODEL_TEMPERATURE, SYSTEM_PROMPT

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded data
    """
    return pd.read_csv(file_path)

def load_protocol_reference(protocol_file: str) -> pd.DataFrame:
    """
    Load and process the protocol reference data.
    
    Args:
        protocol_file (str): Path to the KGH protocols Excel file
        
    Returns:
        pd.DataFrame: Processed protocol reference data
    """
    # Read the Excel file
    df = pd.read_excel(protocol_file)
    
    # Map the actual column names to our expected column names
    column_mapping = {
        'Protocol': 'Protocol',
        'IV Contrast': 'IV_Contrast',
        'Oral Contrast': 'Oral_Contrast',
        'Acquisitions': 'Acquisitions',
        'Example Indications': 'Example_Indications',
        'Notes': 'Notes'
    }
    
    # Rename columns according to mapping
    df = df.rename(columns=column_mapping)
    
    return df

def generate_protocol_recommendations(patient_info: dict, egfr: Union[float, str, int]) -> Dict:
    """
    Generate CT protocol recommendations using OpenAI GPT-3.5 model.
    
    Args:
        patient_info (dict): Dictionary containing patient information
        egfr (Union[float, str, int]): Patient's eGFR value or "no data"
        
    Returns:
        dict: Dictionary containing protocol recommendations
    """
    # Simplified input validation - only check essential fields
    essential_fields = ['Study_ID', 'Location', 'CT_Exam', 'Clinical_Info', 'eGFR']
    for field in essential_fields:
        if field not in patient_info:
            raise ValueError(f"Missing required field: {field}")

    # Get reference protocols with error handling - use a try/except with specific error handling
    try:
        reference_protocols = load_protocol_reference(PROTOCOL_REFERENCE_PATH)
    except Exception as e:
        print(f"Error loading protocol reference: {str(e)}")
        # Return "no data" instead of default recommendations if reference loading fails
        return {
            "priority": "no data",
            "protocol": "no data",
            "iv_contrast": "no data",
            "oral_contrast": "no data"
        }

    # Update contrast guidance to handle eGFR - simplified logic
    egfr_value = patient_info['eGFR']
    egfr_contraindicated = False  # Default assumption
    
    # Handle various forms of "no data" - simplified check
    no_data_variants = ["no data", "No data", "NO DATA", "No Data", "nodata", "NoData", "NODATA", "no_data", "No_Data", "NO_DATA"]
    
    if isinstance(egfr_value, str) and any(egfr_value.lower() == variant.lower() for variant in no_data_variants):
        contrast_guidance = "eGFR data not available - assuming normal renal function."
        egfr_contraindicated = False
    elif isinstance(egfr_value, (int, float)) and egfr_value < EGFR_CONTRAINDICATED:
        contrast_guidance = "Due to eGFR < 30, IV contrast is typically contraindicated."
        egfr_contraindicated = True
    else:
        contrast_guidance = "eGFR > 30, IV contrast can be administered with low risk."
        egfr_contraindicated = False

    # Make protocol guidance more structured - include all protocols
    protocol_guidance = "CT Protocol Reference Document Specifications:\n"
    
    # Include all protocols from the reference document
    relevant_protocols = reference_protocols.to_dict('records')
    
    # Build protocol guidance with all protocols
    for row in relevant_protocols:
        protocol_guidance += (
            f"Protocol: {row['Protocol']}\n"
            f"- IV Contrast: {row['IV_Contrast']}\n"
            f"- Oral Contrast: {row['Oral_Contrast']}\n"
            f"- Example Indications: {row['Example_Indications']}\n"
        )

# Protocol Selection Guidance provided to the model
    protocol_selection_guidance = """
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
   
    None:
   -DEFAULT TO "NONE" unless there is a specific indication for oral contrast.
   
    Water base:
    -Ovarian or gastrointestinal (stomach, esophagus, appendix, colon) primary malignancy followup AND request for contrast. 
    -Recent abdominal surgery and request for contrast to rule out injury versus perforation/leak.
    -If looking for very proximal bowel leak (stomach, duodenum e.g. peptic ulcer disease, post RNY gastric bypass).

    Rectal contrast:
    -Rule out anastomotic leak (colorectal, sigmoid colon) AND request for contrast.
    -Rule out rectal, sigmoid injury/perforation AND request for contrast.

    Water only:
    -CT urogram

    Sorbitol 3%:
    -Evaluate inflammatory bowel disease (IBD)
    -Iron deficiency anemia (IDA) and negative scope

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
-Most malignancy follow-up
-Most OP studies
-Chronic/non-urgent (e.g., abdominal xmonths or years)
"""

# Add example cases (few shot prompting)
    example_cases = """
EXAMPLE CASES - Study these example cases carefully to understand the correct protocol selection:

Case 1:
Location: ER
CT Exam: CT A/P with contrast
Clinical Info: RLQ pain, fever, elevated WBC, Abdo pain ? appendicitis
-> Recommendation:
{
    "priority": 1,
    "protocol": "A/P",
    "iv_contrast": "C+",
    "oral_contrast": "None"
}

Case 2:
Location: OP
CT Exam: CT renal mass
Clinical Info: 3cm right renal lesion on US, characterization needed
-> Recommendation:
{
    "priority": 3,
    "protocol": "Renal mass",
    "iv_contrast": "C+ and C-",
    "oral_contrast": "None"
}

Case 3:
Location: ER
CT Exam: Renal stone
Clinical Info: Left flank pain, hematuria, ?nephrolithiasis
-> Recommendation:
{
    "priority": 1,
    "protocol": "Renal colic",
    "iv_contrast": "C-",
    "oral_contrast": "None"
}

Case 4:
Location: IP
CT Exam: CT C/A/P
Clinical Info: Staging for newly diagnosed colon cancer
-> Recommendation:
{
    "priority": 2,
    "protocol": "C/A/P",
    "iv_contrast": "C+",
    "oral_contrast": "None"
}

Case 5:
Location: OP
CT Exam: CT abdomen pelvis
Clinical Info: Chronic abdominal pain, bloating
-> Recommendation:
{
    "priority": 4,
    "protocol": "A/P",
    "iv_contrast": "C+",
    "oral_contrast": "None"
}

Case 6:
Location: OP
CT Exam: CAP
Clinical Info: 79F, surveillance post resected colon (Left hemicolectomy 3 years ago)
-> Recommendation:
{
    "priority": 4,
    "protocol": "CAP", 
    "iv_contrast": "C+", 
    "oral_contrast": "None"
}

Case 7:
Location: IP
CT Exam: CT Enterography
Clinical Info: Male, 75 years old. Severe iron deficiency anemia (hemoglobin 60s). Negative scopes. Rule out small bowel lesion.
-> Recommendation:
{
    "priority": 3,
    "protocol": "Enterography",
    "iv_contrast": "C+",
    "oral_contrast": "Other (3% sorbitol)"
}

Case 8:
Location: IP
CT Exam: AP w/ contrast
Clinical Info: 72M, POD #5 sigmoid resection r/o anastomotic leak.
-> Recommendation:
{
    "priority": 2,
    "protocol": "A/P",
    "iv_contrast": "C+",
    "oral_contrast": "Other (rectal)"
}

Case 9:
Location: OP
CT Exam: CT abdomen pelvis
Clinical Info: Diverticulitis follow-up
-> Recommendation:
{
    "priority": 4,
    "protocol": "A/P",
    "iv_contrast": "C+",
    "oral_contrast": "None"
}

Case 10:
Location: IP
CT Exam: CT abdomen
Clinical Info: Abdominal pain, possible partial small bowel obstruction
-> Recommendation:
{
    "priority": 2,
    "protocol": "A/P",
    "iv_contrast": "C+",
    "oral_contrast": "None"
}

Case 11:
Location: IP
CT Exam: CT abdomen pelvis
Clinical Info: Post-operative day 3, fever, abdominal pain, suspected anastomotic leak
-> Recommendation:
{
    "priority": 2,
    "protocol": "A/P",
    "iv_contrast": "C+",
    "oral_contrast": "Water base"
}
"""

# USER PROMPT
    prompt = f"""You are a CT protocol assistant. Your task is to analyze the patient information and provide precise protocol recommendations.
You must follow the protocol selection rules and guidelines.

First, study these example cases carefully to understand the correct protocol selection:
{example_cases}

Now, analyze this new case:

Patient Information:
Study ID: {patient_info['Study_ID']}
Location: {patient_info['Location']}
CT Exam Requested: {patient_info['CT_Exam']}
Clinical Info: {patient_info['Clinical_Info']}
Prior Contrast Reaction: {patient_info.get('Prior_Reaction', 'None')}
eGFR: {patient_info['eGFR']} mL/min

{protocol_selection_guidance}

{protocol_guidance}

Provide your recommendation in this exact JSON format:
{{
    "priority": 1 or 2 or 3 or 4,
    "protocol": "A/P or C/A/P or other specific protocol",
    "iv_contrast": "C+ or C- or C+ and C-",
    "oral_contrast": "None or Water base or Water Only or Readi-Cat or Other (rectal) or Other (3% sorbitol)"
}}"""
#END of USER PROMPT

    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            **({"temperature": MODEL_TEMPERATURE} if "o3-mini" not in MODEL_NAME else {}),
            response_format={ "type": "json_object" },
            timeout=10
        )
        
        recommendations = eval(response.choices[0].message.content)
        
        # Enhanced validation - FIRST check for ER patients and set priority 1
        # This check is moved to the top of the validation to ensure it takes precedence
        if patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED':
            recommendations['priority'] = 1
            
        # Validate priority is numeric and in range
        try:
            recommendations['priority'] = int(recommendations['priority'])
            if recommendations['priority'] not in VALID_PRIORITIES:
                # If invalid priority and not ER, default to 4
                if not (patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED'):
                    recommendations['priority'] = 4
        except (ValueError, TypeError):
            # If conversion fails and not ER, default to 4
            if not (patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED'):
                recommendations['priority'] = 4
            else:
                recommendations['priority'] = 1
            
        # Check protocol reference for specific protocols
        exam = str(patient_info['CT_Exam']).lower() if not pd.isna(patient_info['CT_Exam']) else ""
        info = str(patient_info['Clinical_Info']).lower() if not pd.isna(patient_info['Clinical_Info']) else ""
        
        # Map renal stone to renal colic
        renal_stone_terms = ['renal stone', 'kidney stone', 'nephrolithiasis', 'renal calculus', 'flank pain', 'renal colic']
        if any(term in exam for term in renal_stone_terms) or any(term in info for term in renal_stone_terms):
            if recommendations.get('protocol') == 'Renal stone':
                recommendations['protocol'] = 'Renal colic'
            
        # Look up specific protocols from reference document
        for protocol in relevant_protocols:
            protocol_name = str(protocol['Protocol']).lower() if pd.notna(protocol['Protocol']) else ""
            indications = str(protocol['Example_Indications']).lower() if pd.notna(protocol['Example_Indications']) else ""
            
            # Check if exam or clinical info matches protocol indications
            if (('renal mass' in protocol_name) and
                (protocol_name in exam or 
                 any(indication.strip() in info for indication in indications.split(',') if indication.strip()))):
                
                recommendations['protocol'] = protocol['Protocol']
                recommendations['iv_contrast'] = protocol['IV_Contrast']
                recommendations['oral_contrast'] = protocol['Oral_Contrast']
                
                # Even with specific protocol, ER patients still get priority 1
                if patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED':
                    recommendations['priority'] = 1
                    
                return recommendations
                
            # Special handling for renal colic
            if protocol_name == 'renal colic' and any(term in exam or term in info for term in renal_stone_terms):
                recommendations['protocol'] = 'Renal colic'
                # Ensure renal colic uses C- contrast
                recommendations['iv_contrast'] = "C-"
                recommendations['oral_contrast'] = protocol['Oral_Contrast']
                
                # Even with specific protocol, ER patients still get priority 1
                if patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED':
                    recommendations['priority'] = 1
                    
                return recommendations

        # More selective C/A/P validation
        if recommendations.get('protocol') == 'C/A/P':
            explicit_cap_terms = ['c/a/p', 'cap', 'chest', 'thorax', 'c.a.p']
            clinical_cap_terms = ['metastatic cancer', 'major trauma', 'chest and abdomen']
            
            if not (any(term in exam for term in explicit_cap_terms) or
                   any(term in info for term in clinical_cap_terms)):
                recommendations['protocol'] = 'A/P'
                
        # Rest of validation
        valid_oral_contrast = VALID_ORAL_CONTRAST
        if 'oral_contrast' not in recommendations or recommendations['oral_contrast'] not in valid_oral_contrast:
            recommendations['oral_contrast'] = "None"
            
        # Handle IV contrast based on eGFR
        if egfr_contraindicated:
            # If eGFR < 30, override to C- regardless of recommendation
            recommendations['iv_contrast'] = "C-"
        elif 'iv_contrast' not in recommendations or recommendations['iv_contrast'] not in VALID_IV_CONTRAST:
            recommendations['iv_contrast'] = "C+"  # Default to C+ instead of C-
            
        # Strict validation for oral contrast - override Readi-Cat in most cases
        if recommendations.get('oral_contrast') == "Readi-Cat":
            # Only allow Readi-Cat for very specific conditions
            bowel_obstruction_terms = ['bowel obstruction', 'obstruction', 'ileus', 'sbo']
            ibd_terms = ['crohn', 'ulcerative colitis', 'inflammatory bowel']
            radiologist_request_terms = ['radiologist requested', 'radiologist request', 'per radiologist', 'as requested by radiologist']
            
            # Check if any of these specific terms are in the clinical info
            has_bowel_condition = any(term in info for term in bowel_obstruction_terms) or any(term in info for term in ibd_terms)
            has_radiologist_request = any(term in info for term in radiologist_request_terms)
            
            # Only allow Readi-Cat if both condition is present AND radiologist requested it
            if not (has_bowel_condition and has_radiologist_request):
                # If not both conditions, override to None
                recommendations['oral_contrast'] = "None"
        
        # Check for urogram studies first
        urogram_terms = ['urogram', 'ctu', 'ct urography']
        if any(term in exam.lower() for term in urogram_terms):
            # For urogram studies, use Water base (preferred) or keep Water Only if specifically requested
            if recommendations.get('oral_contrast') not in ["Water Only", "Water base"]:
                recommendations['oral_contrast'] = "Water base"
            # Ensure urogram studies use C+ and C- contrast
            recommendations['iv_contrast'] = "C+ and C-"
            
        # Then check for conditions that should use Water base
        bowel_perforation_terms = ['perforation', 'perforated', 'leak', 'anastomotic leak']
        fistula_terms = ['fistula', 'enterocutaneous', 'enterovaginal']
        
        if any(term in info for term in bowel_perforation_terms) or any(term in info for term in fistula_terms):
            # For these conditions, override to Water base
            recommendations['oral_contrast'] = "Water base"
            
        # Then check for rectal cancer or perianal conditions
        rectal_terms = ['rectal cancer', 'rectal mass', 'rectal tumor', 'perianal', 'anal cancer', 'anus cancer']
        if any(term in info for term in rectal_terms) or ('rect' in info and ('cancer' in info or 'staging' in info)):
            # For rectal cancer, use Other (rectal)
            recommendations['oral_contrast'] = "Other (rectal)"
            
        # Final check for ER patients to ensure priority 1
        if patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED':
            recommendations['priority'] = 1
            
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        # Even in error case, if it's an ER patient, set priority to 1
        if patient_info['Location'].strip().upper() == 'ER' or patient_info['Location'].strip().upper() == 'ED':
            return {
                "priority": 1,
                "protocol": "no data",
                "iv_contrast": "no data",
                "oral_contrast": "no data"
            }
        else:
            return {
                "priority": 4,
                "protocol": "no data",
                "iv_contrast": "no data",
                "oral_contrast": "no data"
            }

def get_standard_protocols(protocol_file: str) -> Dict:
    """
    Load protocols from the protocol reference Excel file and convert to standard format
    
    Args:
        protocol_file (str): Path to the protocol reference Excel file
        
    Returns:
        Dict: Dictionary of standardized protocols
    """
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
