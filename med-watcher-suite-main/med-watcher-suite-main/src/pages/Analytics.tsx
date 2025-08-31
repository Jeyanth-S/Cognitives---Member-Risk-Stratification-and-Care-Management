import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";
import "./Analytics.css";

const Analytics: React.FC = () => {
  const navigate = useNavigate();

  // Tabs
  const [activeTab, setActiveTab] = useState<"new" | "existing">("new");

  // ---------- New User ----------
  const [newUserFile, setNewUserFile] = useState<File | null>(null);
  const [newUserResult, setNewUserResult] = useState<any>(null);
  const [newUserError, setNewUserError] = useState<string | null>(null);
  const [loadingNewUser, setLoadingNewUser] = useState(false);

  // ---------- Existing User ----------
  const [beneId, setBeneId] = useState("");
  const [predictResult, setPredictResult] = useState<any>(null);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [loadingPredict, setLoadingPredict] = useState(false);

  const [careResult, setCareResult] = useState<any>(null);
  const [careError, setCareError] = useState<string | null>(null);
  const [loadingCare, setLoadingCare] = useState(false);

  const [showPowerBI, setShowPowerBI] = useState(false);

  // ---------- ROI ----------
  const [roiData, setRoiData] = useState<any>(null);
  const [loadingROI, setLoadingROI] = useState(false);
  const [roiError, setRoiError] = useState<string | null>(null);

  // Clear ROI data when beneId changes
  useEffect(() => {
    setRoiData(null);
    setRoiError(null);
  }, [beneId]);

  const fetchROIData = async (beneId: string) => {
    setLoadingROI(true);
    setRoiError(null);
    try {
      const res = await fetch(`http://127.0.0.1:5000/recency/${beneId}`);
      const data = await res.json();
      console.log("ROI API response:", data); // <-- Add this line
      if (res.ok && !data.error) {
        setRoiData(data);
      } else {
        setRoiError(data.error || "Failed to fetch ROI data");
        setRoiData(null);
      }
    } catch (err) {
      setRoiError("Failed to connect to backend");
      setRoiData(null);
    } finally {
      setLoadingROI(false);
    }
  };

  // Compute ROI from recency API data and prediction result
  const getProxyROI = () => {
    if (
      roiData &&
      roiData.LAST_YEAR_TOTAL_COST != null &&
      predictResult &&
      predictResult.Tier != null
    ) {
      const tierReductionMap: { [key: string]: number } = {
        "1": 0.25,
        "2": 0.18,
        "3": 0.12,
        "4": 0.07,
        "5": 0.03,
      };
      const tier = String(predictResult.Tier);
      const reduction = tierReductionMap[tier] || 0;
      const last_year_expense = roiData.LAST_YEAR_TOTAL_COST;
      const last_year_total_spend = roiData.LAST_YEAR_TOTAL_COST; // Only field available
      if (!last_year_total_spend || last_year_total_spend === 0) return null;
      const proxy_roi = (last_year_expense * reduction) / last_year_total_spend;
      return {
        last_year_expense,
        last_year_total_spend,
        tier,
        reduction,
        proxy_roi,
      };
    }
    return null;
  };

  // ---------- Handlers ----------
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setNewUserFile(e.target.files[0]);
    }
  };

  const handleNewUserPredict = async () => {
    if (!newUserFile) {
      setNewUserError("Please upload a patient CSV file");
      return;
    }

    setLoadingNewUser(true);
    setNewUserError(null);

    const formData = new FormData();
    formData.append("patient_csv", newUserFile);

    try {
      const res = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setNewUserResult(data);
      } else {
        setNewUserError(data.error || "Prediction failed");
      }
    } catch (err) {
      console.error(err);
      setNewUserError("Failed to connect to backend");
    } finally {
      setLoadingNewUser(false);
    }
  };

  const handlePredictExisting = async () => {
    if (!beneId) {
      setPredictError("Please enter a Beneficiary ID");
      return;
    }

    setLoadingPredict(true);
    setPredictError(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ beneficiary_id: beneId }),
      });

      const data = await res.json();
      if (res.ok) {
        setPredictResult(data);
        // Fetch ROI data immediately after prediction
        fetchROIData(beneId);
      } else {
        setPredictError(data.error || "Prediction failed");
        setRoiData(null);
      }
    } catch (err) {
      console.error(err);
      setPredictError("Failed to connect to backend");
      setRoiData(null);
    } finally {
      setLoadingPredict(false);
    }
  };

  const handleCareInsights = async () => {
    if (!beneId) {
      setCareError("Please enter a Beneficiary ID");
      return;
    }

    setLoadingCare(true);
    setCareError(null);

    try {
      const res = await fetch(`http://127.0.0.1:5001/patient/${beneId}`);
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

  const exportWordReport = async () => {
    if (!predictResult && !careResult) return;

    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({
              text: `Patient Analytics Report - ${beneId}`,
              heading: "Heading1",
              spacing: { after: 300 },
            }),
            new Paragraph({
              text: "Risk Tier Prediction",
              heading: "Heading2",
              spacing: { after: 200 },
            }),
            predictResult
              ? new Paragraph({
                  children: [
                    new TextRun({ text: `30-day Risk: ${predictResult.Risk_30}\n` }),
                    new TextRun({ text: `60-day Risk: ${predictResult.Risk_60}\n` }),
                    new TextRun({ text: `90-day Risk: ${predictResult.Risk_90}\n` }),
                    new TextRun({ text: `Risk Tier: ${predictResult.Tier}\n` }),
                    new TextRun({ text: `Explanation: ${predictResult.story}\n` }),
                    new TextRun({
                      text: `Recommended Actions: ${predictResult.recommended?.join(", ")}`,
                    }),
                  ],
                })
              : new Paragraph("No predictions available."),
            new Paragraph({
              text: "Care Management Insights",
              heading: "Heading2",
              spacing: { after: 200 },
            }),
            careResult?.suggestions && Array.isArray(careResult.suggestions)
              ? new Paragraph({
                  text: careResult.suggestions
                    .map(
                      (s: any) =>
                        `${s.disease}:\n${s.suggestion}\n\nSources:\n- ${s.source_chunks.join("\n- ")}`
                    )
                    .join("\n\n"),
                })
              : new Paragraph("No care suggestions."),
          ],
        },
      ],
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, `Patient_Report_${beneId}.docx`);
  };

  // ---------- UI ----------
  return (
    <div className="analytics-container">
      <header className="analytics-header">
        <h1>MED Analytics</h1>
        <div className="header-buttons">
          <button onClick={() => navigate("/home")}>Dashboard</button>
          {activeTab === "existing" && (
            <button onClick={exportWordReport}>Generate Word Report</button>
          )}
          <button onClick={() => setShowPowerBI(!showPowerBI)}>View Output</button>
          <button onClick={() => navigate("/login")}>Logout</button>
        </div>
      </header>

      {/* Tabs */}
      <div className="tab-buttons">
        <button
          className={activeTab === "new" ? "active" : ""}
          onClick={() => setActiveTab("new")}
        >
          New User
        </button>
        <button
          className={activeTab === "existing" ? "active" : ""}
          onClick={() => setActiveTab("existing")}
        >
          Existing User
        </button>
      </div>

      {/* ---------- New User ---------- */}
      {activeTab === "new" && (
        <div>
          {/* Prediction Card */}
          <div className="card">
            <h3>New Patient Risk Prediction</h3>
            <input type="file" accept=".csv" onChange={handleFileChange} />
            <button onClick={handleNewUserPredict} disabled={loadingNewUser}>
              {loadingNewUser ? "Processing..." : "Upload & Predict"}
            </button>
            {newUserError && <p className="error">{newUserError}</p>}
            {newUserResult && (
              <div className="results">
                <p>30-day Risk: <strong>{newUserResult.Risk_30}</strong></p>
                <p>60-day Risk: <strong>{newUserResult.Risk_60}</strong></p>
                <p>90-day Risk: <strong>{newUserResult.Risk_90}</strong></p>
                <p>Risk Tier: <strong>{newUserResult.Tier}</strong></p>
                <p>Explanation: {newUserResult.story}</p>
                <p>
                  Recommended Actions:{" "}
                  {newUserResult.recommended?.map((a: string, i: number) => (
                    <span key={i}>
                      {a}
                      {i < newUserResult.recommended.length - 1 ? ", " : ""}
                    </span>
                  ))}
                </p>
                {newUserResult.shap_img && (
                  <img
                    src={`http://127.0.0.1:5000/figs/${newUserResult.shap_img}`}
                    alt="SHAP"
                    style={{ width: "500px", marginTop: "10px" }}
                  />
                )}
              </div>
            )}
          </div>

          {/* Care Management Card */}
          {newUserResult && (
            <div className="card">
              <h3>Care Management Insights</h3>
              {newUserResult.careError && <p className="error">{newUserResult.careError}</p>}
              {newUserResult.suggestions && (
                <div className="results">
                  <h4>Detected Conditions</h4>
                  <ul>
                    {newUserResult.diseases?.map((d: string, idx: number) => (
                      <li key={idx}>{d}</li>
                    ))}
                  </ul>
                  <h4>Care Suggestions</h4>
                  <ul>
                    {newUserResult.suggestions?.map((s: any, idx: number) => (
                      <li key={idx}>
                        <strong>{s.disease}</strong>
                        <p>{s.suggestion}</p>
                        <details>
                          <summary>Source Chunks</summary>
                          <ul>
                            {s.source_chunks.map((chunk: string, i: number) => (
                              <li key={i}>{chunk}</li>
                            ))}
                          </ul>
                        </details>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* ROI Card */}
          {newUserResult && (
            <div className="card">
              <h3>ROI Calculation</h3>
              <button
                className="roi-btn"
                style={{
                  marginBottom: "10px",
                  background: "#2563eb",
                  color: "#fff",
                  border: "none",
                  borderRadius: "5px",
                  padding: "8px 18px",
                  fontWeight: 600,
                  cursor: loadingROI || !newUserResult.DESYNPUF_ID ? "not-allowed" : "pointer",
                  opacity: loadingROI || !newUserResult.DESYNPUF_ID ? 0.6 : 1,
                  transition: "opacity 0.2s",
                }}
                onClick={() => fetchROIData(newUserResult.DESYNPUF_ID)}
                disabled={loadingROI || !newUserResult.DESYNPUF_ID}
              >
                {loadingROI ? "Fetching ROI..." : "Predict ROI"}
              </button>
              {roiError && <p className="error">{roiError}</p>}
              {(() => {
                // Use newUserResult.Tier for tier, and roiData for cost
                const tierReductionMap: { [key: string]: number } = {
                  "1": 0.25,
                  "2": 0.18,
                  "3": 0.12,
                  "4": 0.07,
                  "5": 0.03,
                };
                if (
                  roiData &&
                  roiData.LAST_YEAR_TOTAL_COST != null &&
                  newUserResult.Tier != null
                ) {
                  const tier = String(newUserResult.Tier);
                  const reduction = tierReductionMap[tier] || 0;
                  const last_year_expense = roiData.LAST_YEAR_TOTAL_COST;
                  const last_year_total_spend = roiData.LAST_YEAR_TOTAL_COST;
                  const proxy_roi =
                    last_year_total_spend && last_year_total_spend !== 0
                      ? (last_year_expense * reduction) / last_year_total_spend
                      : null;
                  return (
                    <>
                      <div className="results">
                        <p>Last Year Expense: <strong>{last_year_expense}</strong></p>
                        <p>Last Year Total Spend: <strong>{last_year_total_spend}</strong></p>
                        <p>Risk Tier: <strong>{tier}</strong></p>
                        <p>Reduction % (by Tier): <strong>{reduction * 100}%</strong></p>
                        <p>
                          <strong>Proxy ROI:</strong>{" "}
                          {proxy_roi !== null ? proxy_roi.toFixed(4) : "N/A"}
                        </p>
                      </div>
                      <div className="roi-benefit-bar" style={{ display: "flex", width: "100%", margin: "10px 0 0 0", height: "32px", borderRadius: "4px", overflow: "hidden", boxShadow: "0 1px 4px #0001" }}>
                        <div
                          className="roi-bar-saved"
                          style={{
                            width: `${reduction * 100}%`,
                            background: "#22c55e",
                            color: "#fff",
                            padding: "4px 0",
                            borderRadius: "4px",
                            textAlign: "center",
                            fontWeight: 600,
                            transition: "width 0.5s",
                          }}
                        >
                          Potential Savings: {Math.round(reduction * 100)}%
                        </div>
                        <div
                          className="roi-bar-remaining"
                          style={{
                            width: `${100 - reduction * 100}%`,
                            background: "#e5e7eb",
                            color: "#222",
                            padding: "4px 0",
                            borderRadius: "4px",
                            textAlign: "center",
                            fontWeight: 400,
                            transition: "width 0.5s",
                          }}
                        >
                          Remaining Spend
                        </div>
                      </div>
                      <p style={{ marginTop: 10 }}>
                        <strong>Interpretation:</strong> By applying targeted care management for this risk tier, you could potentially reduce last year's expense by <b>{Math.round(reduction * 100)}%</b>, improving both patient outcomes and cost efficiency.
                      </p>
                    </>
                  );
                } else if (!loadingROI && !roiError) {
                  return <p className="error">Click "Predict ROI" to view calculation.</p>;
                } else {
                  return null;
                }
              })()}
            </div>
          )}
        </div>
      )}

      {/* ---------- Existing User ---------- */}
      {activeTab === "existing" && (
        <div>
          <div className="inputs-grid">
            <div className="input-item">
              <label>Beneficiary ID</label>
              <input
                type="text"
                name="beneId"
                value={beneId}
                onChange={(e) => setBeneId(e.target.value)}
                placeholder="Enter Beneficiary ID"
              />
            </div>
          </div>

          <div className="card">
            <h3>Risk Prediction (30/60/90 days)</h3>
            <button onClick={handlePredictExisting} disabled={loadingPredict}>
              {loadingPredict ? "Predicting..." : "Run Prediction"}
            </button>
            {predictError && <p className="error">{predictError}</p>}
            {predictResult && (
              <div className="results">
                <p>30-day Risk: <strong>{predictResult.Risk_30}</strong></p>
                <p>60-day Risk: <strong>{predictResult.Risk_60}</strong></p>
                <p>90-day Risk: <strong>{predictResult.Risk_90}</strong></p>
                <p>Risk Tier: <strong>{predictResult.Tier}</strong></p>
                <p>Explanation: {predictResult.story}</p>
                <p>
                  Recommended Actions:{" "}
                  {predictResult.recommended?.map((a: string, i: number) => (
                    <span key={i}>
                      {a}
                      {i < predictResult.recommended.length - 1 ? ", " : ""}
                    </span>
                  ))}
                </p>
                {predictResult.shap_img && (
                  <img
                    src={`http://127.0.0.1:5000/figs/${predictResult.shap_img}`}
                    alt="SHAP"
                    style={{ width: "500px", marginTop: "10px" }}
                  />
                )}
              </div>
            )}
          </div>

          <div className="card">
            <h3>Care Management Insights</h3>
            <button onClick={handleCareInsights} disabled={loadingCare}>
              {loadingCare ? "Fetching..." : "Get Care Suggestions"}
            </button>
            {careError && <p className="error">{careError}</p>}
            {careResult && (
              <div className="results">
                <h4>Detected Conditions</h4>
                <ul>
                  {careResult.diseases?.map((d: string, idx: number) => (
                    <li key={idx}>{d}</li>
                  ))}
                </ul>

                <h4>Care Suggestions</h4>
                <ul>
                  {careResult.suggestions?.map((s: any, idx: number) => (
                    <li key={idx}>
                      <strong>{s.disease}</strong>
                      <p>{s.suggestion}</p>
                      <details>
                        <summary>Source Chunks</summary>
                        <ul>
                          {s.source_chunks.map((chunk: string, i: number) => (
                            <li key={i}>{chunk}</li>
                          ))}
                        </ul>
                      </details>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* ROI Card */}
          <div className="card">
            <h3>ROI Calculation</h3>
            <button
              className="roi-btn"
              style={{
                marginBottom: "10px",
                background: "#2563eb",
                color: "#fff",
                border: "none",
                borderRadius: "5px",
                padding: "8px 18px",
                fontWeight: 600,
                cursor: loadingROI || !beneId ? "not-allowed" : "pointer",
                opacity: loadingROI || !beneId ? 0.6 : 1,
                transition: "opacity 0.2s",
              }}
              onClick={() => fetchROIData(beneId)}
              disabled={loadingROI || !beneId}
            >
              {loadingROI ? "Fetching ROI..." : "Predict ROI"}
            </button>
            {roiError && <p className="error">{roiError}</p>}
            {(() => {
              const roi = getProxyROI();
              if (roiData && predictResult && !roiError && roi) {
                return (
                  <>
                    <div className="results">
                      <p>Last Year Expense: <strong>{roi.last_year_expense}</strong></p>
                      <p>Last Year Total Spend: <strong>{roi.last_year_total_spend}</strong></p>
                      <p>Risk Tier: <strong>{roi.tier}</strong></p>
                      <p>Reduction % (by Tier): <strong>{roi.reduction * 100}%</strong></p>
                      <p>
                        <strong>Proxy ROI:</strong>{" "}
                        {roi.proxy_roi !== null
                          ? roi.proxy_roi.toFixed(4)
                          : "N/A"}
                      </p>
                    </div>
                    <div className="roi-benefit-bar" style={{ display: "flex", width: "100%", margin: "10px 0 0 0", height: "32px", borderRadius: "4px", overflow: "hidden", boxShadow: "0 1px 4px #0001" }}>
                      <div
                        className="roi-bar-saved"
                        style={{
                          width: `${roi.reduction * 100}%`,
                          background: "#22c55e",
                          color: "#fff",
                          padding: "4px 0",
                          borderRadius: "4px",
                          textAlign: "center",
                          fontWeight: 600,
                          transition: "width 0.5s",
                        }}
                      >
                        Potential Savings: {Math.round(roi.reduction * 100)}%
                      </div>
                      <div
                        className="roi-bar-remaining"
                        style={{
                          width: `${100 - roi.reduction * 100}%`,
                          background: "#e5e7eb",
                          color: "#222",
                          padding: "4px 0",
                          borderRadius: "4px",
                          textAlign: "center",
                          fontWeight: 400,
                          transition: "width 0.5s",
                        }}
                      >
                        Remaining Spend
                      </div>
                    </div>
                    <p style={{ marginTop: 10 }}>
                      <strong>Interpretation:</strong> By applying targeted care management for this risk tier, you could potentially reduce last year's expense by <b>{Math.round(roi.reduction * 100)}%</b>, improving both patient outcomes and cost efficiency.
                    </p>
                  </>
                );
              } else if (!loadingROI && !roiError) {
                return <p className="error">Click "Predict ROI" to view calculation.</p>;
              } else {
                return null;
              }
            })()}
          </div>
        </div>
      )}

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
  );
};

export default Analytics;
