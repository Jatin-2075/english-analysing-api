# Deploy steps

1. Build (on your PC or the server, Node 18+):
   npm install
   npm run build        # creates the dist/ folder

2. Copy dist/ to the server:
   sudo mkdir -p /var/www/verba
   sudo cp -r dist/* /var/www/verba/

3. Nginx: use nginx.conf.example, then
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d your-domain.com     # HTTPS is required for the mic

4. Backend (FastAPI) must be running on 127.0.0.1:8000, e.g.
   uvicorn Backend.main:app --host 127.0.0.1 --port 8000
   (run it from the folder that contains Backend/; ffmpeg must be installed)

Because the frontend and API share one domain via /api, no CORS change is needed.
If you host the API on a different domain instead, set VITE_API_URL in .env.production
to that URL before building and add the frontend domain to allow_origins in app/main.py.
