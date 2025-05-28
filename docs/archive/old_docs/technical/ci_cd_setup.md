# CI/CD Setup Guide

This document provides instructions for setting up Continuous Integration and Continuous Deployment (CI/CD) for the QuantDB project.

## Overview

The CI/CD pipeline for QuantDB consists of:

1. **Continuous Integration**: Automated testing and code quality checks using GitHub Actions
2. **Continuous Deployment**: Automated deployment to Vercel when changes are pushed to the main branch

## GitHub Actions Setup

### 1. CI Workflow

The CI workflow is defined in `.github/workflows/ci.yml` and includes:

- Running tests
- Checking code quality
- Building the application

The workflow runs on:
- Push to the main branch
- Pull requests to the main branch

### 2. Configuration

The CI workflow is already configured in the repository. To customize it:

1. Edit the `.github/workflows/ci.yml` file
2. Commit and push your changes

### 3. Secrets

To use external services in your CI workflow, you may need to add secrets:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets" > "Actions"
3. Click "New repository secret"
4. Add secrets as needed (e.g., `SUPABASE_URL`, `SUPABASE_KEY`)

## Vercel Deployment

### 1. Automatic Deployments

Vercel automatically deploys your application when you push to the main branch:

1. Push changes to the main branch
2. Vercel detects the changes and starts a new deployment
3. The deployment is automatically published when complete

### 2. Preview Deployments

Vercel creates preview deployments for pull requests:

1. Create a pull request
2. Vercel creates a preview deployment
3. Review the changes in the preview environment
4. Merge the pull request when ready

### 3. Environment Variables

Set environment variables in the Vercel dashboard:

1. Go to your project in the Vercel dashboard
2. Click on "Settings" > "Environment Variables"
3. Add the necessary environment variables
4. Choose which environments (Production, Preview, Development) should use each variable

## Complete CI/CD Flow

The complete CI/CD flow works as follows:

1. Developer creates a feature branch and makes changes
2. Developer creates a pull request to the main branch
3. GitHub Actions runs tests and code quality checks
4. Vercel creates a preview deployment
5. Team reviews the changes and the preview deployment
6. When approved, the pull request is merged to the main branch
7. GitHub Actions runs tests again
8. Vercel deploys to production

## Best Practices

### 1. Branch Protection

Set up branch protection rules for the main branch:

1. Go to your GitHub repository
2. Click on "Settings" > "Branches"
3. Click "Add rule"
4. Set the branch name pattern to `main`
5. Enable "Require status checks to pass before merging"
6. Select the status checks that must pass
7. Enable "Require pull request reviews before merging"
8. Save the rule

### 2. Conventional Commits

Use conventional commits to make the changelog generation easier:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example: `feat: add user authentication`

### 3. Semantic Versioning

Use semantic versioning for releases:

- **Major version**: Incompatible API changes
- **Minor version**: Add functionality in a backward-compatible manner
- **Patch version**: Backward-compatible bug fixes

## Troubleshooting

### GitHub Actions Issues

If GitHub Actions workflows fail:

1. Check the workflow logs in the GitHub Actions tab
2. Ensure all dependencies are correctly specified
3. Verify that secrets are correctly set
4. Check for any syntax errors in the workflow file

### Vercel Deployment Issues

If Vercel deployments fail:

1. Check the build logs in the Vercel dashboard
2. Ensure all environment variables are correctly set
3. Verify that the build command is correct
4. Check for any compatibility issues with Vercel
