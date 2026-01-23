#!/bin/bash
# Script to help diagnose Heroku 500 error

echo "Heroku 500 Error Diagnostic"
echo "============================"
echo ""

echo "1. Checking if Heroku CLI is available..."
if command -v heroku &> /dev/null; then
    echo "✅ Heroku CLI found"
    echo ""
    echo "To view logs, run:"
    echo "  heroku logs --tail --app YOUR_APP_NAME"
    echo ""
    echo "To connect to database:"
    echo "  heroku pg:psql"
    echo ""
else
    echo "❌ Heroku CLI not found"
    echo "   Install: https://devcenter.heroku.com/articles/heroku-cli"
    echo ""
    echo "Or check logs in Heroku Dashboard:"
    echo "   https://dashboard.heroku.com/apps/YOUR_APP/logs"
fi

echo ""
echo "2. Testing fix endpoints (if latest code is deployed):"
echo "   https://www.localchurches.org/fix-userprofile/"
echo "   https://www.localchurches.org/fix-workflowstate/"
echo "   https://www.localchurches.org/fix-taskstate/"
echo "   https://www.localchurches.org/fix-revision/"
echo ""

echo "3. Most likely issue: Missing database columns"
echo "   Heroku needs the same database fixes we applied to Render"
echo "   See: fix_userprofile_complete.sql"
echo ""

echo "4. Quick fix options:"
echo "   A. Run SQL manually on Heroku database"
echo "   B. Deploy latest code to Heroku (if not already deployed)"
echo "   C. Use API endpoints (if available)"
