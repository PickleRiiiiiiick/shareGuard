-- Update ShareGuardService account permissions to include folder permissions
UPDATE service_accounts 
SET permissions = JSON_ARRAY(
    'targets:read',
    'targets:create', 
    'targets:update',
    'targets:delete',
    'scan:execute',
    'scan:read',
    'folders:read',
    'folders:validate'
)
WHERE username = 'ShareGuardService' AND domain = 'shareguard.com';

-- Verify the update
SELECT id, username, domain, permissions 
FROM service_accounts 
WHERE username = 'ShareGuardService' AND domain = 'shareguard.com';