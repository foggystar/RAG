import React, { useState } from 'react';

const PDFList = ({ 
  pdfs, 
  activePdfs, 
  onDeletePDF, 
  onSetActivePdfs, 
  onRefresh, 
  loading 
}) => {
  const [selectedPdfs, setSelectedPdfs] = useState(activePdfs);

  const handleCheckboxChange = (pdfName) => {
    const newSelected = selectedPdfs.includes(pdfName)
      ? selectedPdfs.filter(pdf => pdf !== pdfName)
      : [...selectedPdfs, pdfName];
    setSelectedPdfs(newSelected);
  };

  const handleSetActivePdfs = () => {
    onSetActivePdfs(selectedPdfs);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">📚 Imported PDFs</h2>
      
      {pdfs.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No PDFs imported yet</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {pdfs.map((pdf, index) => (
            <div 
              key={pdf} 
              className="flex items-center justify-between space-x-2 p-2 rounded hover:bg-gray-50"
            >
              <div className="flex items-center space-x-2 flex-1">
                <input
                  type="checkbox"
                  id={`pdf-${index}`}
                  checked={selectedPdfs.includes(pdf)}
                  onChange={() => handleCheckboxChange(pdf)}
                  disabled={loading}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label 
                  htmlFor={`pdf-${index}`} 
                  className="text-sm font-medium text-gray-700 cursor-pointer flex-1 truncate"
                >
                  {pdf}
                </label>
              </div>
              <button 
                onClick={() => onDeletePDF(pdf)}
                disabled={loading}
                className="text-red-500 hover:text-red-700 hover:bg-red-50 disabled:opacity-50 p-1 rounded transition-colors duration-200 text-xs"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      )}
      
      <div className="mt-4 flex space-x-2">
        <button 
          onClick={handleSetActivePdfs}
          disabled={loading || pdfs.length === 0}
          className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition duration-200"
        >
          Set Active PDFs
        </button>
        <button 
          onClick={onRefresh}
          disabled={loading}
          className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition duration-200"
        >
          Refresh
        </button>
      </div>
    </div>
  );
};

export default PDFList;