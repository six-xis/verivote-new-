param(
    [string]$InputJson
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..")
$ArtifactDir = Join-Path $RootDir "artifacts\zk\private_valid_vote"
$DefaultInput = Join-Path $RootDir "circuits\inputs\private_valid_vote.valid.json"
$InputGenerator = Join-Path $RootDir "scripts\zk\generate_private_valid_vote_input.mjs"
$WitnessJs = Join-Path $ArtifactDir "private_valid_vote_js\generate_witness.js"
$Wasm = Join-Path $ArtifactDir "private_valid_vote_js\private_valid_vote_4_8.wasm"
$Witness = Join-Path $ArtifactDir "witness.wtns"
$Proof = Join-Path $ArtifactDir "proof.json"
$Public = Join-Path $ArtifactDir "public.json"
$Zkey = Join-Path $ArtifactDir "private_valid_vote.zkey"

if (-not $InputJson) {
    $InputJson = $DefaultInput
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

function Invoke-Snarkjs {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $SnarkjsCommand @SnarkjsPrefix @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "snarkjs command failed: $($Arguments -join ' ')"
    }
}

if (-not (Test-Path -LiteralPath $InputGenerator)) {
    throw "Missing input generator at $InputGenerator"
}
if (-not (Test-Path -LiteralPath $WitnessJs)) {
    throw "Missing witness generator. Run scripts/zk/build_private_valid_vote.ps1 first."
}
if (-not (Test-Path -LiteralPath $Wasm)) {
    $WasmMatch = Get-ChildItem -LiteralPath (Join-Path $ArtifactDir "private_valid_vote_js") -Filter "*.wasm" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $WasmMatch) {
        throw "Missing WASM artifact. Run scripts/zk/build_private_valid_vote.ps1 first."
    }
    $Wasm = $WasmMatch.FullName
}
if (-not (Test-Path -LiteralPath $Zkey)) {
    throw "Missing zkey artifact. Run scripts/zk/build_private_valid_vote.ps1 first."
}

Write-Output "Generating Poseidon-consistent witness inputs..."
& node $InputGenerator
if ($LASTEXITCODE -ne 0) {
    throw "input generation failed"
}

if (-not (Test-Path -LiteralPath $InputJson)) {
    throw "Missing input file: $InputJson"
}

Remove-Item -Force -LiteralPath $Witness, $Proof, $Public -ErrorAction SilentlyContinue

Write-Output "Calculating witness..."
& node $WitnessJs $Wasm $InputJson $Witness
if ($LASTEXITCODE -ne 0) {
    throw "witness generation failed"
}

Write-Output "Generating Groth16 proof..."
Invoke-Snarkjs groth16 prove $Zkey $Witness $Proof $Public

Write-Output "Witness written to $Witness"
Write-Output "Proof written to $Proof"
Write-Output "Public signals written to $Public"
