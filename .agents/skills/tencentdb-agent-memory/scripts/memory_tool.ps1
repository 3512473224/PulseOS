param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("read_core", "write_core", "add_convo", "search_convo", "health")]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [string]$Content = "",

    [Parameter(Mandatory=$false)]
    [string]$Query = ""
)

$GATEWAY = "http://104.129.1.216:8420"
$ADMIN_KEY = "sk-mem-Q7XHl4cYK0UnrXxmYOw5J2m9ZBOYR4Ol"

$headers = @{
    "Authorization" = "Bearer $ADMIN_KEY"
    "x-tdai-service-id" = "default"
    "Content-Type" = "application/json; charset=utf-8"
}

switch ($Action) {
    "health" {
        $res = Invoke-RestMethod -Uri "$GATEWAY/health" -Method Get
        Write-Host "Memory Core Status: $($res.status), Version: $($res.version), Uptime: $($res.uptime)s"
    }
    "read_core" {
        $res = Invoke-RestMethod -Uri "$GATEWAY/v3/core/read" -Method Post -Headers $headers -Body "{}"
        Write-Host "=== L3 Core Memory ==="
        Write-Host $res.data.content
    }
    "write_core" {
        if (-not $Content) { Write-Error "Content parameter is required for write_core"; exit 1 }
        $body = @{ content = $Content } | ConvertTo-Json
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
        $res = Invoke-RestMethod -Uri "$GATEWAY/v3/core/write" -Method Post -Headers $headers -Body $bytes
        Write-Host "Write Core Result: code=$($res.code), message=$($res.message)"
    }
    "add_convo" {
        if (-not $Content) { Write-Error "Content parameter is required for add_convo"; exit 1 }
        $body = @{
            session_id = "agent_sync_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            messages = @(
                @{ role = "user"; content = $Content }
                @{ role = "assistant"; content = "Memory registered and queued for indexing." }
            )
        } | ConvertTo-Json -Depth 5
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
        $res = Invoke-RestMethod -Uri "$GATEWAY/v3/conversation/add" -Method Post -Headers $headers -Body $bytes
        Write-Host "Add Convo Result: code=$($res.code), Accepted: $($res.data.accepted_ids)"
    }
    "search_convo" {
        if (-not $Query) { Write-Error "Query parameter is required for search_convo"; exit 1 }
        $body = @{ query = $Query; limit = 5 } | ConvertTo-Json
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
        $res = Invoke-RestMethod -Uri "$GATEWAY/v3/conversation/search" -Method Post -Headers $headers -Body $bytes
        Write-Host "Search Results (Total $($res.data.messages.Count)):"
        foreach ($msg in $res.data.messages) {
            Write-Host "[$($msg.role)] $($msg.content) (Score: $($msg.score))"
        }
    }
}
