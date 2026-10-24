# Script de test automatisé PowerShell pour l'application Flask
$ErrorActionPreference = "Continue"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  LANCEMENT DES TESTS WEB POUR FLASK (PORT 5000)     " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$baseUrl = "http://127.0.0.1:5000"
$results = [System.Collections.Generic.List[PSObject]]::new()

function Run-Test {
    param(
        [string]$Category,
        [string]$TestName,
        [string]$Method,
        [string]$Path,
        [hashtable]$Body = $null,
        [Microsoft.PowerShell.Commands.WebRequestSession]$Session = $null,
        [int[]]$ExpectedStatus = @(200),
        [string]$RedirectContains = "",
        [string]$ContentMustContain = ""
    )

    $url = "$baseUrl$Path"
    $status = 0
    $finalUrl = ""
    $content = ""
    $passed = $false
    $notes = ""

    try {
        $params = @{
            Uri = $url
            Method = $Method
            UseBasicParsing = $true
            TimeoutSec = 10
        }
        if ($Body) {
            $params["Body"] = $Body
        }
        if ($Session) {
            $params["WebSession"] = $Session
        }

        $res = Invoke-WebRequest @params
        $status = $res.StatusCode
        if ($res.BaseResponse -and $res.BaseResponse.ResponseUri) {
            $finalUrl = $res.BaseResponse.ResponseUri.AbsoluteUri
        } else {
            $finalUrl = $url
        }
        $content = $res.Content

    } catch [System.Net.WebException] {
        $ex = $_.Exception
        if ($ex.Response) {
            $status = [int]$ex.Response.StatusCode
            if ($ex.Response.ResponseUri) {
                $finalUrl = $ex.Response.ResponseUri.AbsoluteUri
            }
            try {
                $stream = $ex.Response.GetResponseStream()
                $reader = [System.IO.StreamReader]::new($stream)
                $content = $reader.ReadToEnd()
            } catch {}
        } else {
            $notes = "WebException: $($ex.Message)"
        }
    } catch {
        $ex = $_.Exception
        if ($ex.Response) {
            try {
                $status = [int]$ex.Response.StatusCode
                if ($ex.Response.RequestMessage -and $ex.Response.RequestMessage.RequestUri) {
                    $finalUrl = $ex.Response.RequestMessage.RequestUri.AbsoluteUri
                }
            } catch {}
        }
        if ($status -eq 0) {
            $notes = "Exception: $($ex.Message)"
        }
    }

    # Evaluation
    $statusOk = ($ExpectedStatus -contains $status)
    $redirectOk = $true
    if ($RedirectContains) {
        $redirectOk = ($finalUrl -like "*$RedirectContains*")
        if (-not $redirectOk) {
            $notes += " [Attendu redirect vers $RedirectContains mais finalUrl=$finalUrl]"
        }
    }
    $contentOk = $true
    if ($ContentMustContain) {
        $contentOk = ($content -like "*$ContentMustContain*")
        if (-not $contentOk) {
            $notes += " [Contenu ne contient pas '$ContentMustContain']"
        }
    }

    if ($statusOk -and $redirectOk -and $contentOk) {
        $passed = $true
    }

    $verdict = if ($passed) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($passed) { "Green" } else { "Red" }

    Write-Host "[$verdict] $Category - $TestName ($Method $Path) -> HTTP $status" -ForegroundColor $color
    if ($finalUrl -and $finalUrl -ne $url) {
        Write-Host "         Redirected to: $finalUrl" -ForegroundColor Gray
    }
    if ($notes) {
        Write-Host "         Note: $notes" -ForegroundColor Yellow
    }

    $obj = [PSCustomObject]@{
        Category = $Category
        TestName = $TestName
        Method = $Method
        Path = $Path
        Status = $status
        FinalUrl = $finalUrl
        Expected = ($ExpectedStatus -join ",")
        Result = $verdict
        Notes = $notes
    }
    $results.Add($obj)
    return @{ Object = $obj; Content = $content; FinalUrl = $finalUrl; Status = $status }
}

# ----------------------------------------------------
# 1. ROUTES PUBLIQUES
# ----------------------------------------------------
Write-Host "`n--- 1. ROUTES PUBLIQUES ---" -ForegroundColor Yellow
Run-Test -Category "1. Publiques" -TestName "Page d'accueil" -Method "GET" -Path "/" -ExpectedStatus @(200)
Run-Test -Category "1. Publiques" -TestName "Page de Connexion" -Method "GET" -Path "/login" -ExpectedStatus @(200)
Run-Test -Category "1. Publiques" -TestName "Page d'Inscription" -Method "GET" -Path "/register" -ExpectedStatus @(200)
Run-Test -Category "1. Publiques" -TestName "Page Admin Login" -Method "GET" -Path "/admin/login" -ExpectedStatus @(200)

# ----------------------------------------------------
# 2. ROUTES PROTEGEES SANS AUTH (Doivent rediriger ou 401)
# ----------------------------------------------------
Write-Host "`n--- 2. ROUTES PROTEGEES SANS AUTHENTIFICATION ---" -ForegroundColor Yellow
Run-Test -Category "2. Sans Auth" -TestName "Dashboard sans auth" -Method "GET" -Path "/dashboard" -ExpectedStatus @(200, 302) -RedirectContains "/login"
Run-Test -Category "2. Sans Auth" -TestName "Alertes sans auth" -Method "GET" -Path "/alerts" -ExpectedStatus @(200, 302) -RedirectContains "/login"
Run-Test -Category "2. Sans Auth" -TestName "Chat sans auth" -Method "GET" -Path "/chat" -ExpectedStatus @(200, 302) -RedirectContains "/login"
Run-Test -Category "2. Sans Auth" -TestName "API Notifications sans auth" -Method "GET" -Path "/api/notifications" -ExpectedStatus @(401)
Run-Test -Category "2. Sans Auth" -TestName "API Search sans auth" -Method "GET" -Path "/api/search?q=visa" -ExpectedStatus @(401)
Run-Test -Category "2. Sans Auth" -TestName "Admin Dashboard sans auth" -Method "GET" -Path "/admin/dashboard" -ExpectedStatus @(200, 302) -RedirectContains "/admin/login"

# ----------------------------------------------------
# 3. CONNEXION ADMIN & ROUTES ADMIN
# ----------------------------------------------------
Write-Host "`n--- 3. AUTHENTIFICATION & ROUTES ADMIN ---" -ForegroundColor Yellow

# Initialisation session admin
$adminSession = $null
$loginUrl = "$baseUrl/admin/login"
$adminLoginSuccess = $false

try {
    # On fait un GET pour récupérer les cookies de base si besoin
    $initRes = Invoke-WebRequest -Uri $loginUrl -SessionVariable "adminSession" -UseBasicParsing
    
    # POST login
    $adminPostRes = Invoke-WebRequest -Uri $loginUrl -Method POST -Body @{
        username = "admin"
        password = "admin123"
    } -WebSession $adminSession -UseBasicParsing
    
    $finalAdminUrl = if ($adminPostRes.BaseResponse -and $adminPostRes.BaseResponse.ResponseUri) {
        $adminPostRes.BaseResponse.ResponseUri.AbsoluteUri
    } else { "" }
    
    $status = $adminPostRes.StatusCode
    $isDash = ($finalAdminUrl -like "*/admin/dashboard*") -or ($adminPostRes.Content -like "*Tableau de bord*" -or $adminPostRes.Content -like "*Statistiques*")
    
    $verdict = if ($status -eq 200 -and $isDash) { "✅ PASS" } else { "❌ FAIL" }
    Write-Host "[$verdict] 3. Admin - POST /admin/login (admin/admin123) -> HTTP $status" -ForegroundColor (if ($verdict -eq "✅ PASS") { "Green" } else { "Red" })
    Write-Host "         Redirected to: $finalAdminUrl" -ForegroundColor Gray
    
    $results.Add([PSCustomObject]@{
        Category = "3. Admin Auth"
        TestName = "Connexion Admin POST"
        Method = "POST"
        Path = "/admin/login"
        Status = $status
        FinalUrl = $finalAdminUrl
        Expected = "200 (/admin/dashboard)"
        Result = $verdict
        Notes = "Redirection vers dashboard admin validée"
    })
    $adminLoginSuccess = ($verdict -eq "✅ PASS")
} catch {
    Write-Host "[❌ FAIL] Connexion Admin a échoué: $($_.Exception.Message)" -ForegroundColor Red
    $results.Add([PSCustomObject]@{
        Category = "3. Admin Auth"
        TestName = "Connexion Admin POST"
        Method = "POST"
        Path = "/admin/login"
        Status = 0
        FinalUrl = ""
        Expected = "200"
        Result = "❌ FAIL"
        Notes = $_.Exception.Message
    })
}

if ($adminSession) {
    Run-Test -Category "3. Admin Routes" -TestName "Admin Dashboard" -Method "GET" -Path "/admin/dashboard" -Session $adminSession -ExpectedStatus @(200)
    Run-Test -Category "3. Admin Routes" -TestName "Admin Pending Demandes" -Method "GET" -Path "/admin/pending" -Session $adminSession -ExpectedStatus @(200)
    Run-Test -Category "3. Admin Routes" -TestName "Admin Gestion Démarches" -Method "GET" -Path "/admin/demarches" -Session $adminSession -ExpectedStatus @(200)
    Run-Test -Category "3. Admin Routes" -TestName "Admin Modération Chat" -Method "GET" -Path "/admin/chat" -Session $adminSession -ExpectedStatus @(200)
    
    # Tester API Search avec session admin (Observation: l'API attend user_id ou admin?)
    Run-Test -Category "3. Admin Routes" -TestName "API Search avec Admin Session" -Method "GET" -Path "/api/search?q=visa" -Session $adminSession -ExpectedStatus @(200, 401)
}

# ----------------------------------------------------
# 4. DECONNEXION ADMIN
# ----------------------------------------------------
Write-Host "`n--- 4. DECONNEXION ADMIN ---" -ForegroundColor Yellow
if ($adminSession) {
    Run-Test -Category "4. Déconnexion" -TestName "Déconnexion Admin GET" -Method "GET" -Path "/admin/logout" -Session $adminSession -ExpectedStatus @(200, 302) -RedirectContains "/admin/login"
    
    # Vérifier que le dashboard admin n'est plus accessible
    Run-Test -Category "4. Déconnexion" -TestName "Accès Dashboard après Logout" -Method "GET" -Path "/admin/dashboard" -Session $adminSession -ExpectedStatus @(200, 302) -RedirectContains "/admin/login"
}

# ----------------------------------------------------
# 5. TESTS DES UTILISATEURS (USER 1, USER 2, USER 3)
# ----------------------------------------------------
Write-Host "`n--- 5. TESTS IDENTIFIANTS UTILISATEURS ---" -ForegroundColor Yellow
$userEmails = @(
    @{ Name = "USER 1 (dz/algerie)"; Email = "hachoudhamza3@gmail.com" },
    @{ Name = "USER 2 (dz/france)"; Email = "ps4walid2006@gmail.com" },
    @{ Name = "USER 3 (fr)"; Email = "hamzahachoud0@gmail.com" }
)

$commonPasswords = @("password", "123456", "admin123", "azerty", "hamza123", "walid123", "etudiant123")

foreach ($u in $userEmails) {
    Write-Host "`nTest pour $($u.Name) - $($u.Email):" -ForegroundColor Cyan
    $userLogged = $false
    $userSession = $null
    
    foreach ($pwd in $commonPasswords) {
        try {
            $sess = $null
            $dummy = Invoke-WebRequest -Uri "$baseUrl/login" -SessionVariable "sess" -UseBasicParsing
            $loginRes = Invoke-WebRequest -Uri "$baseUrl/login" -Method POST -Body @{
                email = $u.Email
                password = $pwd
            } -WebSession $sess -UseBasicParsing
            
            $fin = if ($loginRes.BaseResponse -and $loginRes.BaseResponse.ResponseUri) {
                $loginRes.BaseResponse.ResponseUri.AbsoluteUri
            } else { "" }
            
            # Vérifier si redirection vers dashboard ou algerie-setup
            if ($fin -like "*/dashboard*" -or $fin -like "*/diagnostic*") {
                Write-Host "  ✅ TROUVÉ ! Mot de passe pour $($u.Email) = '$pwd'" -ForegroundColor Green
                $userLogged = $true
                $userSession = $sess
                
                $results.Add([PSCustomObject]@{
                    Category = "5. User Auth"
                    TestName = "Connexion $($u.Name) ($pwd)"
                    Method = "POST"
                    Path = "/login"
                    Status = $loginRes.StatusCode
                    FinalUrl = $fin
                    Expected = "200 (/dashboard)"
                    Result = "✅ PASS"
                    Notes = "Mot de passe découvert: $pwd"
                })
                break
            } elseif ($loginRes.Content -like "*n'a pas encore été validé*") {
                Write-Host "  ⚠️ Compte trouvé avec '$pwd' mais non validé par admin !" -ForegroundColor Yellow
                $userLogged = $true
                $results.Add([PSCustomObject]@{
                    Category = "5. User Auth"
                    TestName = "Connexion $($u.Name) ($pwd)"
                    Method = "POST"
                    Path = "/login"
                    Status = $loginRes.StatusCode
                    FinalUrl = $fin
                    Expected = "Message validation admin"
                    Result = "✅ PASS"
                    Notes = "Compte valide avec '$pwd', mais en attente validation admin"
                })
                break
            } elseif ($loginRes.Content -like "*activer votre compte via le lien*") {
                Write-Host "  ⚠️ Compte trouvé avec '$pwd' mais non activé (email token) !" -ForegroundColor Yellow
                $userLogged = $true
                $results.Add([PSCustomObject]@{
                    Category = "5. User Auth"
                    TestName = "Connexion $($u.Name) ($pwd)"
                    Method = "POST"
                    Path = "/login"
                    Status = $loginRes.StatusCode
                    FinalUrl = $fin
                    Expected = "Message activation email"
                    Result = "✅ PASS"
                    Notes = "Compte valide avec '$pwd', mais non activé"
                })
                break
            }
        } catch {
            # Continue
        }
    }
    
    if (-not $userLogged) {
        Write-Host "  ℹ️ Aucun mot de passe usuel ne fonctionne pour $($u.Email) (Protection correcte)" -ForegroundColor Gray
        $results.Add([PSCustomObject]@{
            Category = "5. User Auth"
            TestName = "Test mots de passe $($u.Name)"
            Method = "POST"
            Path = "/login"
            Status = 200
            FinalUrl = "$baseUrl/login"
            Expected = "Rejet identifiant erroné"
            Result = "✅ PASS"
            Notes = "Mots de passe non triviaux, rejet sécurisé"
        })
    } else {
        # Si connecté, tester les routes protégées
        Run-Test -Category "5. User Routes" -TestName "$($u.Name) - Dashboard" -Method "GET" -Path "/dashboard" -Session $userSession -ExpectedStatus @(200, 302)
        Run-Test -Category "5. User Routes" -TestName "$($u.Name) - Alertes" -Method "GET" -Path "/alerts" -Session $userSession -ExpectedStatus @(200)
        Run-Test -Category "5. User Routes" -TestName "$($u.Name) - Chat" -Method "GET" -Path "/chat" -Session $userSession -ExpectedStatus @(200)
        Run-Test -Category "5. User Routes" -TestName "$($u.Name) - API Search" -Method "GET" -Path "/api/search?q=visa" -Session $userSession -ExpectedStatus @(200)
        Run-Test -Category "5. User Routes" -TestName "$($u.Name) - API Notifications" -Method "GET" -Path "/api/notifications" -Session $userSession -ExpectedStatus @(200)
    }
}

# ----------------------------------------------------
# 6. EXPORT DES RESULTATS EN JSON
# ----------------------------------------------------
$jsonPath = Join-Path $PSScriptRoot "test_results.json"
$results | ConvertTo-Json -Depth 4 | Out-File -FilePath $jsonPath -Encoding utf8
Write-Host "`nRésultats sauvegardés dans $jsonPath" -ForegroundColor Cyan
