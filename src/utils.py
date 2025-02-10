import pandas as pd
from openai import OpenAI
from .config import OPENAI_API_KEY, MODEL_NAME, SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load patient data from CSV file
    """
    return pd.read_csv(file_path)

def get_ct_protocol(patient_info: dict) -> str:
    """
    Get CT protocol recommendation using OpenAI API
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Patient information: {patient_info}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting CT protocol: {e}")
        return None 