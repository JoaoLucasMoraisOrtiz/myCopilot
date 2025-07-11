# Passo A: Encontre o caminho exato do seu chrome.exe. Este é o mais comum.
# VERIFIQUE SE ESTE CAMINHO ESTÁ CORRETO NO SEU PC!
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Passo B: Criamos a lista de argumentos. Cada item é separado por vírgula.
$arguments = @(
    "--remote-debugging-port=9222",
    "--remote-debugging-address=127.0.0.1",
    
    # --- A SOLUÇÃO ESTÁ AQUI ---
    # Adicionamos esta linha para permitir que scripts locais se conectem ao Chrome.
    "--remote-allow-origins=*", 

    # Usando um NOVO diretório de perfil para garantir que não há nada corrompido
    "--user-data-dir=C:\tmp\chrome_debug_profile_2",
    "--no-first-run",
    "--no-default-browser-check",
    
    # Usando uma URL simples para o teste
    "https://google.com"
)

# Passo C: Executamos o comando com o caminho e a lista de argumentos.
Write-Host "Iniciando o Google Chrome com os seguintes argumentos:"
Write-Host ($arguments -join " ")
Start-Process -FilePath $chromePath -ArgumentList $arguments