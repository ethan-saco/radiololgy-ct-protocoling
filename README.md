# CT Protocol Automation

This project uses OpenAI's API to automate CT protocol recommendations based on patient data.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your OpenAI API key
5. Place your input CSV file in the `data` directory

## Usage

1. Open the Jupyter notebook in `notebooks/ct_protocol_analysis.ipynb`
2. Update the input/output file paths in `src/config.py` if needed
3. Run the notebook cells to process your data

## Project Structure

- `data/`: Contains input and output CSV files
- `notebooks/`: Jupyter notebooks for analysis
- `src/`: Source code
  - `config.py`: Configuration settings
  - `utils.py`: Utility functions 