param(
    [Parameter(Mandatory = $true)][string]$Doc,
    [string]$Values = ""   # "MED_Agr=0,961;MED_Q=1,5" - property=value pairs
)

# Replaces literal {{TOKEN}} text with real DOCPROPERTY fields, with track
# changes on, and sets the backing properties to the supplied values.
#
# Replacing the tokens with plain text would fix the symptom and lose the link:
# editing the property would no longer change the document. So the properties
# are created or updated first, then proper fields are inserted in their place.

$ErrorActionPreference = "Stop"

# Refuse if the document is open in Word. Word leaves a ~$<name> owner file
# beside an open document; editing it anyway hangs the COM call on a dialog
# with no visible window and orphans a WINWORD.EXE holding the file.
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
$map = [ordered]@{
    "{{AGR}}"             = "MED_Agr"
    "{{GROUND_TYPE}}"     = "MED_Talajosztaly"
    "{{DUCTILITY_CLASS}}" = "MED_Duktilitas"
    "{{Q_FACTOR}}"        = "MED_Q"
}

$vals = @{}
foreach ($pair in ($Values -split ";")) {
    if ($pair -match "^\s*([^=]+)=(.*)$") { $vals[$matches[1].Trim()] = $matches[2].Trim() }
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
    Write-Output ("opened: {0}" -f $base)

    # 1. create or update the backing properties
    $props = $document.CustomDocumentProperties
    foreach ($name in $map.Values) {
        $v = "TBC"
        if ($vals.ContainsKey($name)) { $v = $vals[$name] }
        $existing = $null
        try { $existing = [System.__ComObject].InvokeMember("Item", "GetProperty", $null, $props, @($name)) } catch {}
        if ($null -eq $existing) {
            # 4 = msoPropertyTypeString
            $null = [System.__ComObject].InvokeMember("Add", "InvokeMethod", $null, $props, @($name, $false, 4, $v))
            Write-Output ("  property added:   {0} = {1}" -f $name, $v)
        } else {
            [System.__ComObject].InvokeMember("Value", "SetProperty", $null, $existing, @($v))
            Write-Output ("  property updated: {0} = {1}" -f $name, $v)
        }
    }

    # 2. swap each literal token for a DOCPROPERTY field.
    # Bounded loop: an unbounded `while (Find.Execute())` spins forever if a
    # replacement does not take, which is how the previous run hung.
    $replaced = 0
    foreach ($token in $map.Keys) {
        $prop = $map[$token]
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            $find = $document.Content.Find
            $find.ClearFormatting()
            $find.Text = $token
            $find.Forward = $true
            $find.Wrap = 0              # wdFindStop
            if (-not $find.Execute()) { break }
            $r = $find.Parent
            $r.Text = ""
            # 85 = wdFieldDocProperty
            $null = $document.Fields.Add($r, 85, ('"' + $prop + '" \* MERGEFORMAT'), $false)
            $replaced++
        }
    }
    Write-Output ("  tokens replaced with fields: {0}" -f $replaced)

    $null = $document.Fields.Update()
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
