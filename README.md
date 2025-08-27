# MedAnalytics: Member Risk Stratification and Care Management

MedAnalytics is an end-to-end healthcare analytics platform for risk stratification, care management, and ROI analysis of patient populations. It combines advanced machine learning, explainable AI, and interactive dashboards to empower healthcare professionals with actionable insights.

## Features

- **AI-Powered Risk Prediction:** Predict patient risk tiers for 30, 60, and 90 days using clustering and SHAP explainability.
- **Care Management Insights:** Get disease detection and personalized care suggestions.
- **ROI Analysis:** Calculate intervention ROI for each beneficiary.
- **Interactive Dashboards:** Visualize statistics and trends with a modern React + Tailwind UI.
- **Word Report Generation:** Export patient analytics and insights as Word documents.
- **Power BI Integration:** View advanced analytics and reports.

## Project Structure

```
.
├── app.py, Rag.py, risk_engine.py, ...   # Python backend services (Flask APIs, ML logic)
├── data/                                # Raw and processed healthcare datasets
├── med-watcher-suite-main/              # Main React frontend (TypeScript, Vite, Tailwind, shadcn-ui)
│   └── src/pages/Analytics.tsx          # Main analytics UI
├── pipeline/                            # Notebooks and scripts for data processing & ML
├── ui/                                  # Flask-based UI (optional, for legacy/simple views)
└── README.md
```

## Getting Started

### Backend (Python)

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
2. Start the Flask API:
    ```sh
    python app.py
    # or for risk engine:
    python Rag.py
    ```

### Frontend (React)

1. Go to the frontend directory:
    ```sh
    cd med-watcher-suite-main/med-watcher-suite-main
    ```
2. Install dependencies:
    ```sh
    npm install
    ```
3. Start the development server:
    ```sh
    npm run dev
    ```

### Data Pipeline

- See `pipeline/` for Jupyter notebooks and scripts to process and engineer features from raw CMS data.

## Technologies Used

- **Backend:** Python, Flask, scikit-learn, pandas, SHAP
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn-ui
- **Data:** DuckDB, Parquet, CSV
- **Visualization:** Power BI, docx, file-saver

## Example Usage

- Enter patient features in the Analytics UI to predict risk and get care suggestions.
- Download a Word report for any patient.
- View Power BI dashboards for population-level insights.

## License

This project is for research and demonstration purposes only.

---

*For more details, see the code in [med-watcher-suite-main/src/pages/Analytics.tsx](med-watcher-suite-main/med-watcher-suite-main/src/pages/Analytics.tsx) and the backend logic in [risk_engine.py](risk_engine.py) and [Rag.py](Rag.py)
