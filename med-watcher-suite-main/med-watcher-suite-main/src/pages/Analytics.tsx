import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";

const Analytics: React.FC = () => {
  const navigate = useNavigate();

  // ---------- State ----------
  const [beneId, setBeneId] = useState("");
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [predictResult, setPredictResult] = useState<any>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  const [loadingCare, setLoadingCare] = useState(false);
  const [careResult, setCareResult] = useState<any>(null);
  const [careError, setCareError] = useState<string | null>(null);

  const [showPowerBI, setShowPowerBI] = useState(false); // for iframe toggle

  // ----------- Predictions -----------
  const handlePredict = async () => {
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
        body: JSON.stringify({ bene_id: beneId }),
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

  // ----------- Care Insights -----------
  const handleCareInsights = async () => {
    if (!beneId) {
      setCareError("Please enter a Beneficiary ID");
      return;
    }
    setLoadingCare(true);
    setCareError(null);
    try {
      const res = await fetch(`http://127.0.0.1:5001/patient/${beneId}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
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

  // ----------- Word Report -----------
  const exportWordReport = async () => {
    if (!careResult) return;

    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({ text: `Patient Analytics Report - ${beneId}`, heading: "Heading1", spacing: { after: 300 } }),
            new Paragraph({ text: "Risk tier prediction", heading: "Heading2", spacing: { after: 200 } }),
            predictResult ? new Paragraph({
              children: [
                new TextRun({ text: `30 days: ${predictResult.predictions["30d"]}` }),
                new TextRun({ text: `\n60 days: ${predictResult.predictions["60d"]}` }),
                new TextRun({ text: `\n90 days: ${predictResult.predictions["90d"]}` }),
              ]
            }) : new Paragraph("No predictions available."),
            new Paragraph({ text: "Care Management Insights", heading: "Heading2", spacing: { after: 200 } }),
            careResult.diseases && Array.isArray(careResult.diseases)
              ? new Paragraph({ text: `Detected Conditions:\n- ${careResult.diseases.join("\n- ")}` })
              : new Paragraph("No detected conditions."),
            careResult.suggestions && Array.isArray(careResult.suggestions)
              ? new Paragraph({ text: `Care Suggestions:\n- ${careResult.suggestions.join("\n- ")}` })
              : new Paragraph("No care suggestions."),
          ],
        },
      ],
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, `Patient_Report_${beneId}.docx`);
  };

  return (
    <div className="w-full min-h-screen bg-gray-100">
      {/* Header */}
      <header className="w-full bg-blue-600 text-white flex justify-between items-center px-6 py-4 shadow-md">
        <h1 className="text-3xl font-bold">MED Analytics</h1>
        <div className="flex gap-3">
          <button className="header-btn bg-blue-500 hover:bg-blue-700 px-4 py-2 rounded" onClick={() => navigate("/home")}>Dashboard</button>
          <button className="header-btn bg-blue-500 hover:bg-blue-700 px-4 py-2 rounded" onClick={exportWordReport}>Generate Word Report</button>
          <button className="header-btn bg-blue-500 hover:bg-blue-700 px-4 py-2 rounded" onClick={() => setShowPowerBI(!showPowerBI)}>View Output</button>
          <button className="header-btn bg-blue-500 hover:bg-blue-700 px-4 py-2 rounded" onClick={() => navigate("/login")}>Logout</button>
        </div>
      </header>

      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {/* Page Subtitle */}
        <h2 className="text-2xl font-semibold text-center mb-4">Risk Stratification and Care Management</h2>

        {/* Beneficiary Input */}
        <input
          type="text"
          placeholder="Enter Beneficiary ID"
          value={beneId}
          onChange={(e) => setBeneId(e.target.value)}
          className="border p-2 w-full mb-4 rounded"
        />

        {/* ---------- Prediction Model ---------- */}
        <div className="border rounded p-4 bg-white shadow-sm">
          <h2 className="text-xl font-semibold mb-2">Risk Prediction on 30/60/90 days windows</h2>
          <button
            onClick={handlePredict}
            disabled={loadingPredict}
            className="bg-blue-600 text-white px-4 py-2 rounded w-full"
          >
            {loadingPredict ? "Predicting..." : "Run Prediction"}
          </button>

          {predictError && <p className="text-red-500 mt-3">{predictError}</p>}

          {predictResult && predictResult.predictions && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">Predictions for {predictResult.bene_id}</h3>
              <p>30 days: <span className="font-bold">{predictResult.predictions["30d"]}</span></p>
              <p>60 days: <span className="font-bold">{predictResult.predictions["60d"]}</span></p>
              <p>90 days: <span className="font-bold">{predictResult.predictions["90d"]}</span></p>
            </div>
          )}
        </div>

        {/* ---------- Care Management ---------- */}
        <div className="border rounded p-4 bg-white shadow-sm">
          <h2 className="text-xl font-semibold mb-2">Care Management Insights</h2>
          <button
            onClick={handleCareInsights}
            disabled={loadingCare}
            className="bg-green-600 text-white px-4 py-2 rounded w-full"
          >
            {loadingCare ? "Fetching Insights..." : "Get Care Suggestions"}
          </button>

          {careError && <p className="text-red-500 mt-3">{careError}</p>}

          {careResult && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">Patient ID: {careResult.patient_id || beneId}</h3>

              {careResult.diseases && Array.isArray(careResult.diseases) && (
                <div className="mb-4">
                  <h4 className="font-semibold">Detected Conditions:</h4>
                  <ul className="list-disc list-inside text-gray-700">
                    {careResult.diseases.map((d: string, idx: number) => (
                      <li key={idx}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}

              {careResult.suggestions && Array.isArray(careResult.suggestions) && (
                <div>
                  <h4 className="font-semibold mb-2">Care Suggestions:</h4>
                  <ul className="list-decimal list-inside text-gray-700 space-y-2">
                    {careResult.suggestions.map((s: string, idx: number) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ---------- Power BI Output ---------- */}
        {showPowerBI && (
          <div className="mt-6 border rounded p-4 bg-white shadow-sm">
            <h2 className="text-xl font-semibold mb-4 text-center">Power BI Report</h2>
            <div className="flex justify-center">
              <iframe
                title="cognitives"
                width="800"
                height="450"
                src="https://app.powerbi.com/view?r=eyJrIjoiNDY0ZjM4NTktNDRkZS00MzdjLThjZmQtZTVlNDk2NmIzZDk3IiwidCI6ImI0NGNlZDU4LTJhMjMtNDE5MC1iNjRjLTNmMTljNTc5M2I1MCJ9"
                frameBorder="0"
                allowFullScreen
              ></iframe>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Analytics;
