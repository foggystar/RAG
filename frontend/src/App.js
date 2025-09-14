import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PDFUpload from './components/PDFUpload';
import PDFList from './components/PDFList';
import QueryInterface from './components/QueryInterface';
import ClearDatabase from './components/ClearDatabase';
import Toast from './components/Toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [pdfs, setPdfs] = useState([]);
  const [activePdfs, setActivePdfs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [answer, setAnswer] = useState('');
  const [streamingAnswer, setStreamingAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Fetch PDF list
  const fetchPdfs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/pdfs`);
      if (response.data.success) {
        setPdfs(response.data.data.pdfs);
      }
    } catch (error) {
      showToast('Error fetching PDF list', 'error');
      console.error('Error fetching PDFs:', error);
    }
  };

  // Initialize
  useEffect(() => {
    fetchPdfs();
  }, []);

  // Handle PDF upload
  const handlePDFUpload = async (file) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE_URL}/upload-pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        showToast('PDF uploaded and processed successfully', 'success');
        fetchPdfs();
      } else {
        showToast('Failed to process PDF', 'error');
      }
    } catch (error) {
      showToast('Error uploading PDF: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setLoading(false);
    }
  };

  // Handle delete PDF
  const handleDeletePDF = async (pdfName) => {
    if (!window.confirm(`Are you sure you want to delete "${pdfName}" and all its associated data? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE_URL}/api/pdfs/${encodeURIComponent(pdfName)}`);
      
      if (response.data.success) {
        // Remove from active PDFs if it was active
        if (activePdfs.includes(pdfName)) {
          setActivePdfs(activePdfs.filter(pdf => pdf !== pdfName));
        }
        
        fetchPdfs();
        showToast(`Successfully deleted "${pdfName}"`, 'success');
      } else {
        showToast(`Failed to delete "${pdfName}"`, 'error');
      }
    } catch (error) {
      showToast(`Error deleting "${pdfName}": ${error.response?.data?.detail || error.message}`, 'error');
    }
  };

  // Handle set active PDFs
  const handleSetActivePdfs = async (selectedPdfs) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/set-active-pdfs`, {
        pdf_names: selectedPdfs
      });

      if (response.data.success) {
        setActivePdfs(selectedPdfs);
        showToast(`Set ${selectedPdfs.length} PDFs as active`, 'success');
      } else {
        showToast('Failed to set active PDFs', 'error');
      }
    } catch (error) {
      showToast('Error setting active PDFs: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Handle query
  const handleQuery = async (query, isStreaming = false) => {
    if (activePdfs.length === 0) {
      showToast('Please select at least one PDF first', 'error');
      return;
    }

    setLoading(true);
    setAnswer('');
    setStreamingAnswer('');
    setIsStreaming(false);

    try {
      if (isStreaming) {
        setIsStreaming(true);
        const response = await fetch(`${API_BASE_URL}/api/query/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query,
            active_pdfs: activePdfs
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullAnswer = '';

        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            break;
          }
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const content = line.slice(6);
              
              if (content === '[DONE]') {
                break;
              }
              
              if (content.trim() && !content.startsWith('Error:')) {
                fullAnswer += content;
                setStreamingAnswer(fullAnswer);
              } else if (content.startsWith('Error:')) {
                throw new Error(content);
              }
            }
          }
        }
        
        setAnswer(fullAnswer);
        showToast('Streaming answer completed successfully', 'success');
      } else {
        const response = await axios.post(`${API_BASE_URL}/api/query`, {
          query: query,
          active_pdfs: activePdfs
        });

        if (response.data.success) {
          setAnswer(response.data.data.answer);
          showToast('Answer generated successfully', 'success');
        } else {
          showToast('Failed to get answer', 'error');
        }
      }
    } catch (error) {
      showToast('Error processing query: ' + (error.response?.data?.detail || error.message), 'error');
      console.error('Query error:', error);
    } finally {
      setLoading(false);
      setIsStreaming(false);
    }
  };

  // Handle clear database
  const handleClearDatabase = async () => {
    if (!window.confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE_URL}/api/clear`);
      
      if (response.data.success) {
        setActivePdfs([]);
        setAnswer('');
        setStreamingAnswer('');
        fetchPdfs();
        showToast('Database cleared successfully', 'success');
      } else {
        showToast('Failed to clear database', 'error');
      }
    } catch (error) {
      showToast('Error clearing database: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">RAG System</h1>
          <p className="text-gray-600">PDF-based Retrieval-Augmented Generation</p>
          <div className="mt-4 flex justify-center space-x-4">
            <div className="bg-blue-100 px-3 py-1 rounded">
              <span className="text-blue-800 font-semibold">Total PDFs: </span>
              <span className="text-blue-900">{pdfs.length}</span>
            </div>
            <div className="bg-green-100 px-3 py-1 rounded">
              <span className="text-green-800 font-semibold">Active PDFs: </span>
              <span className="text-green-900">{activePdfs.length}</span>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - PDF Management */}
          <div className="space-y-6">
            <PDFUpload onUpload={handlePDFUpload} loading={loading} />
            <PDFList 
              pdfs={pdfs} 
              activePdfs={activePdfs}
              onDeletePDF={handleDeletePDF}
              onSetActivePdfs={handleSetActivePdfs}
              onRefresh={fetchPdfs}
              loading={loading}
            />
            <ClearDatabase onClear={handleClearDatabase} loading={loading} />
          </div>

          {/* Right Column - Query Interface */}
          <div className="space-y-6">
            <QueryInterface 
              onQuery={handleQuery}
              activePdfs={activePdfs}
              loading={loading}
              isStreaming={isStreaming}
            />
            
            {/* Answer Display */}
            {(answer || streamingAnswer) && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">🤖 Answer</h2>
                <div className="prose max-w-none markdown-content bg-gray-50 p-4 rounded-md">
                  {isStreaming ? (
                    <div>
                      <div className="text-blue-600 text-sm mb-2">
                        📡 Streaming... <span className="animate-pulse">●</span>
                      </div>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamingAnswer}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {answer}
                    </ReactMarkdown>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}
    </div>
  );
}

export default App;