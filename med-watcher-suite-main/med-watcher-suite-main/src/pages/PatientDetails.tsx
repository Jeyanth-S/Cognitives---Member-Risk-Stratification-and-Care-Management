import React, { useEffect, useState } from 'react';
import Papa from 'papaparse';
import './PatientDetails.css'; // Ensure you have appropriate CSS for styling

const PatientDetails = () => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10; // Adjust this value as needed

  const loadData = async () => {
    try {
      const response = await fetch("/data/combined_features_2010.csv"); // Update the path to your CSV file
      if (!response.ok) throw new Error("Failed to fetch CSV file");
      
      const text = await response.text();
      Papa.parse(text, {
        header: true,
        complete: (results) => {
          const limitedData = results.data.slice(0, 10000); // Load only the first 10,000 rows
          setColumns(Object.keys(limitedData[0])); // Set columns from the first row
          setData(limitedData); // Set limited data
          setLoading(false);
        },
        error: (err) => {
          setError(err.message || "Error loading data");
          setLoading(false);
        }
      });
    } catch (err) {
      setError(err.message || "Error loading data");
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Search functionality
  const filteredData = data.filter(row => {
    const beneId = row['DESYNPUF_ID'] || ''; // Adjust the key based on your CSV structure
    return beneId.toString().toUpperCase().includes(searchTerm.toUpperCase());
  });

  // Pagination logic
  const totalPages = Math.ceil(filteredData.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const currentRows = filteredData.slice(startIndex, startIndex + rowsPerPage);

  return (
    <div className="content">
      <h1 className="page-title">Member Data (Page {currentPage} of {totalPages})</h1>

      {/* Search Box */}
      <div className="search-container" style={{ textAlign: 'right', marginBottom: '10px' }}>
        <input
          type="text"
          id="searchInput"
          placeholder="Search Bene ID..."
          className="form-control"
          style={{ maxWidth: '250px', display: 'inline-block' }}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Table wrapper for scrolling */}
      <div className="table-container">
        <table className="member-table" id="memberTable">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, index) => (
              <tr key={index}>
                {columns.map((col) => (
                  <td key={col}>
                    {["SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
                      "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS",
                      "SP_RA_OA", "SP_STRKETIA"].includes(col) ? (
                      row[col] === '1' ? 'Yes' : 'No'
                    ) : (
                      row[col]
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        {currentPage > 1 && (
          <button onClick={() => setCurrentPage(currentPage - 1)}>Prev</button>
        )}
        <span className="active">{currentPage}</span>
        {currentPage < totalPages && (
          <button onClick={() => setCurrentPage(currentPage + 1)}>Next</button>
        )}
      </div>
    </div>
  );
};

export default PatientDetails;
