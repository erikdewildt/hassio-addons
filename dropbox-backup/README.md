# Dropbox Backup Hassio.io Add-on

## Installation

1. Add this repository to Hassio.io
   Follow [the official instructions][third-party-addons] on the website of Home Assistant, and use the following URL:
   
   ```txt
   https://github.com/erikdewildt/hassio-addons
   ```
   
2. Install the "Dropbox Backup" add-on

3. Configure the add-on. Example configuration:

    ```json
    {
        "oauth_access_token": "<YOUR_ACCESS_TOKEN>",
        "remote_path": "/hassio-backups/",
        "number_to_keep_local": 7,
        "number_to_keep_remote": 7,
        "debug": false
     }
    ```

|Parameter|Required|Description|
|---------|--------|-----------|
|oauth_access_token|Yes|The dropbox access token (see below).|
|remote_path|Yes|The target directory in Dropbox where you want to upload the backups files.| 
|number_to_keep_local|Yes|Number of files to keep locally|
|number_to_keep_remote|Yes|Number of files to keep on Dropbox|
|max_use_dropbox_percentage|No|Limit the dropbox usage. (Tip: set the `number_to_keep_remote` to a large number to store as much backups as possible)|
|debug|No|Enable or disable debugging|

Please make sure that the amount of files on DropBox is larger then the amount of local snapshots. If this is not 
the case the addon will keep trying to sync the older snapshots to dropbox. 

### Creating a Dropbox Access Token

To access your personal Dropobox, this add-on requires an access token. Follow these steps to create an Access Token:

1. Go to https://www.dropbox.com/developers/apps
2. Click the "Create App" button
3. Follow the prompts to set permissions and choose a unique name for your "app" token.
   
Once you have created the token, copy it into this add-on's configuration under the oauth_access_token label.


## Usage

Dropbox Backup uploads all snapshot files in the Hassio.io `/backup` directory to the specified path in your Dropbox.
When the addon is started is wil listen for service calls. To invoke the backup sync invoke the `hassio.addon_stdin` 
service with the following service data:

```json
{
 "addon": "229f9685_dropbox_backup",
 "input":
    {
        "command": "sync"
    }
}
```

