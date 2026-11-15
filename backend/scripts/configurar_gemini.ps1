# Grava a chave do Gemini em backend\.env sem aparecer na tela nem no histórico do terminal.
# Uso (PowerShell, na raiz do projeto):  powershell -ExecutionPolicy Bypass -File backend\scripts\configurar_gemini.ps1
# O arquivo .env é ignorado pelo Git. A chave não é enviada a lugar nenhum além do Google quando o jogo roda.

$arquivo = Join-Path $PSScriptRoot '..\.env'
$segura = Read-Host 'Cole a chave do Gemini e tecle Enter (nada aparece na tela)' -AsSecureString
$ponteiro = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)
$chave = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ponteiro)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ponteiro)
if ([string]::IsNullOrWhiteSpace($chave)) { Write-Host 'Nenhuma chave informada. Nada foi alterado.'; exit 1 }

$linhas = @()
if (Test-Path $arquivo) { $linhas = @(Get-Content $arquivo | Where-Object { $_ -notmatch '^(GEMINI_API_KEY|GEMINI_RECURSOS)=' }) }
$linhas += "GEMINI_API_KEY=$($chave.Trim())"
# O Gemini só reconhece o texto do jogador e entrega ao motor. Para ligar mais coisas depois: interpretar,mapear,narrar,perguntar
$linhas += 'GEMINI_RECURSOS=interpretar,mapear'
[IO.File]::WriteAllLines($arquivo, $linhas, (New-Object Text.UTF8Encoding($false)))
Write-Host "Pronto: chave gravada em $((Resolve-Path $arquivo).Path)"
Write-Host 'Agora rode a prova:  backend\.venv\Scripts\python.exe backend\scripts\provar_gemini.py'
