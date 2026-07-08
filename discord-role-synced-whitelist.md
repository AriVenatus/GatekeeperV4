I would love to propose an extension of the bot's features: **An automated, role-based Whitelist Sync.**

Managing whitelists manually across multiple game servers (Minecraft, Rust, Palworld, etc.) is tedious. Linking Discord roles directly to AMP's whitelisting system would fully automate player onboarding and server security.

## Proposed Features

1.  **Discord Role to Whitelist Sync:**
    *   Administrators can define specific Discord roles in the AMP plugin configuration that grant server access.
    *   If a user has the designated role, they are automatically added to the server's whitelist.
    *   If they lose the role (or leave the Discord server), they are immediately removed from the whitelist.
2.  **Player Identity Database (Account Linking):**
    *   To make whitelisting work across different game types (Steam-based, Xbox, Epic, Minecraft UUIDs), the bot needs to map Discord IDs to game identifiers.
    *   Users should be able to link their accounts via a Discord slash command (e.g., `/link steam [SteamID64]` or via OAuth if possible).
    *   This creates new entries in the database: `Discord ID <---> SteamID / GUID / Minecraft UUID`.

## Proposed Workflows

### 1. Account Linking (One-Time Setup for Players)
```
[Player links discord and other accounts e.g. with command: /link steam <SteamID>] 
                │
                ▼
[Bot validates format & saves to DB]
  (Maps: Discord ID ──► SteamID / GUID)
```

### 2. Whitelist Sync Logic
```
          Does Discord Member have designated Role?
                         /            \
                       YES             NO
                       /                 \
[Trigger AMP API to Whitelist]     [Trigger AMP API to Remove/Deny]
(Using the linked Game ID/UUID)     (Instantly revokes server access)
```

### 3. Global Ban / Moderation
```
[Admin issues Discord Ban or /gban @User]
                    │
                    ▼
[Bot queries Plugin DB for linked Game IDs]
                    │
                    ▼
[Bot loops through all active AMP Instances]
                    │
                    ▼
[Executes native ban commands across all instances]
```


