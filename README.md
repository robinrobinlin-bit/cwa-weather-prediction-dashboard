# CWA Weather Prediction Dashboard (Skeleton)

This is a production-ready weather prediction and interactive visualization dashboard project skeleton.

## Tech Stack
- **Python**: 3.12
- **Backend API**: FastAPI
- **Data Processing**: Pandas
- **Database**: SQLite
- **Machine Learning**: Scikit-Learn
- **Visualization**: Plotly & Windy Map API
- **Deployment**: Vercel Serverless Functions

## Project Structure
```text
cwa-weather-prediction-dashboard/
│
├── api/                      # Serverless API endpoints for Vercel
│   └── index.py              # Main API entry point (FastAPI instance)
│
├── src/                      # Source code directory for core logic
│   ├── cwa_client.py         # CWA Weather Data API Client
│   ├── database.py           # SQLite Database schemas and helpers
│   ├── train.py              # ML training service using RandomForestRegressor
│   └── predict.py            # ML inference service
│
├── models/                   # Directory to store trained ML models (.pkl)
│   └── .gitkeep
│
├── data/                     # Directory to store SQLite database files
│   └── .gitkeep
│
├── outputs/                  # Directory for generated reports, figures, and plots
│   └── .gitkeep
│
├── tests/                    # Directory containing automated unit tests
│   └── .gitkeep
│
├── .env.example              # Configuration template for local development
├── .gitignore                # Git exclusion specifications
├── README.md                 # Project documentation
├── requirements.txt          # Python dependency specifications
├── vercel.json               # Vercel deployment rewrite rules
└── app.py                    # Streamlit Dashboard application
```

## Getting Started

### 1. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### 3. Local Development
To run the FastAPI server locally:
```bash
uvicorn api.index:app --reload
```
View the live API documentation at `http://127.0.0.1:8000/docs`.

### 4. Deploying to Vercel
Push this repository to GitHub and connect it to Vercel. Vercel will automatically recognize the configurations in `vercel.json` and deploy the FastAPI backend.
