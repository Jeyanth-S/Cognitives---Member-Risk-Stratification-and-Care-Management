import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";
import Papa from "papaparse"; // ✅ CSV parser
import "./Analytics.css"; // import CSS

const Analytics: React.FC = () => {
  const navigate = useNavigate();

  // ---------- State ----------
  const [inputs, setInputs] = useState({
    beneId: "",
    carrier_num_claims: "",
    carrier_total_payment: "",
    chronic_count_2008: "",
    inpatient_num_claims: "",
    inpatient_total_payment: "",
    inpatient_total_util_days: "",
    num_unique_drg: "",
    num_unique_inpatient_dx: "",
    num_unique_outpatient_dx: "",
    outpatient_num_claims: "",
    outpatient_total_payment: "",
    pde_num_prescriptions: "",
    pde_total_drug_cost: "",
    race: "",
    sex: "",
    total_spending: "",
  });

  const [loadingPredict, setLoadingPredict] = useState(false);
  const [predictResult, setPredictResult] = useState<any>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  const [loadingCare, setLoadingCare] = useState(false);
  const [careResult, setCareResult] = useState<any>(null);
  const [careError, setCareError] = useState<string | null>(null);

  const [showPowerBI, setShowPowerBI] = useState(false);

  // ROI state
  const [roiResult, setRoiResult] = useState<string | null>(null);
  const [roiError, setRoiError] = useState<string | null>(null);

  // ---------- Handle Input Change ----------
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setInputs((prev) => ({ ...prev, [name]: value }));
  };

  // ---------- Risk Prediction ----------
  const handlePredict = async () => {
    if (!inputs.beneId) {
      setPredictError("Please enter a Beneficiary ID");
      return;
    }

    setLoadingPredict(true);
    setPredictError(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          member_index: 0,
          features: {
            carrier_num_claims: Number(inputs.carrier_num_claims),
            carrier_total_payment: Number(inputs.carrier_total_payment),
            chronic_count_2008: Number(inputs.chronic_count_2008),
            inpatient_num_claims: Number(inputs.inpatient_num_claims),
            inpatient_total_payment: Number(inputs.inpatient_total_payment),
            inpatient_total_util_days: Number(inputs.inpatient_total_util_days),
            num_unique_drg: Number(inputs.num_unique_drg),
            num_unique_inpatient_dx: Number(inputs.num_unique_inpatient_dx),
            num_unique_outpatient_dx: Number(inputs.num_unique_outpatient_dx),
            outpatient_num_claims: Number(inputs.outpatient_num_claims),
            outpatient_total_payment: Number(inputs.outpatient_total_payment),
            pde_num_prescriptions: Number(inputs.pde_num_prescriptions),
            pde_total_drug_cost: Number(inputs.pde_total_drug_cost),
            race: Number(inputs.race),
            sex: Number(inputs.sex),
            total_spending: Number(inputs.total_spending),
          },
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setPredictResult(data);
      } else {
        setPredictError(data.error || "Prediction failed");
      }
    } catch (err) {
      console.error(err);
      setPredictError("Failed to connect to backend");
    } finally {
      setLoadingPredict(false);
    }
  };

  // ---------- Care Insights ----------
  const handleCareInsights = async () => {
    if (!inputs.beneId) {
      setCareError("Please enter a Beneficiary ID");
      return;
    }

    setLoadingCare(true);
    setCareError(null);

    try {
      const res = await fetch(`http://127.0.0.1:5001/patient/${inputs.beneId}`);
      const data = await res.json();
      if (res.ok) {
        setCareResult(data);
      } else {
        setCareError(data.error || "Failed to retrieve insights");
      }
    } catch (err) {
      console.error(err);
      setCareError("Failed to connect to backend");
    } finally {
      setLoadingCare(false);
    }
  };

  // ---------- ROI Calculation ----------
  const handleCalculateROI = async () => {
    if (!inputs.beneId) {
      setRoiError("Please enter a Beneficiary ID");
      return;
    }

    setRoiError(null);
    setRoiResult(null);

    try {
      const response = await fetch("/src/assets/final_beneficiary_dataset_transformed_test1.csv");
      const csvText = await response.text();

      Papa.parse(csvText, {
        header: true,
        complete: (result) => {
          const record = result.data.find(
            (row: any) => row.DESYNPUF_ID === inputs.beneId
          );
          if (record && record.ROI) {
            setRoiResult(record.ROI);
          } else {
            setRoiError("ROI not found for this Beneficiary ID");
          }
        },
      });
    } catch (error) {
      console.error(error);
      setRoiError("Error loading ROI data");
    }
  };

  // ---------- Word Report ----------
  const exportWordReport = async () => {
    if (!predictResult && !careResult && !roiResult) return;

    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({
              text: `Patient Analytics Report - ${inputs.beneId}`,
              heading: "Heading1",
              spacing: { after: 300 },
            }),
            new Paragraph({
              text: "Risk tier prediction",
              heading: "Heading2",
              spacing: { after: 200 },
            }),
            predictResult
              ? new Paragraph({
                  children: [
                    new TextRun({
                      text: `30 days cluster: ${predictResult.cluster_assignments["30_day"]}`,
                    }),
                    new TextRun({
                      text: `\n60 days cluster: ${predictResult.cluster_assignments["60_day"]}`,
                    }),
                    new TextRun({
                      text: `\n90 days cluster: ${predictResult.cluster_assignments["90_day"]}`,
                    }),
                    new TextRun({ text: `\nRisk Tier: ${predictResult.risk_tier}` }),
                    new TextRun({ text: `\nNarrative: ${predictResult.narrative}` }),
                  ],
                })
              : new Paragraph("No predictions available."),
            new Paragraph({
              text: "Care Management Insights",
              heading: "Heading2",
              spacing: { after: 200 },
            }),
            careResult && careResult.diseases && Array.isArray(careResult.diseases)
              ? new Paragraph({
                  text: `Detected Conditions:\n- ${careResult.diseases.join("\n- ")}`,
                })
              : new Paragraph("No detected conditions."),
            careResult && careResult.suggestions && Array.isArray(careResult.suggestions)
              ? new Paragraph({
                  text: `Care Suggestions:\n- ${careResult.suggestions.join("\n- ")}`,
                })
              : new Paragraph("No care suggestions."),
            new Paragraph({
              text: "ROI Analysis",
              heading: "Heading2",
              spacing: { after: 200 },
            }),
            roiResult
              ? new Paragraph({
                  children: [
                    new TextRun({ text: `ROI for ${inputs.beneId}: ${roiResult}` }),
                    new TextRun({
                      text: `\n\nThe ROI is calculated using Total cost before intervention (Inpatient cost + Outpatient cost + Drug cost) and Saving After intervention (Inpatient savings + Outpatient savings + PDE saving).`,
                    }),
                  ],
                })
              : new Paragraph("No ROI available."),
          ],
        },
      ],
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, `Patient_Report_${inputs.beneId}.docx`);
  };

  return (
    <div className="analytics-container">
      <header className="analytics-header">
        <h1>MED Analytics</h1>
        <div className="header-buttons">
          <button onClick={() => navigate("/home")}>Dashboard</button>
          <button onClick={exportWordReport}>Generate Word Report</button>
          <button onClick={() => setShowPowerBI(!showPowerBI)}>View Output</button>
          <button onClick={() => navigate("/login")}>Logout</button>
        </div>
      </header>

      <div className="analytics-content">
        <h2>Risk Stratification & Care Management</h2>

        {/* ---------- Input Form ---------- */}
        <div className="inputs-grid">
          {Object.entries(inputs).map(([key, value]) => (
            <div key={key} className="input-item">
              <label>{key.replace(/_/g, " ")}</label>
              <input
                type={key === "beneId" ? "text" : "number"}
                name={key}
                value={value}
                onChange={handleInputChange}
                placeholder={key === "beneId" ? "Enter Beneficiary ID" : "0"}
              />
            </div>
          ))}
        </div>

        {/* ---------- Risk Prediction ---------- */}
        <div className="card">
          <h3>🧠 Patient Risk Summary</h3>
          <button onClick={handlePredict} disabled={loadingPredict}>
            {loadingPredict ? "Predicting..." : "Run Prediction"}
          </button>
          {predictError && <p className="error">{predictError}</p>}
          {predictResult && (
            <div className="results">
              {/* existing prediction result UI */}
            </div>
          )}
        </div>

        {/* ---------- Care Management ---------- */}
        <div className="card">
          <h3>Care Management Insights</h3>
          <button onClick={handleCareInsights} disabled={loadingCare}>
            {loadingCare ? "Fetching..." : "Get Care Suggestions"}
          </button>
          {careError && <p className="error">{careError}</p>}
          {careResult && (
            <div className="results">
              {careResult.diseases && (
                <ul>
                  {careResult.diseases.map((d: string, idx: number) => (
                    <li key={idx}>{d}</li>
                  ))}
                </ul>
              )}
              {careResult.suggestions && (
                <ul>
                  {careResult.suggestions.map((s: string, idx: number) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* ---------- ROI Calculation (Separate Card) ---------- */}
        <div className="card">
          <h3>📈 ROI Calculation</h3>
          <button onClick={handleCalculateROI}>Calculate ROI</button>
          {roiError && <p className="error">{roiError}</p>}
          {roiResult && (
            <div className="results">
              <p>
                <strong>ROI for {inputs.beneId}:</strong> {roiResult}
              </p>
              <p style={{ marginTop: "0.5rem", fontStyle: "italic" }}>
                The ROI is calculated using Total cost before intervention (Inpatient cost + Outpatient cost + Drug cost) and Saving After intervention (Inpatient savings + Outpatient savings + PDE saving).
              </p>
            </div>
          )}
        </div>

        {/* ---------- Power BI ---------- */}
        {showPowerBI && (
          <div className="card">
            <h3>Power BI Report</h3>
            <iframe
              title="PowerBI"
              width="800"
              height="450"
              src="https://app.powerbi.com/view?r=eyJrIjoiNDY0ZjM4NTktNDRkZS00MzdjLThjZmQtZTVlNDk2NmIzZDk3IiwidCI6ImI0NGNlZDU4LTJhMjMtNDE5MC1iNjRjLTNmMTljNTc5M2I1MCJ9"
              frameBorder="0"
              allowFullScreen
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Analytics;
