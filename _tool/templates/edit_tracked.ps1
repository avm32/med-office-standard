param([Parameter(Mandatory = $true)][string]$Doc)

# Edits a document with track changes ON, so every change is reviewable and
# reversible in Word. Used instead of regenerating, which would discard the
# user's own edits.
#
# TrackRevisions is set on the DOCUMENT, not the Application - setting it on the
# app would silently turn tracking on for anything else the user has open.
# Word's UserName is application-wide and stored in settings, so it is saved and
# restored rather than left changed.

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

try {
    $full = (Resolve-Path $Doc).Path
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    $originalUser = $word.UserName
    $word.UserName = "Claude (medtpl)"

    $document = $word.Documents.Open($full, $false, $false)   # read-write
    $document.TrackRevisions = $true
    $before = $document.Revisions.Count
    Write-Output ("opened: {0}" -f [System.IO.Path]::GetFileName($full))
    Write-Output ("  existing revisions: {0}" -f $before)

    # ---- 1. table header rows: grey -> white -------------------------------
    $wdColorWhite = 16777215
    $changed = 0
    foreach ($t in $document.Tables) {
        $row = $t.Rows.Item(1)
        foreach ($cell in $row.Cells) {
            if ($cell.Shading.BackgroundPatternColor -ne $wdColorWhite) {
                $cell.Shading.BackgroundPatternColor = $wdColorWhite
                $changed++
            }
        }
    }
    Write-Output ("  header cells set to white: {0}" -f $changed)

    # ---- 2. comments where something needs the engineer's decision ---------
    $comments = 0

    # fire table - the ratings reportedly changed but nothing shows it
    foreach ($t in $document.Tables) {
        if ($t.Range.Text -match "REI") {
            $null = $document.Comments.Add($t.Rows.Item(1).Range,
                "A tűzállósági értékek forrása? Ebben a fájlban nem látszik módosítás a táblázaton, és tűzvédelmi dokumentáció sem érkezett a 02-Bejovo mappába. Az értékeket a tűzvédelmi tervező dokumentációjából kell átvenni — kérlek add meg a forrást, és bevezetem.")
            $comments++
            break
        }
    }

    # P + F + 5 here vs P + F + 6 in PROJECT.md
    $find = $document.Content.Find
    $find.ClearFormatting()
    $find.Text = "P + F + 5"
    if ($find.Execute()) {
        $null = $document.Comments.Add($find.Parent,
            "Eltérés: a PROJECT.md 'P + F + 6' szintszámot rögzít, itt 'P + F + 5' szerepel. Melyik a helyes? A javítás a PROJECT.md-be is kell, mert onnan töltődik minden dokumentumba.")
        $comments++
    }

    Write-Output ("  comments added: {0}" -f $comments)

    $document.Save()
    $after = $document.Revisions.Count
    Write-Output ("  revisions now: {0} (was {1})" -f $after, $before)
    $document.Close([ref]0)
    $document = $null
}
catch {
    Write-Output ("ERROR: " + $_.Exception.Message)
}
finally {
    if ($document -ne $null) { try { $document.Close([ref]0) } catch {} }
    if ($word -ne $null) {
        if ($originalUser -ne $null) { try { $word.UserName = $originalUser } catch {} }
        try { $word.Quit([ref]0) } catch {}
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {}
    }
    [GC]::Collect()
}
