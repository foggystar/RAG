import React, { useRef } from 'react';

const PDFUpload = ({ onUpload, loading }) => {
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const file = fileInputRef.current?.files[0];
    
    if (!file) {
      return;
    }
    
    if (!file.name.endsWith('.pdf')) {
      alert('Please select a PDF file');
      return;
    }
    
    onUpload(file);
    fileInputRef.current.value = '';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">📁 Upload PDF</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <input 
            type="file" 
            ref={fileInputRef}
            accept=".pdf" 
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>
        <button 
          type="submit" 
          disabled={loading}
          className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition duration-200 flex items-center justify-center"
        >
          {loading ? (
            <div className="loading mr-2"></div>
          ) : null}
          <span>{loading ? 'Processing...' : 'Upload & Process PDF'}</span>
        </button>
      </form>
    </div>
  );
};

export default PDFUpload;