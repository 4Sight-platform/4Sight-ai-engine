# Testing the Onboarding API

## Starting the Server

Run the FastAPI server:

```bash
cd c:/Users/Sanket\ Ghosh/Documents/Internships/TDSC/Platform/4Sight-ai-engine/Seo_automation
python -m uvicorn api.app:app --reload --port 8001
```

Or run directly:

```bash
python api/app.py
```

## Accessing Swagger UI

Once the server is running, open your browser and navigate to:

```
http://localhost:8001/docs
```

## Testing the Onboarding Endpoint

### Endpoint Details

- **URL**: `POST /api/v1/onboarding/complete`
- **Description**: Complete onboarding process with all 8 pages of data

### Sample Request Body

Copy and paste this JSON into Swagger UI:

```json
{
  "business_name": "TechStart Solutions",
  "website_url": "https://techstartsolutions.com",
  "business_description": "We provide innovative technology solutions for small and medium businesses, specializing in cloud infrastructure, cybersecurity, and custom software development.",
  "gsc_connected": false,
  "location_scope": "nationwide",
  "selected_locations": [],
  "customer_description": "Small to medium-sized businesses looking to modernize their IT infrastructure and improve operational efficiency",
  "search_intent": [
    "information",
    "action-focused"
  ],
  "products": [
    "Cloud Migration Service",
    "Cybersecurity Suite",
    "Custom CRM Software"
  ],
  "services": [
    "IT Consulting",
    "24/7 Technical Support",
    "Infrastructure Monitoring",
    "Security Audits"
  ],
  "differentiators": [
    "20 years combined team experience",
    "24/7 customer support",
    "Money-back guarantee",
    "Free security audit"
  ],
  "seo_goals": [
    "organic_traffic",
    "search_visibility",
    "top_rankings"
  ],
  "page_urls": {
    "home": "https://techstartsolutions.com/",
    "product": "https://techstartsolutions.com/products",
    "contact": "https://techstartsolutions.com/contact",
    "about": "https://techstartsolutions.com/about",
    "blog": "https://techstartsolutions.com/blog"
  },
  "reporting_channels": [
    "email",
    "dashboard"
  ],
  "email_addresses": [
    "admin@techstartsolutions.com",
    "seo@techstartsolutions.com"
  ],
  "report_frequency": "weekly"
}
```

### Expected Response

The API will return:

```json
{
  "status": "success",
  "message": "Onboarding completed successfully",
  "user_id": "user_xxxxxxxxxxxx",
  "data": {
    "business_info": { ... },
    "gsc_connected": false,
    "audience": { ... },
    "portfolio": { ... },
    "seo_goals": [...],
    "generated_keywords": [
      {
        "keyword": "cloud migration services",
        "score": 8.5
      },
      ...
    ],
    "selected_keywords": [...],
    "page_urls": { ... },
    "reporting": { ... }
  }
}
```

## Other Available Endpoints

### Get User Profile

```
GET /api/v1/profile/{user_id}
```

Replace `{user_id}` with the user_id returned from the onboarding endpoint.

### Get All Profiles

```
GET /api/v1/profiles
```

Returns all user profiles in the system.

## Validation Rules

The API validates the following:

### Required Fields
- `business_name`: 2-100 characters
- `website_url`: Valid URL (auto-adds https:// if missing)
- `business_description`: Not empty, max 500 characters
- `customer_description`: Not empty
- `search_intent`: 1-2 values from: information, comparison, deal, action-focused
- `seo_goals`: At least 1 from: organic_traffic, search_visibility, local_visibility, top_rankings
- `reporting_channels`: At least 1 from: email, dashboard
- `report_frequency`: One of: daily, weekly, monthly

### Optional Fields
- `gsc_connected`: Boolean (default: false)
- `selected_locations`: List of strings, max 5 items
- `products`: List of strings, max 10 items
- `services`: List of strings, max 10 items
- `differentiators`: List of strings, max 5 items
- `email_addresses`: List of valid emails, max 5 items

### Location Scope
Must be one of: `local`, `regional`, `nationwide`, `international`

## Error Handling

The API returns appropriate HTTP status codes:

- `201 Created`: Onboarding completed successfully
- `400 Bad Request`: Validation error
- `404 Not Found`: Profile not found (for GET endpoints)
- `422 Unprocessable Entity`: Invalid request format
- `500 Internal Server Error`: Server error

## Notes

- The API automatically generates and ranks keywords based on your business profile
- Top 15 keywords are selected and saved
- All data is stored in `storage/user_profiles/{user_id}/` directory
- Each profile gets a unique user_id in format: `user_xxxxxxxxxxxx`
