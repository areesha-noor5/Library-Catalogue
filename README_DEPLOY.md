Deployment instructions (Render)
------------------------------

These steps create a persistent, public URL for your Flask app by deploying the repo to Render (free tier available).

1) Push your repo to GitHub (already done) on the branch you want to deploy (e.g., `clean/library-data`).

2) Sign in to https://dashboard.render.com and create a new Web Service:
   - Click "New" → "Web Service".
   - Choose "Connect a repository" and pick this repository.
   - Branch: choose `clean/library-data` (or `main`).
   - Environment: "Docker" (Render will use the `Dockerfile` in repo).
   - Build and Start: default values are fine.
   - Click "Create Web Service".

3) Render will build the Docker image, run the container, and give you a permanent public URL like `https://your-servicename.onrender.com`.

Notes:
- The Dockerfile uses `gunicorn` to run the app and downloads NLTK stopwords at build time.
- If you prefer other hosts (Railway, Fly, Heroku), they can also run the Dockerfile or install via `requirements.txt`.

If you want, I can create a GitHub Action to auto-deploy on push, but connecting Render to the repo is the simplest path.
