import React, { useEffect, useState } from "react";
import Papa from "papaparse";
import { saveAs } from "file-saver";
import { Document, Packer, Paragraph, Table, TableCell, TableRow, WidthType } from "docx";
import { useNavigate } from "react-router-dom";
import "./PatientDetails.css";

const PatientDetails = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const navigate = useNavigate();

  const requiredColumns = [
    "DESYNPUF_ID",
    "SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
    "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS",
    "SP_RA_OA", "SP_STRKETIA",
    "chronic_count_2008", "chronic_count_2009", "chronic_count_2010",
    "total_visits", "total_amount", "avg_claim_amount"
  ];

  const loadData = async () => {
    try {
      const response = await fetch("/data/combined_features_2010.csv");
      if (!response.ok) throw new Error("Failed to fetch CSV file");

      const text = await response.text();
      Papa.parse(text, {
        header: true,
        complete: (results) => {
          setData(results.data.slice(0, 10000));
          setLoading(false);
        },
        error: (err) => {
          setError(err.message || "Error loading data");
          setLoading(false);
        },
      });
    } catch (err: any) {
      setError(err.message || "Error loading data");
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredData = data.filter(row => {
    const beneId = row["DESYNPUF_ID"] || "";
    return beneId.toString().toUpperCase().includes(searchTerm.toUpperCase());
  });

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const currentRows = filteredData.slice(startIndex, startIndex + rowsPerPage);

  const exportWord = async () => {
    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({ text: "MED Analytics - Patient Details", heading: "Heading1", spacing: { after: 300 } }),
            new Table({
              rows: [
                new TableRow({
                  children: requiredColumns.map(col => new TableCell({
                    children: [new Paragraph({ text: col })],
                    width: { size: 100 / requiredColumns.length, type: WidthType.PERCENTAGE },
                  }))
                }),
                ...filteredData.slice(0, 100).map(row => new TableRow({
                  children: requiredColumns.map(col => new TableCell({
                    children: [new Paragraph({
                      text: [
                        "SP_ALZHDMTA","SP_CHF","SP_CHRNKIDN","SP_CNCR","SP_COPD",
                        "SP_DEPRESSN","SP_DIABETES","SP_ISCHMCHT","SP_OSTEOPRS",
                        "SP_RA_OA","SP_STRKETIA"
                      ].includes(col) ? (row[col] === "1" ? "Yes" : "No") : (row[col] || "")
                    })]
                  }))
                }))
              ]
            })
          ]
        }
      ]
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, "med_analytics.docx");
  };

  return (
    <div>
      {/* Header Bar */}
      <header className="header-bar">
        <h2 className="header-title">MED Analytics</h2>
        <div className="header-buttons">
          <button className="header-btn" onClick={() => navigate("/home")}>Dashboard</button>
          <button className="header-btn" onClick={exportWord}>Download Word</button>
        </div>
      </header>

      <div className="content">
        <h1 className="page-title">
          Patient Details 2010 (Page {currentPage} of {totalPages})
        </h1>

        {/* Search Box */}
        <div className="search-container">
          <input
            type="text"
            placeholder="Search Bene ID..."
            className="form-control"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Table */}
        <div className="table-container">
          <table className="member-table">
            <thead>
              <tr>
                {requiredColumns.map(col => <th key={col}>{col}</th>)}
              </tr>
            </thead>
            <tbody>
              {currentRows.map((row, i) => (
                <tr key={i}>
                  {requiredColumns.map(col => (
                    <td key={col}>
                      {[
                        "SP_ALZHDMTA","SP_CHF","SP_CHRNKIDN","SP_CNCR",
                        "SP_COPD","SP_DEPRESSN","SP_DIABETES","SP_ISCHMCHT",
                        "SP_OSTEOPRS","SP_RA_OA","SP_STRKETIA"
                      ].includes(col) ? row[col] === "1" ? "Yes" : "No" : row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="pagination">
          {currentPage > 1 && <button onClick={() => setCurrentPage(currentPage - 1)}>Prev</button>}
          <span className="active">{currentPage}</span>
          {currentPage < totalPages && <button onClick={() => setCurrentPage(currentPage + 1)}>Next</button>}
        </div>
      </div>
    </div>
  );
};

export default PatientDetails;
