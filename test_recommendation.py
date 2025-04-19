#!/usr/bin/env python3
"""
Test script for CT protocol recommendations.
"""

import os
from dotenv import load_dotenv
import pandas as pd
from src.utils import generate_protocol_recommendations

# Load environment variables
load_dotenv()

# Sample patient data
sample_patient = {
    'Study_ID': '12345',
    'Location': 'OP',
    'CT_Exam': 'CT abdomen pelvis',
    'Clinical_Info': 'Abdominal pain, rule out appendicitis',
    'Prior_Reaction': 'None',
    'eGFR': 85
}

try:
    # Generate recommendations
    print("Generating recommendations for sample patient...")
    recommendations = generate_protocol_recommendations(sample_patient, sample_patient['eGFR'])
    
    # Print results
    print("\nRecommendation Results:")
    print(f"Priority: {recommendations.get('priority', 'Not specified')}")
    print(f"Protocol: {recommendations.get('protocol', 'Not specified')}")
    print(f"IV Contrast: {recommendations.get('iv_contrast', 'Not specified')}")
    print(f"Oral Contrast: {recommendations.get('oral_contrast', 'Not specified')}")
    
except Exception as e:
    print(f"Error: {str(e)}")

# Try another sample with ER location
er_patient = {
    'Study_ID': '67890',
    'Location': 'ER',
    'CT_Exam': 'CT C/A/P',
    'Clinical_Info': 'Trauma, MVA',
    'Prior_Reaction': 'None',
    'eGFR': 'no data'
}

try:
    # Generate recommendations for ER patient
    print("\nGenerating recommendations for ER patient...")
    er_recommendations = generate_protocol_recommendations(er_patient, er_patient['eGFR'])
    
    # Print results
    print("\nER Patient Recommendation Results:")
    print(f"Priority: {er_recommendations.get('priority', 'Not specified')}")
    print(f"Protocol: {er_recommendations.get('protocol', 'Not specified')}")
    print(f"IV Contrast: {er_recommendations.get('iv_contrast', 'Not specified')}")
    print(f"Oral Contrast: {er_recommendations.get('oral_contrast', 'Not specified')}")
    
except Exception as e:
    print(f"ER Patient Error: {str(e)}") 