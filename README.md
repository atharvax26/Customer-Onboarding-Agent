# Customer Onboarding Agent

A single-tenant SaaS platform that transforms product documentation into personalized, role-based onboarding experiences using AI-powered document processing and real-time engagement analytics.

## Features

- **AI-Powered Document Processing**: Uses Claude API to process documentation into summaries and actionable tasks
- **Role-Based Onboarding**: Customized flows for Developers (5 steps), Business Users (3 steps), and Admins
- **Real-Time Engagement Scoring**: Monitors user activity and calculates engagement scores
- **Automated Interventions**: Provides contextual help when engagement drops below threshold
- **Analytics Dashboard**: Comprehensive reporting on activation rates and user behavior

## Architecture

- **Backend**: FastAPI with SQLAlchemy and SQLite
- **Frontend**: React with Vite and TypeScript
- **AI Integration**: Anthropic Claude API for document processing
- **Testing**: pytest + Hypothesis (backend), Vitest + Testing Library (frontend)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Claude API key from Anthropic

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd customer-onboarding-agent
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Claude API key and other configuration
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

Or run manually:

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Testing

**Backend tests:**
```bash
cd backend
pytest
```

**Frontend tests:**
```bash
cd frontend
npm run test
```

## Project Structure

```
customer-onboarding-agent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── database.py     # SQLAlchemy models and database config
│   │   └── routers/        # API route handlers
│   ├── tests/              # Backend tests
│   ├── main.py             # FastAPI application entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── test/           # Frontend tests
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Docker orchestration
└── README.md              # This file
```

## API Endpoints

- **Authentication**: `/api/auth/*`
- **Onboarding**: `/api/onboarding/*`
- **Document Processing**: `/api/scaledown/*`
- **Analytics**: `/api/analytics/*`

## Development

This project follows a spec-driven development approach. See `.kiro/specs/customer-onboarding-agent/` for detailed requirements, design, and implementation tasks.

## License

MIT License - see LICENSE file for details.