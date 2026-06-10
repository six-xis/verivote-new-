param(
    [int]$PtauPower = 15
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..")
$ArtifactDir = Join-Path $RootDir "artifacts\zk\private_valid_vote"
$Circuit = Join-Path $RootDir "circuits\private_valid_vote_4_8.circom"
$NodeModules = Join-Path $RootDir "node_modules"
$CircomlibPoseidon = Join-Path $RootDir "node_modules\circomlib\circuits\poseidon.circom"
$InputGenerator = Join-Path $RootDir "scripts\zk\generate_private_valid_vote_input.mjs"

if (-not (Get-Command circom -ErrorAction SilentlyContinue)) {
    throw "Missing circom. Install Circom 2 and ensure 'circom' is on PATH."
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

if (-not (Test-Path -LiteralPath $CircomlibPoseidon)) {
    throw "Missing circomlib Poseidon circuit at $CircomlibPoseidon. Install suggestion: pnpm add -D circomlib circomlibjs"
}
if (-not (Test-Path -LiteralPath $InputGenerator)) {
    throw "Missing input generator at $InputGenerator"
}

New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null

Write-Output "Generating Poseidon-consistent witness inputs..."
& node $InputGenerator
if ($LASTEXITCODE -ne 0) {
    throw "input generation failed"
}

@(
    "private_valid_vote.r1cs",
    "private_valid_vote.sym",
    "private_valid_vote_0000.zkey",
    "private_valid_vote.zkey",
    "verification_key.json",
    "proof.json",
    "public.json",
    "witness.wtns",
    "pot$($PtauPower)_0000.ptau",
    "pot$($PtauPower)_0001.ptau",
    "pot$($PtauPower)_final.ptau"
) | ForEach-Object {
    $Path = Join-Path $ArtifactDir $_
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -Force -LiteralPath $Path
    }
}
if (Test-Path -LiteralPath (Join-Path $ArtifactDir "private_valid_vote_js")) {
    Remove-Item -Recurse -Force -LiteralPath (Join-Path $ArtifactDir "private_valid_vote_js")
}
if (Test-Path -LiteralPath (Join-Path $ArtifactDir "private_valid_vote_4_8_js")) {
    Remove-Item -Recurse -Force -LiteralPath (Join-Path $ArtifactDir "private_valid_vote_4_8_js")
}

Write-Output "Compiling private_valid_vote_4_8.circom..."
& circom $Circuit --r1cs --wasm --sym -l $NodeModules -o $ArtifactDir
if ($LASTEXITCODE -ne 0) {
    throw "circom compile failed"
}

$R1csOut = Join-Path $ArtifactDir "private_valid_vote_4_8.r1cs"
$SymOut = Join-Path $ArtifactDir "private_valid_vote_4_8.sym"
$JsOut = Join-Path $ArtifactDir "private_valid_vote_4_8_js"
if (Test-Path -LiteralPath $R1csOut) {
    Move-Item -Force -LiteralPath $R1csOut -Destination (Join-Path $ArtifactDir "private_valid_vote.r1cs")
}
if (Test-Path -LiteralPath $SymOut) {
    Move-Item -Force -LiteralPath $SymOut -Destination (Join-Path $ArtifactDir "private_valid_vote.sym")
}
if (Test-Path -LiteralPath $JsOut) {
    $TargetJs = Join-Path $ArtifactDir "private_valid_vote_js"
    if (Test-Path -LiteralPath $TargetJs) {
        Remove-Item -Recurse -Force -LiteralPath $TargetJs
    }
    Move-Item -LiteralPath $JsOut -Destination $TargetJs
}

Write-Output "DEV ONLY: generating an unsafe local Powers of Tau and Groth16 zkey."
Write-Output "DEV ONLY: not for production or a competition final trusted setup."

$Ptau0000 = Join-Path $ArtifactDir "pot$($PtauPower)_0000.ptau"
$Ptau0001 = Join-Path $ArtifactDir "pot$($PtauPower)_0001.ptau"
$PtauFinal = Join-Path $ArtifactDir "pot$($PtauPower)_final.ptau"
$R1cs = Join-Path $ArtifactDir "private_valid_vote.r1cs"
$Zkey0000 = Join-Path $ArtifactDir "private_valid_vote_0000.zkey"
$Zkey = Join-Path $ArtifactDir "private_valid_vote.zkey"
$Vk = Join-Path $ArtifactDir "verification_key.json"

Invoke-Snarkjs powersoftau new bn128 "$PtauPower" $Ptau0000 -v
Invoke-Snarkjs powersoftau contribute $Ptau0000 $Ptau0001 --name="VeriVote M6B dev unsafe contribution" -e="verivote-m6b-dev-unsafe" -v
Invoke-Snarkjs powersoftau prepare phase2 $Ptau0001 $PtauFinal -v
Invoke-Snarkjs groth16 setup $R1cs $PtauFinal $Zkey0000
Invoke-Snarkjs zkey contribute $Zkey0000 $Zkey --name="VeriVote M6B dev unsafe zkey contribution" -e="verivote-m6b-dev-unsafe-zkey" -v
Invoke-Snarkjs zkey export verificationkey $Zkey $Vk

Write-Output "Artifacts written to $ArtifactDir"
