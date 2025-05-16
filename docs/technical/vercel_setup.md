# Vercel Setup Guide

This document provides instructions for setting up Vercel for the QuantDB project.

## Prerequisites

- Vercel account (https://vercel.com)
- GitHub repository with the QuantDB code
- Supabase project already set up (see [Supabase Setup Guide](./supabase_setup.md))

## Setup Steps

### 1. Connect Your GitHub Repository

1. Log in to the [Vercel dashboard](https://vercel.com/dashboard)
2. Click "Add New" > "Project"
3. Import your GitHub repository
   - If you don't see your repository, you may need to configure the Vercel GitHub integration
   - Click "Adjust GitHub App Permissions" and add the repository

### 2. Configure Project Settings

1. After selecting your repository, configure the project settings:
   - **Project Name**: QuantDB (or your preferred name)
   - **Framework Preset**: Other
   - **Root Directory**: ./
   - **Build Command**: `pip install -r requirements.txt`
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

2. Configure environment variables:
   - Click "Environment Variables"
   - Add the following variables:
     - `DATABASE_URL`: Your Supabase PostgreSQL connection string
     - `SUPABASE_URL`: Your Supabase project URL
     - `SUPABASE_KEY`: Your Supabase API key
     - `SECRET_KEY`: A secure random string for JWT encoding
     - `ENVIRONMENT`: `production`

3. Click "Deploy"

### 3. Set Up Serverless Functions

For the FastAPI application, we'll use Vercel Serverless Functions:

1. Create a `vercel.json` file in the root of your repository:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "src/api/main.py"
    }
  ]
}
```

2. Create a `requirements.txt` file specifically for Vercel (if needed):

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-dotenv
pydantic
```

3. Commit and push these changes to your repository
4. Redeploy your Vercel project

### 4. Configure Custom Domain (Optional)

1. Go to the "Domains" tab in your project settings
2. Click "Add" and enter your domain
3. Follow the instructions to verify domain ownership
4. Configure DNS settings as instructed

### 5. Set Up Continuous Deployment

Vercel automatically deploys when you push to the main branch. To customize:

1. Go to the "Git" tab in your project settings
2. Configure production branch and preview branches
3. Set up build caching if needed

## Testing the Deployment

After deployment:

1. Visit your Vercel deployment URL
2. Test the API endpoints:
   - Root endpoint: `https://[your-vercel-url]/`
   - Health check: `https://[your-vercel-url]/api/v1/health`
   - API documentation: `https://[your-vercel-url]/api/v1/docs`

## Troubleshooting

### Deployment Failures

If your deployment fails:

1. Check the build logs in the Vercel dashboard
2. Ensure all dependencies are correctly specified
3. Verify that environment variables are correctly set
4. Check for any Python version compatibility issues

### API Issues

If the API doesn't work as expected:

1. Check the function logs in the Vercel dashboard
2. Ensure the database connection is working
3. Verify that the API routes are correctly configured
4. Check for any CORS issues if accessing from a frontend

## Limitations and Considerations

- **Cold Starts**: Serverless functions may experience cold starts
- **Execution Time**: Vercel has a 10-second execution limit for serverless functions
- **Memory**: Limited to 1GB RAM per function
- **Statelessness**: Functions are stateless, so don't rely on local file storage

## Next Steps

After setting up Vercel:

1. Set up monitoring and alerts
2. Configure custom error pages
3. Implement a CI/CD pipeline with GitHub Actions
4. Set up staging environments for testing
