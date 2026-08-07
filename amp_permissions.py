'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA. 
'''
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
        'Core.UserManagement.ViewUserInfo',
        'Instances.*',
        'ADS.*',
        '-ADS.TemplateManagement.*',
        'Settings.*',
        '-Settings.GSMyAdmin.*',
        '-Settings.ADSModule.*',
        '-Settings.FileManagerPlugin.*',
        '-Settings.EmailSenderPlugin.*',
        '-Settings.WebRequestPlugin.*',
        '-Settings.LocalFileBackupPlugin.*',
        '-Settings.steamcmdplugin.*',
        'ADS.InstanceManagement.*',
        '-ADS.InstanceManagement.RegisterToController',
        '-ADS.InstanceManagement.CreateInstance',
        '-ADS.InstanceManagement.SuspendInstances',
        '-ADS.InstanceManagement.UpgradeInstances',
        '-ADS.InstanceManagement.DeleteInstances',
        '-ADS.InstanceManagement.AttachRemoteADSInstance',
        '-ADS.InstanceManagement.RemoveRemoteADSInstance',
        '-ADS.InstanceManagement.EditRemoteTargets',
        '-ADS.InstanceManagement.Convert',
        '-ADS.InstanceManagement.Reconfigure',
        '-ADS.InstanceManagement.RefreshConfiguration',
        '-ADS.InstanceManagement.RefreshRemoteConfigStores',
        'FileManager.*',
        '-FileManager.FileManager.CreateArchive',
        '-FileManager.FileManager.ExtractArchive',
        '-FileManager.FileManager.ChangeBackupExclusions',
        '-FileManager.FileManager.ConnectViaSFTP',
        '-FileManager.FileManager.ModifyAMPConfigFiles',
        '-FileManager.FileManager.DownloadFromURL',
        'LocalFileBackup.*',
        '-LocalFileBackup.Backup.ViewBackupsList',
        '-LocalFileBackup.Backup.DeleteBackup',
        '-LocalFileBackup.Backup.RestoreBackup',
        '-LocalFileBackup.Backup.ToggleStickiness',
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
        'Core.UserManagement.ViewUserInfo']
    return core






        