Get-ChildItem .\artifacts\pairs -Recurse -File |
Where-Object { $_.Name -in @("metadata.json", "result.json", "blind_responses.json", "system_key.json") } |
ForEach-Object {
    Write-Output "`n========== $($_.FullName) =========="
    Get-Content $_.FullName -Raw
}