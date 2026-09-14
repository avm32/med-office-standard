# Word-level verification for medtpl. Run by `medtpl verify`.
#
# XML that passes every structural check can still make Word offer to repair the
# file, and only Word will tell you. This opens the document read-only, asserts
# the things that matter, and always tears the COM object down - an orphaned
# invisible WINWORD.EXE will otherwise sit holding the file open forever.

param(
    [Parameter(Mandatory = $true)][string]$Doc,
    [string]$ImageTest = "",
    [switch]$Pdf
)

$ErrorActionPreference = "Stop"
$word = $null
$document = $null   # NOT $doc: PowerShell variables are case-insensitive, so that would clobber the -Doc parameter
$exit = 0

try {
    $full = (Resolve-Path $Doc).Path
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    # ReadOnly, AddToRecentFiles=false, so nothing is written back
    $document = $word.Documents.Open($full, $false, $true)
    Write-Output ("OPENED OK        paragraphs={0}  tables={1}  images={2}  styles={3}" -f `
        $document.Paragraphs.Count, $document.Tables.Count, $document.InlineShapes.Count, $document.Styles.Count)
    Write-Output ("  pages          {0}" -f $document.ComputeStatistics(2))
    Write-Output ("  margins        left={0}cm right={1}cm" -f `
        [math]::Round($document.PageSetup.LeftMargin / 28.35, 2), `
        [math]::Round($document.PageSetup.RightMargin / 28.35, 2))

    # Hungarian style names must be present and reachable by name
    $wanted = @('11 - Szöveg', '21 - Címsor 1', '22 - Címsor 2', '15 - Ábra',
                '14 - Ábra felirat', '17 - Táblázat felirat', '48 - Aláírás', '49 - Nyilatkozat',
                '27 - Melléklet', '31 - Felsorolás pont', '16 - Táblázatcím')
    $missing = @()
    foreach ($n in $wanted) {
        try { $null = $document.Styles.Item($n) } catch { $missing += $n }
    }
    if ($missing.Count -gt 0) {
        Write-Output ("  STYLES MISSING {0}" -f ($missing -join ', '))
        $exit = 1
    } else {
        Write-Output ("  styles         all {0} Hungarian names present" -f $wanted.Count)
    }

    # The regression test: Normal must not use Exactly line spacing (4), which
    # is what clips an inline image to one line.
    $rule = $document.Styles.Item('Normal').ParagraphFormat.LineSpacingRule
    if ($rule -eq 4) {
        Write-Output "  IMAGE RISK     Normal uses Exactly line spacing - images will be clipped"
        $exit = 1
    } else {
        Write-Output ("  image safety   Normal LineSpacingRule={0} (not Exactly)" -f $rule)
    }

    if ($Pdf) {
        $out = [System.IO.Path]::ChangeExtension($full, ".pdf")
        $document.ExportAsFixedFormat($out, 17)
        Write-Output ("  pdf            {0} ({1} bytes)" -f `
            [System.IO.Path]::GetFileName($out), (Get-Item $out).Length)
    }
}
catch {
    Write-Output ("ERROR: " + $_.Exception.Message)
    $exit = 1
}
finally {
    if ($document -ne $null) { try { $document.Close([ref]0) } catch {} }
    if ($word -ne $null) {
        try { $word.Quit([ref]0) } catch {}
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {}
    }
    [GC]::Collect()
}

exit $exit
