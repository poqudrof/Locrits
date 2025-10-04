# Secrets Installation Guide for Locrits Platform

This guide explains how to configure all the required secrets and environment variables for deploying the Locrits platform to production.

## 📋 Overview

The platform requires secrets for:
- **Firebase Configuration** - API keys and project settings
- **Deployment Services** - Firebase Hosting, Netlify, or Vercel
- **Authentication Services** - Service accounts and tokens

## 🔥 Firebase Secrets

### Required Firebase Environment Variables

Add these secrets to your GitHub repository settings under **Settings > Secrets and variables > Actions**:

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `VITE_FIREBASE_API_KEY` | Firebase Web API Key | Firebase Console > Project Settings > General > Web apps |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase Auth Domain | Usually `{project-id}.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Firebase Project ID | Firebase Console > Project Settings > General |
| `VITE_FIREBASE_STORAGE_BUCKET` | Firebase Storage Bucket | Firebase Console > Storage > Settings |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase Messaging Sender ID | Firebase Console > Project Settings > Cloud Messaging |
| `VITE_FIREBASE_APP_ID` | Firebase App ID | Firebase Console > Project Settings > General > Web apps |
| `VITE_FIREBASE_MEASUREMENT_ID` | Google Analytics Measurement ID | Firebase Console > Analytics > Settings (optional) |

### Firebase Service Account (for Rules Deployment)

1. **Create Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Select your Firebase project
   - Navigate to **IAM & Admin > Service Accounts**
   - Click **Create Service Account**
   - Name: `locrits-github-deploy`
   - Roles:
     - `Firebase Rules Admin`
     - `Firebase Hosting Admin`
     - `Cloud Datastore Index Admin`

2. **Generate Private Key:**
   - Click on the created service account
   - Go to **Keys** tab
   - Click **Add Key > Create new key**
   - Choose **JSON** format
   - Download the JSON file

3. **Add to GitHub Secrets:**
   - Copy the entire content of the JSON file
   - Add as secret `FIREBASE_SERVICE_ACCOUNT_LOCRIT`

## 🌐 Deployment Platform Secrets

Choose **ONE** of the following deployment platforms:

### Option 1: Firebase Hosting (Recommended)

Firebase Hosting is already configured if you have the `FIREBASE_SERVICE_ACCOUNT_LOCRIT` secret above.

### Option 2: Netlify

1. **Create Netlify Account** and site
2. **Get Auth Token:**
   - Go to [Netlify User Settings](https://app.netlify.com/user/applications#personal-access-tokens)
   - Create new access token
   - Add as secret `NETLIFY_AUTH_TOKEN`

3. **Get Site ID:**
   - Go to your site's dashboard
   - Copy Site ID from **Site settings > General > Site details**
   - Add as secret `NETLIFY_SITE_ID`

4. **Get Site Name (for preview URLs):**
   - Copy Site name from dashboard
   - Add as secret `NETLIFY_SITE_NAME`

### Option 3: Vercel

1. **Create Vercel Account** and project
2. **Get Vercel Token:**
   - Go to [Vercel Account Settings](https://vercel.com/account/tokens)
   - Create new token
   - Add as secret `VERCEL_TOKEN`

3. **Get Organization ID:**
   - Run `npx vercel link` in your project
   - Copy Organization ID from `.vercel/project.json`
   - Add as secret `VERCEL_ORG_ID`

4. **Get Project ID:**
   - Copy Project ID from `.vercel/project.json`
   - Add as secret `VERCEL_PROJECT_ID`

## 🔧 Local Development Setup

### Platform (.env.local)

Create `platform/.env.local`:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=locrit.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=locrit
VITE_FIREBASE_STORAGE_BUCKET=locrit.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=150648923940
VITE_FIREBASE_APP_ID=1:150648923940:web:26407f6900045bd23ff5b1
VITE_FIREBASE_MEASUREMENT_ID=G-92CRH1S5QQ

# Development flags
VITE_NODE_ENV=development
```

### Backend (.env)

Create `src/.env` for the Python backend:

```env
# Firebase Configuration (for backend services)
FIREBASE_API_KEY=your_api_key_here
FIREBASE_AUTH_DOMAIN=locrit.firebaseapp.com
FIREBASE_PROJECT_ID=locrit
FIREBASE_STORAGE_BUCKET=locrit.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=150648923940
FIREBASE_APP_ID=1:150648923940:web:26407f6900045bd23ff5b1

# Google Cloud Service Account (optional for local development)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Development settings
FLASK_ENV=development
FLASK_DEBUG=True
```

## 🚀 Production Deployment Steps

### 1. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings > Secrets and variables > Actions**
3. Add all required secrets from the tables above

### 2. Firebase Configuration

1. **Enable Firebase Services:**
   - Firestore Database
   - Firebase Authentication
   - Firebase Storage
   - Firebase Hosting (if using Firebase for hosting)

2. **Configure Authentication:**
   - Enable Email/Password provider
   - Enable Google OAuth provider
   - Add authorized domains: `localhost`, `your-domain.com`

3. **Deploy Firestore Rules:**
   ```bash
   # The GitHub Action will handle this automatically
   # Or run manually: firebase deploy --only firestore:rules
   ```

### 3. Trigger Deployment

1. **Push to main branch:**
   ```bash
   git add .
   git commit -m "Configure production deployment"
   git push origin main
   ```

2. **Monitor deployment:**
   - Go to **Actions** tab in GitHub
   - Watch the deployment workflow progress

### 4. Configure Custom Domain (Optional)

#### Firebase Hosting
1. Go to Firebase Console > Hosting
2. Click **Add custom domain**
3. Follow DNS configuration instructions

#### Netlify
1. Go to site dashboard > Domain settings
2. Add custom domain
3. Configure DNS records

#### Vercel
1. Go to project dashboard > Domains
2. Add custom domain
3. Configure DNS records

## 🔒 Security Best Practices

### Secret Management
- **Never commit secrets** to version control
- **Rotate secrets regularly** (quarterly recommended)
- **Use least-privilege principle** for service accounts
- **Monitor secret usage** in deployment logs

### Firebase Security
- **Review Firestore rules** before deployment
- **Enable App Check** for production
- **Configure CORS** for web domains only
- **Enable audit logs** for Firebase Admin SDK

### Environment Variables
- **Separate dev/staging/prod** configurations
- **Validate all required vars** in CI/CD
- **Use different Firebase projects** for each environment

## 🐛 Troubleshooting

### Common Issues

1. **Build fails with Firebase errors:**
   - Check that all `VITE_FIREBASE_*` secrets are set
   - Verify Firebase project ID matches secrets

2. **Deployment fails with permissions:**
   - Verify service account has correct roles
   - Check that service account JSON is valid

3. **Authentication doesn't work:**
   - Add your domain to Firebase authorized domains
   - Check Auth provider configuration

4. **Missing environment variables:**
   - Use `env | grep VITE_` to check variables in CI
   - Verify secret names match exactly (case-sensitive)

### Debug Commands

```bash
# Test Firebase connection locally
npm run dev

# Validate Firebase rules
firebase firestore:rules:check

# Test build locally
npm run build

# Deploy manually
firebase deploy --project locrit
```

## 📞 Support

If you encounter issues:

1. **Check GitHub Actions logs** for detailed error messages
2. **Verify all secrets** are properly configured
3. **Test locally first** before deploying to production
4. **Check Firebase Console** for quota limits and billing

## 🔄 Updates and Maintenance

### Regular Tasks
- **Update dependencies** monthly
- **Review and rotate secrets** quarterly
- **Monitor Firebase usage** and costs
- **Review security rules** after major updates

### Backup Strategy
- **Export Firestore data** regularly
- **Backup Firebase project configuration**
- **Document all custom domain configurations**
- **Keep service account keys secure and backed up**

---

*This guide covers the complete setup for production deployment. Keep this document updated as your infrastructure evolves.*