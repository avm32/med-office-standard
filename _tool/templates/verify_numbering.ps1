param([Parameter(Mandatory = $true)][string]$Doc)

# Reports the auto-numbering Word actually renders for every heading. The XML
# can look right while Word numbers it differently - ListString is what a
# reader will see, so that is what gets checked.

$ErrorActionPreference = "Stop"
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open((Resolve-Path $Doc).Path, $false, $true)
    $null = $document.Fields.Update()

    $wanted = @('21 - Címsor 1', '22 - Címsor 2', '50 - Számozatlan címsor',
                '27 - Melléklet', '28 - Melléklet alcím')
    foreach ($p in $document.Paragraphs) {
        $st = $p.Style.NameLocal
        if ($wanted -contains $st) {
            $txt = $p.Range.Text.Trim()
            if ($txt.Length -gt 44) { $txt = $txt.Substring(0, 44) }
            $num = $p.Range.ListFormat.ListString
            if ($num -eq "") { $num = "—" }
            Write-Output ("  {0,-9} {1,-24} {2}" -f $num, $st, $txt)
        }
    }
    $document.Close([ref]0)
    $document = $null
}
catch { Write-Output ("ERROR: " + $_.Exception.Message) }
finally {
    if ($document -ne $null) { try { $document.Close([ref]0) } catch {} }
    if ($word -ne $null) { try { $word.Quit([ref]0) } catch {} }
}
