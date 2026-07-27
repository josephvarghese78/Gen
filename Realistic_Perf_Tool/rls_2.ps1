# ======================================================================
# Microsoft Power BI Realistic Load Test Tool - RLS Identity Overhaul
# ======================================================================

# 1. DEFINE TARGET ENVIRONMENT AND SECURITY CONTEXTS
$WorkspaceId = "YOUR-WORKSPACE-GUID-HERE"
$ReportId    = "YOUR-REPORT-GUID-HERE"
$DatasetId   = "YOUR-SEMANTIC-MODEL-DATASET-GUID-HERE"

$TargetUser  = "manager_l1@yourcompany.com"   # UPN evaluated by USERPRINCIPALNAME()
$TargetRole  = "Dynamic_RLS_User"             # The RLS Role built inside Power BI Desktop

# 2. AUTHENTICATION AND POWERBI MANAGEMENT CHECK
Try {
    $currentProfile = Get-PowerBICntlrProfile
} Catch {
    Write-Host "No active Power BI Management context discovered. Initiating login dialog..." -ForegroundColor Yellow
    Connect-PowerBIMgmt
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

Write-Host "Sending API request to fetch RLS-scoped token context for: $TargetUser" -ForegroundColor Green

# 4. QUERY THE GENERATE TOKEN GATEWAY VIA REST METHODS
# Hits POST https://api.powerbi.com/v1.0/myorg/groups/$WorkspaceId/reports/$ReportId/GenerateToken
$rawTokenResponse = Invoke-PowerBIRestMethod -Url "groups/$WorkspaceId/reports/$ReportId/GenerateToken" -Method Post -Body $rlsBody

# --- FIX IMPLEMENTED HERE ---
# Safely handle whether Invoke-PowerBIRestMethod returned a string or a pre-parsed object
if ($rawTokenResponse -is [string]) {
    $tokenObject = ConvertFrom-Json $rawTokenResponse
} else {
    $tokenObject = $rawTokenResponse
}

# Extract the exact string that starts with "ey..."
$cleanTokenString = $tokenObject.token

# Verification check to ensure we aren't writing an empty string or incorrect wrapper
if ([string]::IsNullOrEmpty($cleanTokenString)) {
    Write-Host "ERROR: Failed to extract the 'token' property from the API response. Check your GUIDs and RLS configurations." -ForegroundColor Red
    Exit
}
# ----------------------------

# 5. STREAM SCALED TOKEN KEYS TO LOAD TEST DIRECTORIES
foreach ($subDir in $subDirs) {
    # The tool frontend (RealisticLoadTest.html) relies on a structural key named "accessToken"
    $tokenJsonWrapper = "{""accessToken"": """ + $cleanTokenString + """}"
    
    $outputPath = Join-Path $subDir.FullName "PBIToken.json"
    Out-File -FilePath $outputPath -InputObject $tokenJsonWrapper -Encoding ascii -Force
    Write-Host "Successfully delivered secure RLS token layer to: $outputPath" -ForegroundColor Cyan
}

Write-Host "Token cycle completed successfully. Ready to run your load runner." -ForegroundColor Green