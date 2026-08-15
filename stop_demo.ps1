# This script stops both the frontend server and the background Python worker.

Write-Host "Stopping frontend (Vite/Node)..."
Stop-Process -Name "node" -ErrorAction SilentlyContinue

Write-Host "Stopping backend worker (Python)..."
# Be careful: this stops all python processes running on your machine.
Stop-Process -Name "python" -ErrorAction SilentlyContinue

Write-Host "Demo stopped successfully!"
