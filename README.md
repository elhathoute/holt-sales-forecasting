# 📊 Sales Forecasting App with Holt's Method

Streamlit application for sales forecasting using Holt's double exponential smoothing method, designed for macOS but works on all platforms.

![App Screenshot](screenshot.png)

## Features
- Excel-based product database (EAN codes)
- 12-month historical data input
- Customizable forecast period (1-12 months)
- CSV export functionality
- Responsive design

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- macOS (or any OS with Python)

### Installation

#### 1. Install Python (if not installed)
**macOS:**
```bash
# Install Homebrew (package manager)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python via Homebrew
brew install python

python3 --version  # Should show Python 3.9+
pip3 --version

cd sales-forecast-app

# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

run app
streamlit run app.py

## Demo Video

[Watch the demo video](./video.mp4)
