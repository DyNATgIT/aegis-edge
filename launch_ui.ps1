# launch_ui.ps1
# Aegis-Edge — Launch Streamlit UI
# Aayu Wadhwani & Keshav Bhatnagar

cd "C:\Users\poona\Documents\aegis-edge"
.\aegis-env\Scripts\Activate.ps1

Write-Host ""
Write-Host "Launching Aegis-Edge Streamlit UI..." -ForegroundColor Cyan
Write-Host "Open browser at: http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

streamlit run ui\app.py `
    --server.port 8501 `
    --browser.gatherUsageStats false `
    --server.headless false
