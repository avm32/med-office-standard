param([Parameter(Mandatory = $true)][string]$Target)

# Checks that caption numbering fires from the STYLE alone - no Insert > Caption
# dialog - and that the DOCPROPERTY fields resolve. ListString is what Word
# renders as the automatic number; if it is empty the style-link is not working.

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null
try {
    $document = $word.Documents.Open((Resolve-Path $Target).Path, $false, $true)
    Write-Output ("OPENED OK  paragraphs={0}  tables={1}" -f `
        $document.Paragraphs.Count, $document.Tables.Count)
    $null = $document.Fields.Update()

    foreach ($st in @('14 - Ábra felirat', '17 - Táblázat felirat')) {
        $found = @()
        foreach ($p in $document.Paragraphs) {
            if ($p.Style.NameLocal -eq $st) {
                $txt = $p.Range.Text.Trim()
                if ($txt.Length -gt 46) { $txt = $txt.Substring(0, 46) }
                $found += ("auto-number=[{0}]  text={1}" -f $p.Range.ListFormat.ListString, $txt)
            }
        }
        Write-Output ("  {0}  ({1} found)" -f $st, $found.Count)
        foreach ($f in $found) { Write-Output ("      " + $f) }
    }

    $props = $document.CustomDocumentProperties
    $count = [System.__ComObject].InvokeMember("Count", "GetProperty", $null, $props, $null)
    Write-Output ("  custom document properties: {0}" -f $count)
    for ($i = 1; $i -le [Math]::Min($count, 6); $i++) {
        $item = [System.__ComObject].InvokeMember("Item", "GetProperty", $null, $props, @($i))
        $nm = [System.__ComObject].InvokeMember("Name", "GetProperty", $null, $item, $null)
        $vl = [System.__ComObject].InvokeMember("Value", "GetProperty", $null, $item, $null)
        Write-Output ("      {0} = {1}" -f $nm, $vl)
    }
    $document.Close([ref]0)
}
catch { Write-Output ("ERROR: " + $_.Exception.Message) }
finally {
    if ($document -ne $null) { try { $document.Close([ref]0) } catch {} }
    if ($word -ne $null) { try { $word.Quit([ref]0) } catch {} }
}
