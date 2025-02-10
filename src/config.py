from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Model configuration
MODEL_NAME = "gpt-4-turbo-preview"  # or your preferred model

# Data configuration
INPUT_DATA_PATH = "data/input.csv"
OUTPUT_DATA_PATH = "data/output.csv"

# Prompt configuration
SYSTEM_PROMPT = """You are an expert radiologist AI assistant. Your task is to 
analyze patient information and recommend appropriate CT protocols.""" 