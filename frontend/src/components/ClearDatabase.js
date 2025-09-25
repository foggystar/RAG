import React from 'react';

const ClearDatabase = ({ onClear, loading }) => {
  const handleClear = () => {
    onClear();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-red-600">🗑️ Clear Database</h2>
      <p className="text-gray-600 mb-4">
        This will remove all imported PDFs from the database. This action cannot be undone.
      </p>
      <button 
        onClick={handleClear}
        disabled={loading}
        className="w-full bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition duration-200"
      >
        {loading ? 'Clearing...' : 'Clear All Data'}
      </button>
    </div>
  );
};

export default ClearDatabase;