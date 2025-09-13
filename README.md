# Query Mitra

Query Mitra is a data visualization and query application that allows you to upload datasets, run queries, and visualize the results.

## Project Structure

```
Backend/                 # Python Flask backend
  App/                   # Main application code
    models/              # Data models
    routes/              # API routes
    services/            # Business logic
  config.py              # Configuration
  requirements.txt       # Python dependencies
  run.py                 # Entry point

Frontend/                # React TypeScript frontend
  components/            # React components
  services/              # API services
  App.tsx                # Main application component
  index.tsx              # Entry point
```

## Setup and Running

### Option 1: Using Docker Compose (recommended)

1. Make sure you have Docker and Docker Compose installed
2. Run the following command in the project root directory:

```bash
docker-compose up
```

3. Access the application at http://localhost:3000

### Option 2: Manual Setup

#### Backend Setup

1. Navigate to the Backend directory:

```bash
cd Backend
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Make sure MongoDB is installed and running at mongodb://localhost:27017

5. Run the backend server:

```bash
python run.py
```

The backend will be available at http://localhost:5000

#### Frontend Setup

1. Navigate to the Frontend directory:

```bash
cd Frontend
```

2. Install dependencies:

```bash
npm install
```

3. Run the development server:

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Features

- Upload CSV datasets
- Query datasets using:
  - Natural language queries
  - SQL-like queries
  - MongoDB aggregation pipelines
- Visualize query results as tables or charts
- Interactive UI with dark/light mode support

## API Endpoints

- `GET /api/datasets` - Get list of datasets
- `POST /api/datasets` - Upload a new dataset
- `POST /api/queries/execute` - Execute a query on a dataset

## Technology Stack

- **Backend**: Python, Flask, MongoDB
- **Frontend**: TypeScript, React, Tailwind CSS, Recharts
