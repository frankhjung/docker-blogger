# Google Blogger API Authentication Setup

To use this GitHub Action, you need to set up credentials for the Google Blogger API using **OAuth 2.0**.

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "blog-publishing-action").
3. Select the project you just created.

## 2. Enable the Blogger API

1. In the sidebar, go to **APIs & Services > Library**.
2. Search for **"Blogger API v3"**.
3. Click **Enable**.

## 3. Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**.
2. Select **External** (unless you have a Google Workspace organization) and click **Create**.
3. Fill in the required App Information (App name, User support email, Developer contact information).
4. Click **Save and Continue**.
5. **Scopes**: You can skip adding scopes here or search for `https://www.googleapis.com/auth/blogger` but strictly speaking, it's not mandatory to enforce it here for the token generation script if you approve specifically later. However, adding `../auth/blogger` is good practice.
6. **Test Users**: Add the email address of the Google account that owns the blog. **This is critical** for External apps in Testing mode.
7. Click **Save and Continue** until finished.

## 4. Create OAuth Client Credentials

1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials** -> **OAuth client ID**.
3. **Application type**: choose **Desktop app** (this allows the flow to run easily for a script).
4. Name it something like "Blogger CLI".
5. Click **Create**.
6. Note down the **Client ID** and **Client Secret**. (You can also download the JSON, but you'll just need those two strings).

## 5. Obtain a Refresh Token

You need to authorize the app once to get a "Refresh Token" which will be stored in your GitHub Secrets.

You can use the Google OAuth 2.0 Playground or a small local Python script.

### Option A: Using Google OAuth 2.0 Playground

1. Go to [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/).
2. Click the **Settings (gear icon)** in the top right.
    - Check **Use your own OAuth credentials**.
    - Enter your **OAuth Client ID** and **OAuth Client Secret**.
    - Click **Close**.
3. In **Step 1**, input the scope: `https://www.googleapis.com/auth/blogger`.
4. Click **Authorize APIs**.
5. Sign in with your Test User account and grant permission.
6. In **Step 2**, click **Exchange authorization code for tokens**.
7. Copy the **Refresh Token**.

### Option B: Using a Python Script (if you have the dependencies)

If you have `google-auth-oauthlib` installed locally:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/blogger"]
)

creds = flow.run_local_server(port=0)
print(f"Refresh Token: {creds.refresh_token}")
```

## 6. Configure GitHub Secrets

In your blog repository, go to **Settings > Secrets and variables > Actions** and add the following secrets:

- `BLOGGER_CLIENT_ID`: Your Client ID.
- `BLOGGER_CLIENT_SECRET`: Your Client Secret.
- `BLOGGER_REFRESH_TOKEN`: The Refresh Token you obtained.
- `BLOGGER_BLOG_ID`: The ID of your blog (you can find this in the URL of your Blogger dashboard: `blogger.com/blog/post/edit/<BLOG_ID>/...`).
