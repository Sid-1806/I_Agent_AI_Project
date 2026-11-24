# Assemble video/build/plan.json into a PowerPoint deck (one still per slide, narration playing on entry,
# slide timed to its narration) and export it as a 1080p MP4 with PowerPoint's own video export.
param([string]$Plan, [string]$Deck, [string]$Video)

$items = Get-Content $Plan -Raw | ConvertFrom-Json
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Add(0)               # no window
    $pres.PageSetup.SlideWidth = 960
    $pres.PageSetup.SlideHeight = 540
    $i = 0
    foreach ($item in $items) {
        $i++
        $slide = $pres.Slides.Add($i, 12)           # ppLayoutBlank
        $null = $slide.Shapes.AddPicture($item.image, 0, -1, 0, 0, 960, 540)
        $audio = $slide.Shapes.AddMediaObject2($item.audio, 0, -1, 970, 10, 32, 32)   # icon off the slide
        $audio.AnimationSettings.PlaySettings.PlayOnEntry = -1
        $audio.AnimationSettings.PlaySettings.HideWhileNotPlaying = -1
        $t = $slide.SlideShowTransition
        $t.EntryEffect = 0                          # cut: no transition animation
        $t.AdvanceOnClick = 0
        $t.AdvanceOnTime = -1
        $t.AdvanceTime = [double]$item.seconds
    }
    $pres.SaveAs($Deck)
    $pres.CreateVideo($Video, $true, 5, 1080, 30, 90)
    while ($pres.CreateVideoStatus -eq 1 -or $pres.CreateVideoStatus -eq 2) { Start-Sleep -Seconds 2 }  # in progress / queued
    "video status: $($pres.CreateVideoStatus) (3 = done)"
    $pres.Close()
} finally {
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
