# Test-GroupResolver.ps1

function Test-GroupMembership {
    param(
        [string]$GroupName,
        [string]$DomainName = "SHAREGUARD"
    )
    
    Write-Host "`n============================================================"
    Write-Host "Testing Group: $DomainName\$GroupName" -ForegroundColor Cyan
    Write-Host "============================================================"
    
    # Test different methods of group resolution
    Write-Host "`n1. Testing Get-ADGroup..."
    try {
        $group = Get-ADGroup -Identity $GroupName -Properties Members, Description
        Write-Host "  ✓ Group found" -ForegroundColor Green
        Write-Host "  - Description: $($group.Description)"
        Write-Host "  - Distinguished Name: $($group.DistinguishedName)"
    }
    catch {
        Write-Host "  ✗ Error getting group: $_" -ForegroundColor Red
    }
    
    Write-Host "`n2. Testing Get-ADGroupMember..."
    try {
        $members = Get-ADGroupMember -Identity $GroupName
        Write-Host "  ✓ Found $($members.Count) members:" -ForegroundColor Green
        $members | ForEach-Object {
            Write-Host "  - $($_.SamAccountName) ($($_.ObjectClass))"
            # If member is a group, show its members too
            if ($_.ObjectClass -eq 'group') {
                try {
                    $nestedMembers = Get-ADGroupMember -Identity $_.SamAccountName
                    Write-Host "    Nested members:"
                    $nestedMembers | ForEach-Object {
                        Write-Host "    └─ $($_.SamAccountName) ($($_.ObjectClass))"
                    }
                }
                catch {
                    Write-Host "    └─ Error getting nested members: $_" -ForegroundColor Red
                }
            }
        }
    }
    catch {
        Write-Host "  ✗ Error getting members: $_" -ForegroundColor Red
    }
    
    Write-Host "`n3. Testing Net APIs..."
    try {
        $netGroup = net group "$GroupName" /domain
        Write-Host "  Net group output:" -ForegroundColor Yellow
        $netGroup | ForEach-Object {
            Write-Host "  $_"
        }
    }
    catch {
        Write-Host "  ✗ Error with net group: $_" -ForegroundColor Red
    }

    Write-Host "`n4. Testing ADSI..."
    try {
        $adsiGroup = [ADSI]"WinNT://$DomainName/$GroupName,group"
        $adsiMembers = @($adsiGroup.Invoke("Members"))
        Write-Host "  ✓ Found $($adsiMembers.Count) members via ADSI:" -ForegroundColor Green
        $adsiMembers | ForEach-Object {
            $member = $_.GetType().InvokeMember("Name", 'GetProperty', $null, $_, $null)
            Write-Host "  - $member"
        }
    }
    catch {
        Write-Host "  ✗ Error with ADSI: $_" -ForegroundColor Red
    }
}

# Test each group
$groups = @(
    'IT_Staff',
    'Folder_Admins',
    'Domain Users'
)

foreach ($group in $groups) {
    Test-GroupMembership -GroupName $group
}

Write-Host "`nTesting specific user membership..."
Write-Host "============================================================"
$testUser = "john.smith"

Write-Host "`nChecking group membership for $testUser..."
try {
    $userGroups = Get-ADPrincipalGroupMembership -Identity $testUser
    Write-Host "`nUser $testUser is a member of:" -ForegroundColor Green
    $userGroups | ForEach-Object {
        Write-Host "- $($_.Name) ($($_.GroupCategory)/$($_.GroupScope))"
    }
}
catch {
    Write-Host "Error getting user group membership: $_" -ForegroundColor Red
}