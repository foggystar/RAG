# React Frontend for RAG System

This is the React-based frontend for the RAG (Retrieval-Augmented Generation) system.

## Features

- **PDF Upload**: Upload and process PDF files
- **PDF Management**: View, select, and delete imported PDFs
- **Query Interface**: Ask questions about selected PDFs
- **Streaming Responses**: Real-time streaming answers
- **Markdown Rendering**: Properly formatted answers with support for tables, images, and code
- **Responsive Design**: Works on desktop and mobile devices

## Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will run on `http://localhost:3000` and proxy API requests to the backend at `http://localhost:8000`.

## Environment Variables

Create a `.env` file in the frontend directory to configure the API URL:

```
REACT_APP_API_URL=http://localhost:8000
```

## Components

- `App.js`: Main application component with state management
- `PDFUpload.js`: PDF file upload component
- `PDFList.js`: List and manage imported PDFs
- `QueryInterface.js`: Query input and submission
- `ClearDatabase.js`: Database clearing functionality
- `Toast.js`: Notification system

## Dependencies

- React 18
- React Router (for future routing)
- Axios (for API calls)
- React Markdown (for answer formatting)
- Tailwind CSS (styling)

## Build for Production

```bash
npm run build
```

This will create a `build` directory with optimized production files.