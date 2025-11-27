# Deploying Eldro AI Assistant to Koyeb

1. Put code into a GitHub repo (public or linked private).
2. Create a Koyeb account and "Create App".
   - Choose "Deploy from Git" and point to your repo & branch.
   - Container will be built using the Dockerfile in repo.
3. In Koyeb app settings -> Environment variables, add:
   - TELEGRAM_BOT_TOKEN
   - GEMINI_API_KEY
   - EXPOSED_URL (you can set it to the public URL Koyeb shows after deploy; or set after first deploy)
4. Ensure health check /port is default (Koyeb will check the exposed port).
5. Deploy. Check logs in Koyeb if build fails (common: missing env or incorrect API endpoints).
6. After deployment: call https://<your-app>.koyeb.app/set_webhook (open in browser or curl). This will tell Telegram where to post updates.
7. Test in Telegram: message your bot.
8. Notes:
   - Koyeb may scale-to-zero on free tiers; consider paid plan for reliable instant responses.
   - If Gemini endpoints change, update gemini_client.py to match official docs.
