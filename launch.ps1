# Windows PowerShell 5.1+ and PowerShell 7
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $launchArgs = @($args)
    if ($launchArgs.Count -eq 0) { $launchArgs = @('serve') }
    if ($launchArgs[0] -eq 'install') {
        & uv sync --locked
    } elseif ($launchArgs[0] -eq 'help') {
        & uv run yt-transcript --help
    } else {
        & uv run yt-transcript @launchArgs
    }
    $launchExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $launchExitCode
