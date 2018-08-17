## Google Sheets Tap

This is a Singer.io compliant (not yet) tap to stream data from Google Sheets to a Singer target.

## Running it locally

### Step 1: Configure

Create a file called `config.json` in your working directory,
following [config.sample.json](config.sample.json).

### Step 2: Activate the Google Sheets and Drive APIs

 (originally found in the [Google API
 docs](https://developers.google.com/sheets/api/quickstart/python))
 
 1. Create a project [here](https://console.developers.google.com/)

 1. Add the Google Sheets and Google Drive services from the library to the project

 1. In the credentials section, add OAUTH credentials, and select "web application" as the application type.

 1. Download the client id and secret and add them to the config.json file.

 1. Navigate to the [Google Oauth 2.0 playground](https://developers.google.com/oauthplayground)

 1. In the gear dropdown, choose "offline", and tick off the Use your own credentials

 1. Select the Drive Readonly API, and make sure that the Sheets API is selected also. Then click Authorize APIs

 1. Once you've logged in with a google account, click the Exhange authorization code for tokens button. Take the refresh token and place it into your config.json file.

### Step 3: Install the tap and run in discovery mode
1. Run `python3 setup.py develop`, this will install the tap
2. Run `tap-sheets --discover --config config.json > properties.json`, this will show the names and ids of your spreadsheets available. Use some of these to populate the **properties.json** file
3. Run `tap-sheets --config config.json --properties properties.json`, this will run the tap and give the current, non-singer compliant output.
