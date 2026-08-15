<#
.SYNOPSIS
Invokes the private FeeOps ADK service on Cloud Run using the current gcloud user.

.DESCRIPTION
This is the no-Firebase live-agent demonstration path. It gets a short-lived IAM
identity token from gcloud, creates an ADK session, and prints the final model
answer. No API key, service-account JSON key, or browser credential is used.
#>

param(
    [string]$ProjectId = "intern-bnmit-july-2026",
    [string]$Region = "us-central1",
    [string]$Service = "feeops-backend",
    [string]$AppName = "feeops_adk",
    [string]$UserId = "local-demonstrator",
    [string]$Prompt = "Use the cash forecast and leakage tools. Summarize the forecast and name the highest-risk reviewer action without inventing monetary values."
)

$ErrorActionPreference = "Stop"

$token = (& gcloud auth print-identity-token).Trim()
if (-not $token) {
    throw "Could not obtain an identity token. Run 'gcloud auth login' first."
}

$serviceUrl = (& gcloud run services describe $Service --project $ProjectId --region $Region --format="value(status.url)").Trim()
if (-not $serviceUrl) {
    throw "Cloud Run service '$Service' was not found in '$ProjectId/$Region'."
}

$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}
$sessionId = "feeops-" + [guid]::NewGuid().ToString("N")
$sessionBody = @{ sessionId = $sessionId } | ConvertTo-Json -Compress

Invoke-RestMethod `
    -Uri "$serviceUrl/apps/$AppName/users/$UserId/sessions" `
    -Headers $headers `
    -Method Post `
    -Body $sessionBody | Out-Null

$request = @{
    appName = $AppName
    userId = $UserId
    sessionId = $sessionId
    newMessage = @{
        role = "user"
        parts = @(@{ text = $Prompt })
    }
} | ConvertTo-Json -Depth 8 -Compress

$events = Invoke-RestMethod -Uri "$serviceUrl/run" -Headers $headers -Method Post -Body $request
$answer = @(
    foreach ($event in $events) {
        foreach ($part in @($event.content.parts)) {
            if ($part.text) { $part.text }
        }
    }
) | Select-Object -Last 1

if (-not $answer) {
    throw "The ADK request returned no final text response."
}

Write-Output "Cloud Run service: $serviceUrl"
Write-Output "Session: $sessionId"
Write-Output ""
Write-Output $answer
