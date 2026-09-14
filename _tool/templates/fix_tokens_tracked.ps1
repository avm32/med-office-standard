param([Parameter(Mandatory = $true)][string]$Doc)

# Replaces literal {{TOKEN}} text with real DOCPROPERTY fields, with track
# changes on. The tokens leaked because table cells were emitted without
# substitution; replacing them with plain text would fix the symptom but lose
# the link, so the properties are created first and proper fields inserted.

$ErrorActionPreference = "Stop"

# Refuse if the document is open in Word. Word leaves a ~$<name> owner file
# beside an open document; editing it anyway hangs the COM call on a dialog
# that has no visible window, and leaves an orphaned WINWORD.EXE holding the
# file. Better to stop and say so.
$dir = [System.IO.Path]::GetDirectoryName((Resolve-Path $Doc).Path)
$base = [System.IO.Path]::GetFileName((Resolve-Path $Doc).Path)
$owner = Join-Path $dir ("~$" + $base.Substring([Math]::Min(2, $base.Length)))
if (Test-Path $owner) {
    Write-Output "REFUSING: the document appears to be open in Word (owner file present)."
    Write-Output "  Close it first. Editing an open document hangs the COM call and"
    Write-Output "  risks losing whatever is unsaved in that Word session."
    exit 2
}

$word = $null
$document = $null
$originalUser = $null

# token in the document -> the custom property that should back it
$map = @{
    "{{AGR}}"             = "MED_Agr"
    "{{GROUND_TYPE}}"     = "MED_Talajosztaly"
    "{{DUCTILITY_CLASS}}" = "MED_Duktilitas"
    "{{Q_FACTOR}}"        = "MED_Q"
}

try {
    $full = (Resolve-Path $Doc).Path
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $originalUser = $word.UserName
    $word.UserName = "Claude (medtpl)"

    $document = $word.Documents.Open($full, $false, $false)
    $document.TrackRevisions = $true
    Write-Output ("opened: {0}" -f [System.IO.Path]::GetFileName($full))

    # 1. create the properties if absent, so the fields resolve to something
    $props = $document.CustomDocumentProperties
    foreach ($name in $map.Values) {
        $exists = $false
        try { $null = [System.__ComObject].InvokeMember("Item", "GetProperty", $null, $props, @($name)); $exists = $true } catch {}
        if (-not $exists) {
            # 4 = msoPropertyTypeString
            $null = [System.__ComObject].InvokeMember("Add", "InvokeMethod", $null, $props, @($name, $false, 4, "TBC"))
            Write-Output ("  property added: {0}" -f $name)
        }
    }

    # 2. swap each literal token for a DOCPROPERTY field
    $replaced = 0
    foreach ($token in $map.Keys) {
        $prop = $map[$token]
        while ($true) {
            $find = $document.Content.Find
            $find.ClearFormatting()
            $find.Text = $token
            $find.Forward = $true
            $find.Wrap = 0          # wdFindStop
            if (-not $find.Execute()) { break }
            $r = $find.Parent
            $r.Text = ""            # clear, then drop the field in its place
            $null = $document.Fields.Add($r, 85, ('"' + $prop + '" \* MERGEFORMAT'), $false)
            $replaced++
        }
    }
    Write-Output ("  tokens replaced with fields: {0}" -f $replaced)

    $document.Fields.Update() | Out-Null
    $document.Save()
    Write-Output ("  revisions now: {0}" -f $document.Revisions.Count)
    $document.Close([ref]0)
    $document = $null
}
catch { Write-Output ("ERROR: " + $_.Exception.Message) }
finally {
    if ($document -ne $null) { try { $document.Close([ref]0) } catch {} }
    if ($word -ne $null) {
        if ($originalUser -ne $null) { try { $word.UserName = $originalUser } catch {} }
        try { $word.Quit([ref]0) } catch {}
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {}
    }
    [GC]::Collect()
}
