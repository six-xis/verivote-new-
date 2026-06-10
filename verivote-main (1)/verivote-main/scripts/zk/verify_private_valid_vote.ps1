param(
    [string]$VerificationKey,
    [string]$PublicJson,
    [string]$ProofJson
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..")
$ArtifactDir = Join-Path $RootDir "artifacts\zk\private_valid_vote"

if (-not $VerificationKey) {
    $VerificationKey = Join-Path $ArtifactDir "verification_key.json"
}
if (-not $PublicJson) {
    $PublicJson = Join-Path $ArtifactDir "public.json"
}
if (-not $ProofJson) {
    $ProofJson = Join-Path $ArtifactDir "proof.json"
}

if (Get-Command snarkjs -ErrorAction SilentlyContinue) {
    $SnarkjsCommand = "snarkjs"
    $SnarkjsPrefix = @()
} elseif (Get-Command pnpm.cmd -ErrorAction SilentlyContinue) {
    $SnarkjsCommand = (Get-Command pnpm.cmd).Source
    $SnarkjsPrefix = @("exec", "snarkjs")
} elseif (Get-Command pnpm -ErrorAction SilentlyContinue) {
    $SnarkjsCommand = (Get-Command pnpm).Source
    $SnarkjsPrefix = @("exec", "snarkjs")
} else {
    throw "Missing snarkjs. Install with 'pnpm add -D snarkjs' or expose snarkjs on PATH."
}

foreach ($Path in @($VerificationKey, $PublicJson, $ProofJson)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing required file: $Path"
    }
}

Write-Output "Verifying Groth16 proof..."
& $SnarkjsCommand @SnarkjsPrefix groth16 verify $VerificationKey $PublicJson $ProofJson
if ($LASTEXITCODE -ne 0) {
    throw "snarkjs groth16 verify failed"
}
