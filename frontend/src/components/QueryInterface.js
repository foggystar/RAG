import React, { useState } from 'react';

const QueryInterface = ({ onQuery, activePdfs, loading, isStreaming }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e, isStreaming = false) => {
    e.preventDefault();
    if (!query.trim()) return;
    onQuery(query.trim(), isStreaming);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">💬 Ask Questions</h2>
      
      {activePdfs.length > 0 && (
        <div className="mb-4 p-3 bg-gray-100 rounded-md">
          <p className="text-sm font-medium text-gray-700">
            Using PDFs: <span className="text-blue-600">{activePdfs.join(', ')}</span>
          </p>
        </div>
      )}
      
      <form onSubmit={(e) => handleSubmit(e, false)} className="space-y-4">
        <div>
          <label htmlFor="user-query" className="block text-sm font-medium text-gray-700 mb-2">
            Your Question:
          </label>
          <textarea
            id="user-query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
            placeholder="Enter your question about the selected PDFs..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
            disabled={loading}
          />
        </div>
        
        <button 
          type="submit"
          disabled={loading || !query.trim() || activePdfs.length === 0}
          className="w-full bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition duration-200 flex items-center justify-center"
        >
          {loading && !isStreaming ? (
            <div className="loading mr-2"></div>
          ) : null}
          <span>{loading && !isStreaming ? 'Processing...' : 'Get Answer'}</span>
        </button>
        
        <button 
          type="button"
          onClick={(e) => handleSubmit(e, true)}
          disabled={loading || !query.trim() || activePdfs.length === 0}
          className="w-full bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition duration-200 flex items-center justify-center"
        >
          {loading && isStreaming ? (
            <div className="loading mr-2"></div>
          ) : null}
          <span>{loading && isStreaming ? 'Streaming...' : 'Get Streaming Answer'}</span>
        </button>
      </form>
      
      {activePdfs.length === 0 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800">
            ⚠️ Please select at least one PDF from the list to start asking questions
          </p>
        </div>
      )}
    </div>
  );
};

export default QueryInterface;