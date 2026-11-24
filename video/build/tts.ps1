# Speak each line of video/build/lines.json to a WAV file with the Windows OneCore voices.
param([string]$Lines, [string]$OutDir)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]

$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Await($op, [Type]$type) {
    $task = $asTask.MakeGenericMethod($type).Invoke($null, @($op))
    $task.Wait() | Out-Null
    $task.Result
}

$synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$voices = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
$items = Get-Content $Lines -Raw | ConvertFrom-Json
foreach ($item in $items) {
    $synth.Voice = $voices | Where-Object { $_.DisplayName -like "*$($item.voice)*" } | Select-Object -First 1
    $synth.Options.SpeakingRate = 1.0
    $stream = Await ($synth.SynthesizeTextToStreamAsync($item.text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
    $size = [uint32]$stream.Size
    Await ($reader.LoadAsync($size)) ([uint32]) | Out-Null
    $bytes = New-Object byte[] $size
    $reader.ReadBytes($bytes)
    [IO.File]::WriteAllBytes((Join-Path $OutDir "$($item.id).wav"), $bytes)
    "spoke $($item.id) with $($synth.Voice.DisplayName)"
}
