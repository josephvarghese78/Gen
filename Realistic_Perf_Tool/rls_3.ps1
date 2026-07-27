# ======================================================================
# Microsoft Power BI Realistic Load Test Tool - Direct API RLS Overhaul
# ======================================================================

# 1. DEFINE TARGET ENVIRONMENT AND SECURITY CONTEXTS
$WorkspaceId = "YOUR-WORKSPACE-GUID-HERE"
$ReportId    = "YOUR-REPORT-GUID-HERE"
$DatasetId   = "YOUR-SEMANTIC-MODEL-DATASET-GUID-HERE"

$TargetUser  = "manager_l1@yourcompany.com"   # UPN evaluated by USERPRINCIPALNAME()
$TargetRole  = "Dynamic_RLS_User"             # The RLS Role built inside Power BI Desktop

# 2. AUTHENTICATION AND EXPLICIT AAD TOKEN EXTRACTION
Try {
    $currentProfile = Get-PowerBICntlrProfile
    # Extract the raw underlying AAD access token string
    $aadToken = Get-PowerBIAccessToken -AsString
} Catch {
    Write-Host "No active Power BI session discovered. Initiating login..." -ForegroundColor Yellow
    Connect-PowerBIMgmt
    $aadToken = Get-PowerBIAccessToken -AsString
}

# Find all active generation load test execution subfolders
$currentDir = Get-Item .
$subDirs = Get-ChildItem -Path $currentDir.FullName | Where-Object { $_.PSIsContainer }

if ($subDirs.Count -eq 0) {
    Write-Host "CRITICAL ERROR: No load test target subdirectories found. Run Setup_Load_Test.ps1 first." -ForegroundColor Red
    Exit
}

# 3. CONSTRUCT THE ROW-LEVEL SECURITY EMBED TOKEN PAYLOAD
$rlsBody = @{
    accessLevel = "View"
    identities = @(
        @{
            username = $TargetUser
            roles = @($TargetRole)
            datasets = @($DatasetId)
        }
    )
} | ConvertTo-Json -Depth 5

# 4. EXPLICIT HTTP HEADERS USING NATIVE AAD TOKEN
$headers = @{
    "Authorization" = "Bearer $aadToken"
    "Content-Type"  = "application/json"
}

$uri = "https://api.powerbi.com/v1.0/myorg/groups/$WorkspaceId/reports/$ReportId/GenerateToken"

Write-Host "Sending direct HTTP POST to fetch RLS-scoped token for: $TargetUser" -ForegroundColor Green

# 5. EXECUTE VIA NATIVE API CALL (Forces pure JSON handling)
Try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $rlsBody
    $cleanTokenString = $response.token
} Catch {
    Write-Host "API ERROR: The Power BI gateway rejected the token request." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Exit
}

# Final structural check for the expected "ey" prefix
if (-not $cleanTokenString.StartsWith("ey")) {
    Write-Host "WARNING: Token does not start with 'ey'. Received: $($cleanTokenString.Substring(0,5))..." -ForegroundColor Yellow
}

# 6. STREAM SCALED TOKEN KEYS TO LOAD TEST DIRECTORIES IN THE EXACT TARGET STRING FORMAT
foreach ($subDir in $subDirs) {
    # Custom format: accessToken='{"PBIToken":"ey..."}';
    $customTokenWrapper = "accessToken='{""PBIToken"":""" + $cleanTokenString + """}';"
    
    # Update filename extension to .js if your framework loads it as a script tag, 
    # or keep it as PBIToken.json depending on what the tool loader targets.
    $outputPath = Join-Path $subDir.FullName "PBIToken.json"
    
    Out-File -FilePath $outputPath -InputObject $customTokenWrapper -Encoding ascii -Force
    Write-Host "Successfully delivered secure RLS token layer to: $outputPath" -ForegroundColor Cyan
}

Write-Host "Token cycle completed successfully. Ready to run your load runner." -ForegroundColor Green