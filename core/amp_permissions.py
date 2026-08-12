# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
def perms_super():
    core = ['Core.*',
        'Core.RoleManagement.*',
        'Core.UserManagement.*',
        '-Core.Scheduler.*',
        '-Core.AuditLog.*',
        '-Core.RoleManagement.DeleteRoles',
        '-Core.RoleManagement.CreateCommonRoles',
        '-Core.UserManagement.UpdateUserInfo',
        '-Core.UserManagement.UpdateOwnAccount',
        '-Core.UserManagement.DeleteUser',
        '-Core.UserManagement.ResetUserPassword',
        '-Core.UserManagement.CreateNewUser',
        '-Core.UserManagement.ViewOtherUsersSessions',
        '-Core.UserManagement.EndUserSessions',
        # AMP's own description: "super-admin permission, must be used with caution" --
        # lets a user see/assign other users to roles they didn't create. Gatekeeper only
        # ever manages its own role membership, never needs this.
        '-Core.UserManagement.AccessExternalPermissions',
        # Only gates the GUI "active sessions" tab; getActiveAMPSessions() in AMP.py is
        # never called from anywhere in this codebase.
        '-Core.UserManagement.ViewActiveSessions',
        'Core.UserManagement.ViewUserInfo',
        'Instances.*',
        'ADS.*',
        '-ADS.TemplateManagement.*',
        # New category in this AMP build, not referenced anywhere in this codebase.
        '-ADS.DatastoreManagement.*',
        # No code anywhere in this repo makes a single Settings/* API call (confirmed via
        # grep) -- explicitly denied (not just omitted) so re-running permission setup
        # actively revokes it on a role that already has it granted from before.
        '-Settings.*',
        'ADS.InstanceManagement.*',
        '-ADS.InstanceManagement.RegisterToController',
        '-ADS.InstanceManagement.CreateInstance',
        '-ADS.InstanceManagement.SuspendInstances',
        '-ADS.InstanceManagement.UpgradeInstances',
        '-ADS.InstanceManagement.DeleteInstances',
        '-ADS.InstanceManagement.AttachRemoteADSInstance',
        '-ADS.InstanceManagement.RemoveRemoteADSInstance',
        '-ADS.InstanceManagement.EditRemoteTargets',
        # -ADS.InstanceManagement.Convert removed: not a recognized permission node
        # on current AMP versions (confirmed via Core/GetPermissionsSpec).
        '-ADS.InstanceManagement.Reconfigure',
        '-ADS.InstanceManagement.RefreshConfiguration',
        '-ADS.InstanceManagement.RefreshRemoteConfigStores',
        # Added in this AMP build after this list was first written -- bulk/ADS-wide
        # start/stop/restart and suspended-instance management. Gatekeeper only ever
        # acts on a specific instance via its own Instances.<uuid>.* node, never these.
        '-ADS.InstanceManagement.StartInstances',
        '-ADS.InstanceManagement.StopInstances',
        '-ADS.InstanceManagement.RestartInstances',
        '-ADS.InstanceManagement.ManageSuspendedInstances',
        # Currently granted on the live role from an untracked source (not set by any
        # code here) -- no Store/* API call exists anywhere in this codebase.
        '-Store.*',
        'FileManager.*',
        '-FileManager.FileManager.CreateArchive',
        '-FileManager.FileManager.ExtractArchive',
        '-FileManager.FileManager.ChangeBackupExclusions',
        '-FileManager.FileManager.ConnectViaSFTP',
        '-FileManager.FileManager.ModifyAMPConfigFiles',
        '-FileManager.FileManager.DownloadFromURL',
        # LocalFileBackup.* removed: not a recognized permission node on current AMP
        # versions (renamed/restructured server-side) -- setting it always fails and
        # blocked Gatekeeper role setup from ever completing. Revisit once the modern
        # equivalent node name is confirmed against Configuration -> Role Management.
        'Core.AppManagement.*',
        '-Core.AppManagement.UpdateApplication',
        '-Core.Special.*']
    return core


def perms_whitelist_only():
    """Minimal permission profile for the MAIN AMP instance (ID 0) Gatekeeper role, scoped to
    only what the bot needs to manage its OWN Gatekeeper role membership for the Discord-Role
    <-> Whitelist-Sync use case. Per-instance module permissions (e.g. Minecraft.*) are granted
    separately by each module's own setup_Gatekeeper_Permissions() override (see
    modules/Minecraft/amp_minecraft.py) and are unaffected by this profile."""
    core = ['Core.RoleManagement.*',
        '-Core.RoleManagement.DeleteRoles',
        '-Core.RoleManagement.CreateCommonRoles',
        'Core.UserManagement.*',
        '-Core.UserManagement.UpdateUserInfo',
        '-Core.UserManagement.UpdateOwnAccount',
        '-Core.UserManagement.DeleteUser',
        '-Core.UserManagement.ResetUserPassword',
        '-Core.UserManagement.CreateNewUser',
        '-Core.UserManagement.ViewOtherUsersSessions',
        '-Core.UserManagement.EndUserSessions',
        '-Core.UserManagement.AccessExternalPermissions',
        '-Core.UserManagement.ViewActiveSessions',
        'Core.UserManagement.ViewUserInfo']
    return core






        