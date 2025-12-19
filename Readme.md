# 4Sight AI Engine

**Version 2.0.0**

A FastAPI-based backend service providing intelligent SEO automation and onboarding services for the 4Sight platform. This engine handles user onboarding, profile management, and keyword generation for SEO optimization.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Project Structure](#-project-structure)

---

## ✨ Features

- **Incremental Onboarding**: 8-page progressive onboarding flow for collecting business information
- **Intelligent Keyword Generation**: AI-powered keyword suggestions based on business profile
- **Profile Management**: Create, update, and retrieve user profiles
- **RESTful API**: Clean, documented API endpoints with automatic validation
- **Environment-based Configuration**: Secure credential management via environment variables
- **CORS Support**: Configured for seamless frontend integration

---

## 🏗️ Architecture

### Core Components

- **`app.py`**: FastAPI application setup with CORS and routing
- **`platform_services.py`**: API endpoint definitions for all onboarding pages
- **`base_requests.py`**: Pydantic models for request/response validation
- **`config.py`**: Environment variable configuration using Pydantic Settings
- **`onboarding/`**: Business logic modules
  - `fetch_profile_data.py`: Profile management and storage
  - `keyword_generation/`: AI-powered keyword analysis and ranking

### Technology Stack

- **Framework**: FastAPI
- **Validation**: Pydantic v2
- **AI/LLM**: Google Gemini API
- **Authentication**: Google OAuth 2.0 (GSC integration)
- **Storage**: File-based JSON storage

---

## 🚀 Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/4Sight-platform/4Sight-ai-engine.git
   cd 4Sight-ai-engine
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

The server will start at `http://localhost:8001`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Google Gemini API (Required for keyword generation)
GEMINI_API_KEY=your_gemini_api_key_here

# Google Search Console OAuth (Required for GSC features)
GSC_CLIENT_ID=your_client_id.apps.googleusercontent.com
GSC_CLIENT_SECRET=your_client_secret
GSC_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
GSC_OAUTH_SCOPE=https://www.googleapis.com/auth/webmasters

# Google Keyword Planner API (Optional)
KP_DEVELOPER_TOKEN=your_developer_token
KP_CLIENT_ID=your_kp_client_id
KP_CLIENT_SECRET=your_kp_client_secret
KP_REFRESH_TOKEN=your_refresh_token
KP_CUSTOMER_ID=your_customer_id

# Google Custom Search API (Optional)
CUSTOM_SEARCH_API_KEY=your_api_key
CUSTOM_SEARCH_CX=your_search_engine_id

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=4Sight AI Engine

# CORS Origins (comma-separated)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Storage
STORAGE_DIR=storage/user_profiles
```

### Getting API Credentials

- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Google OAuth Credentials**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

---

## 📡 API Endpoints

### Interactive Documentation

Access the auto-generated API documentation:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Onboarding Endpoints

All endpoints are prefixed with `/api/v1`

#### **Page 1: Business Information**
```http
POST /onboarding/page1/business-info
```
Submit business name, website URL, and description. Returns a new `user_id`.

**Request Body:**
```json
{
  "business_name": "TechStart Solutions",
  "website_url": "https://techstartsolutions.com",
  "business_description": "We provide innovative technology solutions..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Business information saved successfully",
  "user_id": "user_930d408caf01",
  "data": { ... }
}
```

#### **Page 2: Google Search Console**
```http
POST /onboarding/page2/gsc
```
Save GSC connection status.

**Request Body:**
```json
{
  "user_id": "user_930d408caf01",
  "gsc_connected": false
}
```

#### **Page 3: Audience & Search Intent**
```http
POST /onboarding/page3/audience
```
Define target audience and search intent (1-2 selections).

**Request Body:**
```json
{
  "user_id": "user_930d408caf01",
  "location_scope": "nationwide",
  "selected_locations": [],
  "customer_description": "Small to medium-sized businesses...",
  "search_intent": ["information", "action"]
}
```

**Valid Search Intents**: `information`, `comparison`, `deal`, `action` (or `action-focused`)

#### **Page 4: Business Portfolio**
```http
POST /onboarding/page4/portfolio
```
Submit products, services, and differentiators.

#### **Page 5: SEO Goals**
```http
POST /onboarding/page5/goals
```
Define SEO objectives.

**Valid Goals**: `organic_traffic`, `search_visibility`, `local_visibility`, `top_rankings`

#### **Page 6: Keyword Generation**
```http
GET /onboarding/page6/keywords/{user_id}
```
Generate AI-powered keyword suggestions based on profile.

**Response:**
```json
{
  "status": "success",
  "message": "Generated 30 keywords successfully",
  "user_id": "user_930d408caf01",
  "data": {
    "generated_keywords": [
      { "keyword": "cloud migration services", "score": 8.5 },
      ...
    ],
    "selected_keywords": [ ... ],
    "total_generated": 30,
    "total_selected": 15
  }
}
```

#### **Page 7: Content Filter**
```http
POST /onboarding/page7/content-filter
```
Configure page URLs for content optimization.

#### **Page 8: Reporting Settings**
```http
POST /onboarding/page8/reporting
```
Set up reporting preferences. Marks onboarding as complete.

**Request Body:**
```json
{
  "user_id": "user_930d408caf01",
  "reporting_channels": ["email", "dashboard"],
  "email_addresses": ["admin@example.com"],
  "report_frequency": "weekly"
}
```

---

## 🧪 Testing

### Using Swagger UI

1. Start the server: `python app.py`
2. Navigate to http://localhost:8001/docs
3. Expand any endpoint and click "Try it out"
4. Fill in the request body and execute

### Using cURL

**Example: Create Business Profile**
```bash
curl -X POST "http://localhost:8001/api/v1/onboarding/page1/business-info" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "TechStart Solutions",
    "website_url": "https://techstartsolutions.com",
    "business_description": "Innovative technology solutions for businesses"
  }'
```

### Validation Rules

- **Business Name**: 2-100 characters
- **Website URL**: Valid URL format
- **Business Description**: Max 500 characters
- **Search Intent**: 1-2 selections required
- **Location Scope**: `local`, `regional`, `nationwide`, or `international`
- **Email Addresses**: Valid email format, max 5
- **Report Frequency**: `daily`, `weekly`, or `monthly`

---

## 📂 Project Structure

```
4Sight-ai-engine/
├── app.py                      # FastAPI application entry point
├── platform_services.py        # API endpoint definitions
├── base_requests.py            # Pydantic request/response models
├── config.py                   # Environment configuration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
│
├── onboarding/                 # Business logic modules
│   ├── fetch_profile_data.py  # Profile management
│   ├── keyword_generation/    # AI keyword generation
│   │   ├── keyword_suggester.py
│   │   ├── keyword_analyzer.py
│   │   └── prompt_templates.py
│   ├── ga_gsc_connection/     # Google Analytics/GSC integration
│   └── competitor_analysis/   # Competitor research tools
│
├── storage/                    # User profile storage
│   └── user_profiles/
│       └── user_*/             # Individual user data
│
└── GSC_automation/             # Google Search Console automation
```

---

## 🔒 Security Notes

- Never commit `.env` file to version control
- Rotate API credentials regularly
- Use environment-specific configurations
- Enable HTTPS in production
- Implement rate limiting for production deployment

---

## 📝 API Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Validation error
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Invalid request format
- `500 Internal Server Error`: Server error

---

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add proper type hints
3. Update documentation for API changes
4. Test endpoints before committing

---

## 📧 Support

For issues or questions, contact the 4Sight Platform team.

---

**Last Updated**: December 2024  
**Version**: 2.0.0
