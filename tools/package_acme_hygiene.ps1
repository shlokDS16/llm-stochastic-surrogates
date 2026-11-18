# Hygiene pass for the ACME package (CRP-S09 typeset). Uses the hidden-unicode skill (wm.ps1).
#   powershell -NoProfile -File tools\package_acme_hygiene.ps1 -Mode text -Dir submission\acme\source
#   powershell -NoProfile -File tools\package_acme_hygiene.ps1 -Mode pdf  -Dir submission\acme\source        (figure PDFs)
#   powershell -NoProfile -File tools\package_acme_hygiene.ps1 -Mode pdf  -Dir submission\acme              (manuscript PDFs)
# text: wm scan (payload carriers) and wm inspect per text file (hygiene-only characters); prints the counts.
# pdf : per PDF, document metadata before (Author, Creator, Producer, Title, Subject, Keywords, dates), wm clean
#       (exiftool -all= then qpdf rewrite; fonts and page content stay), raw-byte check that the old strings are gone,
#       metadata after; the cleaned file replaces the original. Top level of -Dir only.
param(
  [Parameter(Mandatory = $true)][ValidateSet('text', 'pdf')][string]$Mode,
  [Parameter(Mandatory = $true)][string]$Dir
)
$wm = "$env:USERPROFILE\.claude\skills\hidden-unicode\scripts\wm.ps1"
$Dir = (Resolve-Path $Dir).Path
$latin1 = [Text.Encoding]::GetEncoding(28591)
$fields = @('Author', 'Creator', 'Producer', 'Title', 'Subject', 'Keywords', 'CreateDate', 'ModifyDate')

function MetaLine($path) {
  $vals = (& exiftool -q -s ($fields | ForEach-Object { "-$_" }) $path) | ForEach-Object { $_.Trim() }
  if (-not $vals) { return '(no document metadata fields)' }
  return ($vals -join ' | ')
}

if ($Mode -eq 'text') {
  $o = & $wm scan $Dir 2>&1 | Out-String
  Write-Output $o.Trim()
  $tot = 0; $n = 0
  Get-ChildItem $Dir -File | Where-Object { $_.Extension -in '.tex', '.bib', '.bst', '.cls', '.bbl', '.md', '.txt' } | ForEach-Object {
    $n++
    $i = & $wm inspect $_.FullName 2>&1 | Out-String
    if ($i -match 'Suspicious:\s*(\d+)') { $c = [int]$Matches[1]; $tot += $c; if ($c -gt 0) { Write-Output "  $($_.Name): $c" } }
  }
  Write-Output "inspect: $n text files, $tot suspicious characters in total"
  return
}

Get-ChildItem $Dir -File -Filter *.pdf | Where-Object { $_.Name -notlike '*.cleaned.pdf' } | ForEach-Object {
  $f = $_.FullName
  $before = MetaLine $f
  $raw0 = $latin1.GetString([IO.File]::ReadAllBytes($f))
  $hit0 = @('Matplotlib', 'MiKTeX', 'pdfTeX', 'PyMuPDF', 'fig_', 'analysis/') | Where-Object { $raw0.Contains($_) }
  # wm writes its progress line to stderr; PowerShell 5.1 turns that into an error record, so call it through cmd
  $null = cmd /c "powershell -NoProfile -File `"$wm`" clean `"$f`" 2>nul"
  $clean = [IO.Path]::ChangeExtension($f, '.cleaned.pdf')
  if (-not (Test-Path $clean)) { Write-Output "$($_.Name): CLEAN FAILED"; return }
  $raw1 = $latin1.GetString([IO.File]::ReadAllBytes($clean))
  $hit1 = @('Matplotlib', 'MiKTeX', 'pdfTeX', 'PyMuPDF', 'fig_', 'analysis/') | Where-Object { $raw1.Contains($_) }
  $after = MetaLine $clean
  Move-Item $clean $f -Force
  Write-Output "$($_.Name): before [$before] strings-in-bytes [$($hit0 -join ',')] -> after [$after] strings-in-bytes [$($hit1 -join ',')]"
}
