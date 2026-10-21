param(
    [string]$InputDocx = (Join-Path $PSScriptRoot "docx\QWeave_IEEE_Conference.docx"),
    [string]$OutputPdf = (Join-Path $PSScriptRoot "pdf\QWeave_IEEE_Conference.pdf")
)

$inputPath = [System.IO.Path]::GetFullPath($InputDocx)
$outputPath = [System.IO.Path]::GetFullPath($OutputPdf)
$outputDirectory = Split-Path -Parent $outputPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $document = $word.Documents.Open($inputPath, $false, $true)
    try {
        $document.ExportAsFixedFormat($outputPath, 17)
    }
    finally {
        $document.Close($false)
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null
}

Write-Output $outputPath
