# CT Protocol Automation

A Python-based system that automates CT protocol recommendations using OpenAI's API. This tool helps radiologists and medical professionals by analyzing patient data and generating appropriate CT imaging protocols.

## 🚀 Features

- Automated CT protocol recommendations based on patient data
- Integration with OpenAI's API for intelligent protocol selection
- Support for various CT exam types and contrast requirements
- Handles complex medical scenarios including renal function considerations
- Generates structured recommendations for:
  - Protocol selection (A/P, C/A/P, specialized protocols)
  - IV contrast requirements
  - Oral contrast requirements
  - Priority levels

## 🔍 Logging and Error Handling

The system includes comprehensive logging and error handling:

- Logs are written to `ct_protocol.log` with timestamps and log levels
- Console output for immediate feedback
- Detailed error messages for:
  - Missing or invalid input data
  - API communication issues
  - File access problems
  - Invalid protocol recommendations
- Automatic retry mechanism for API calls (3 attempts)
- Graceful fallback for missing data

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Virtual environment (recommended)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/radiololgy-ct-protocoling.git
   cd radiololgy-ct-protocoling
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## ⚙️ Configuration

The system can be configured through `src/config.py`:

- **API Settings**:
  - Model selection and temperature
  - API timeout and retry settings
  - API key validation

- **Data Processing**:
  - Input/output file paths
  - Column name mappings
  - eGFR threshold for contrast contraindication
  - Valid options for priorities and contrast types

- **Logging**:
  - Log level and format
  - Log file location
  - Console output settings

- **Protocol Selection**:
  - Detailed guidance for protocol selection
  - Contrast administration rules
  - Priority assignment guidelines

## 📋 Protocol Selection Rules

The system follows specific rules for protocol selection:

1. **Priority Assignment**:
   - Priority 1: ER patients, urgent IP cases
   - Priority 2: Most inpatients, urgent OP cases
   - Priority 3: Initial staging, malignancy workup
   - Priority 4: Routine OP studies, follow-ups

2. **Protocol Selection**:
   - Default to A/P unless chest imaging is explicitly requested
   - C/A/P requires explicit chest imaging request or strong clinical indication
   - Specialized protocols (e.g., renal mass, renal colic) take precedence

3. **Contrast Guidelines**:
   - IV Contrast:
     - Default to C+ for most cases
     - C- for renal stones, eGFR < 30
     - C+ and C- for mass characterization
   - Oral Contrast:
     - Default to None unless specifically indicated
     - Water base for GI/ovarian malignancy
     - Water only for urogram studies
     - Special preparations for specific indications

## 📊 Project Structure

```
.
├── data/                  # Input and output data files
│   ├── Data-Extraction-Table.csv    # Sample patient data
│   └── Institutional-Protocols.xlsx  # Protocol reference document
├── notebooks/             # Jupyter notebooks for analysis
│   └── ct_protocol_analysis.ipynb   # Main analysis notebook
├── src/                   # Source code
│   ├── config.py         # Configuration settings
│   └── utils.py          # Utility functions
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 💻 Usage

1. Prepare your input data:
   - Place your patient data CSV file in the `data/` directory
   - Ensure the CSV file contains required columns (Study ID, Location, Age, Sex, etc.)

2. Run the analysis:
   - Open `notebooks/ct_protocol_analysis.ipynb` in Jupyter
   - Execute the cells to process your data
   - Review the generated protocol recommendations

## 📝 Input Data Format

The system expects a CSV file with the following exact column names:
```python
{
    'Study ID #': 'Unique identifier for the study',
    'Location [IP, ER, OP]': 'Patient location (Inpatient, Emergency Room, Outpatient)',
    'Age': 'Patient age',
    'Sex': 'Patient sex',
    'CT Exam Requested': 'Type of CT exam requested',
    'Clinical Information/Reason for Scan': 'Clinical details and reason for scan',
    'Previous adverse reaction to contrast (if YES, what type)': 'History of contrast reactions',
    'eGFR (mL/min)': 'Estimated Glomerular Filtration Rate',
    'Creatinine (umol/L)': 'Serum creatinine level'
}
```

## 📊 Output Format

The system generates recommendations in the following exact format:
```python
{
    'Study_ID': 'Study ID # from input',
    'Priority': 1-4,  # 1=STAT, 2=48h, 3=10d, 4=>10d
    'Protocol': 'A/P or C/A/P or specific protocol',
    'IV_Contrast': 'C+ or C- or C+ and C-',
    'Oral_Contrast': 'None or Water base or Water Only or Readi-Cat or Other'
}
```

## 🚨 Troubleshooting

Common issues and solutions:

1. **API Connection Issues**:
   - Verify your OpenAI API key in `.env`
   - Check internet connection
   - Review API timeout settings in `config.py`

2. **Data Loading Problems**:
   - Ensure input files are in correct format
   - Verify column names match expected format
   - Check file permissions

3. **Invalid Recommendations**:
   - Review input data quality
   - Check protocol reference file format
   - Verify eGFR values are valid

4. **Logging Issues**:
   - Check log file permissions
   - Verify log level settings
   - Ensure sufficient disk space

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is intended for educational and research purposes only. Always consult with qualified medical professionals for clinical decisions. 