### **Requirements**
_________
- **Python 3.11 -> [Help](#installing-python-311)** or greater
    - See **[Setting up Python](#setting-up-python)**
- Cube Coders AMP License
    - *https://cubecoders.com/AMP*
- Discord Bot Account

## **Setting up Python**
___
### Installing Python on Linux

A version of Python is installed on most Linux systems by default. It might not however include all the required packages.
- *Note* - For Debian/Ubuntu and similar systems, make sure you have the `pip` and `venv` packages installed.

For example, to install latest Python version available in the system repository, install:

    `python3 python3-pip python3-venv`

Or for a specific version:

    `python3.11 python3-pip python3.11-venv`

For RHEL or similar systems, consult your system documentation. An example might be:

    `python39 python3-devel`

### Installing Python on  Windows

Installers can be downloaded from [here](https://www.python.org/downloads/windows/).

1. Run the installer as Administrator, and select “Customize installation”. 
    - Make sure you select the option to install `pip`, and (under Advanced Options) the options to install Python for all users on the system and add it to the system’s environment variables. 
    - *Note* - This will mean Python is installed in Program Files and is essential to ensuring it can be used by AMP.

### Installing Python 3.11

Follow instructions listed above for your respective operating system. As of the current
`requirements.txt`, `numpy` and `yarl` are already pinned to versions with Python 3.11+
support (`numpy==2.1.3`, `yarl==1.18.0`) — no manual edits to `requirements.txt` are needed.
___


### **Creating a Discord Bot Account**
1. Please visit [Creating a Bot Account](https://discordpy.readthedocs.io/en/stable/discord.html)
    - Use this Scope and Permissions -> **[Permissions](/resources/Bot%20Permissions.png)**
    - Enable the Intents Gatekeeper Needs -> **[Intents](/resources/intents.jpg)**

## **Installation Methods**
___
### **Manual Instructions**
1. Create an AMP user for the Bot with `Super Admins` role, must be done on the Global AMP Home Screen GUI.
    - Usually this is the URL ending in **8080** when connecting to AMP. *(eg. `http://X.X.X.X:8080`)*
    - Remember the Log-in details for your newly created AMP user.
2. Copy [`.env.template`](/.env.template) to `.env` and fill in your credentials (or export the same variables in your process/service environment instead — useful for systemd `EnvironmentFile=` or container/secret-manager based deployments).
3. From Command Line run script `start.py` *(eg. `../Discord Bot/start.py`)*
    - Run the bot, it will finish installing the rest of the requirements.
4. See **[Interacting with the Bot~](#interacting-with-the-bot)**

### **AMP Instance Instructions**
1. Create an AMP user for the Bot with `Super Admins` role, must be done on the Global AMP Home Screen GUI.
    - Usually this is the URL ending in **8080** when connecting to AMP. *(eg. `http://X.X.X.X:8080`)*
2. Create a new instance of GatekeeperV2 in a container. *(The container option can be found under `Configuration -> New Instance Defaults`)*
3. Configure the settings in the GatekeeperV2 Instance under the `Configuration -> Bot Settings`, click `Update`, then start the bot.
4. See **[Interacting with the Bot~](#interacting-with-the-bot)**
___

## **Interacting with the Bot**
### **First Time Startup**
- After Gatekeeper has connected to your server, please run the command `$bot utils sync` inside the Discord server you invited to bot to. 
    - This should populate all of its available commands to your guild.
- See **[Commands](/docs/COMMANDS.md#ubot-commandsu)** for a full list of all Bot Commands and how to use them.
    

### **Updating the Command Tree**
- When commands are added or removed it is highly suggested that you `reset` your command tree and `re-sync`
    - See **[Bot Commands](/docs/COMMANDS.md#ubot-commandsu)** `/bot utils sync` for details on how to reset your local command tree.
    - **TIP**: Gatekeeper will reset and auto sync on updates that require a re-structure of the commands.
    
### **Setting up a NON-Discord Adminstrator Role for the Bot**
- Use `/bot moderator (role)` and the bot will add that role as the minimum required role to interact with the bot.
    - **TIP**: Use this if you want NON-Discord Admins to have the ability to interact with the bot
    - It does honor the role heirarchy set via `Discord -> Server Settings -> Roles`.
    - Want more control? See **[Setting up Custom Permissions](/docs/PERMISSIONS.md#permissions).**

### **Setting your AMP Console Channels**
- Use `/server console channel (channel)` and the bot will begin sending AMP Console messages to that channel. 
    - **TIP**: You can also send AMP Console commands through that Discord Channel to the Dedicated Server.
    - **ATTENTION**: Interacting with the console this way requires a special permission node `server.console.interact` or having Discord Admin and or Bot Moderator Role.

### **Setting your AMP Chat Channels**
- Use `/server chat channel (channel)` and the bot will begin sending AMP Chat messages to that channel. 
    - **TIP**: You can also send Chat messages through that Discord Channel to the Dedicated Server.

### **Setting your AMP Event Channels**
- User `/server event channel (channel)` and the bot will begin sending AMP Event messages to that channel.
    - Events are when a player Joins or Leaves and Achievements.

### **Setting your Whitelist Channel and Auto Whitelist Settings**
- Use `/whitelist request_channel (channel)` to set a channel for the bot to send Whitelist Request Approvals to.
    - **ATTENTION**: By default Auto-Whitelist is turned off, meaning someone with Discord Admin or Bot `Moderator` role or higher must approve the request.
- Use `/whitelist auto true` to allow the bot to handle whitelist requests.
    - **ATTENTION**: Gatekeeper has a **default wait time of 5 minutes**, after the wait time is up requests are auto-approved.
    - **TIP**: You can enable `Donators` to bypass the wait time after setting the `/bot donator` role.
- Use `/whitelist wait_time (time)` to adjust the Bot's wait time after a whitelist request.
    - **TIP**: You can set this value to `0` to allow the bot to instantly approve the users whitelist request..

### **Setting up Discord Role Whitelist Syncing**
- Have your players link their game account first via `/link minecraft (ign)` or `/link steam (steam)`.
    - **TIP**: Both show a preview (skin face / Steam avatar) with Confirm/Deny buttons before saving anything, so there's no need for Staff to run `/user add` on their behalf anymore.
- Use `/server settings whitelist_role_add (server, role)` to pick which Discord Role(s) grant Whitelist access to a Server.
    - **TIP**: You can add more than one Role per Server, and reuse the same Role across multiple Servers.
- Use `/whitelist_sync enabled true` to turn the sync on bot-wide.
    - **ATTENTION**: Gaining a configured Role Whitelists the Member automatically (as long as they've linked their account); losing the Role, or leaving the Guild, removes them again.
    - **TIP**: Use `/whitelist_sync interval (minutes)` to control how often the safety-net reconciliation pass runs (default `15` minutes), which catches any Role/Whitelist drift that happened while the bot was offline.

### **Setting up your Server Banner Displays**
- First, set all your servers settings/information. See [Server Commands](/docs/COMMANDS.md#server-commands)
    - Adjust your settings on via sub commands such as `Host`, `Description`, `DisplayName`, `Prefix` and `Whitelist` to name a few.
    - **TIP**: You can do this after you set your Display Banner location, the bot will updated the information automatically.

- Pick which style of Display you'd like. The Bot supports Discord Embeds or Custom Banner Images.
    - Use `/bot banner_settings type (type)` and select the type of display you'd like.
    - If you picked `Custom Banner Images` you can customize the colors of the text via `/server banner settings`

- See [Banner How-to](/docs/BANNER.md) for usage and customization.
______
## **Launch Args**
- These are append to the command line when launching the bot. *(eg. `start.py -super`)*
    - `-token` - Bypasse tokens validation check. *(Mandatory for AMP Template Installations/Operations)*
    - `-command` - Enable slash command print statements for user traceback. 
    - `-super` - This leaves AMP Super Admin role intact, use at your own risk.    
    - `-whitelist-only` - Restricts the bot's AMP role on the main instance to the minimum needed for Discord-Role<->Whitelist sync (no `Instances.*`/`ADS.*`/`FileManager.*`/`LocalFileBackup.*`). **⚠ Needs verification before relying on it in production** — see `CLAUDE.md`.
    - `-dev` - Enable development print statments. *(used for development)*
    - `-debug` - Enables *DEBUGGING* level for logging. *(used for development)*
    - `-discord` - Disables Discord Intigration *(used for testing)*

___
## **Using Gatekeeperv2 as a Service**
- **Secrets hygiene**: run Gatekeeper under a dedicated, non-root system user (not your personal SSH account, not `root`). Restrict `.env` to that user with `chmod 600 .env`, owned by the service user.
- Log into your dedicated server/VPS via root. 
- You are then going to use the following command to create a service script for your Gatekeeper `nano /etc/systemd/system/gatekeeper.service`
    - Once done, input the following information into the service file.

```ini
[Unit]
Description= GateKeeperv2
After= network.service

[Service]
Type= simple
User= # Dedicated non-root service user (eg. 'gatekeeper'), not root/your personal SSH user
WorkingDirectory= # This points to the directory of Gatekeeperv2 files (eg. '/home/gatekeeper')
ExecStart= #This points to the python3 script. (eg. 'ExecStart=/usr/bin/python3.9 /home/gatekeeper/start.py')
Restart= always 
RestartSec= 15

[Install]
WantedBy= multi-user.target
```

### __Then run these in the command line.__
```
systemctl daemon-reload
systemctl enable gatekeeper.service
systemctl start gatekeeper.service
```

## Useful Command
- Use `systemctl status gatekeeper.service` to see the status of the Gatekeeper Service!

*Thanks @LeviN*
___
