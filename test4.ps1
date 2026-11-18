$dir = ".cache\project_RAVE\data\runs"
$file = Get-ChildItem $dir -Filter "rave-*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

$j = Get-Content $file.FullName -Raw | ConvertFrom-Json

Write-Host "`n=== IDENTIFICACAO ==="
$file.Name
$j.execution_status
$j.metadata.status

Write-Host "`n=== ORCAMENTO ==="
$j.run_budget | ConvertTo-Json -Depth 5

Write-Host "`n=== CHAMADAS ==="
$j.metadata.calls |
    Select-Object agent_id, purpose, status, prompt_tokens,
        completion_tokens, duration_seconds, request_attempts |
    Format-Table -AutoSize

Write-Host "`n=== TAMANHO DOS RESULTADOS ==="
if ($j.agent_results -is [System.Collections.IDictionary]) {
    $j.agent_results.GetEnumerator() | ForEach-Object {
        [PSCustomObject]@{
            Agent = $_.Key
            Characters = ($_.Value | ConvertTo-Json -Depth 15 -Compress).Length
        }
    } | Format-Table -AutoSize
}
elseif ($j.agent_results) {
    $j.agent_results | ForEach-Object {
        [PSCustomObject]@{
            Agent = $_.agent_id
            Characters = ($_.messages | ConvertTo-Json -Depth 15 -Compress).Length
            Refinement = $_.refinement_status
            Failure = $_.failure_type
        }
    } | Format-Table -AutoSize
}

Write-Host "`n=== ERRO DE SINTESE ==="
$j.synthesis_error

Write-Host "`n=== PROPRIEDADES DO ORCAMENTO ==="
$j.run_budget.PSObject.Properties.Name