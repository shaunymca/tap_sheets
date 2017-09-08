## Google Sheets Tap

This is a Singer.io compliant (not yet) tap to stream data from Google Sheets to a Singer target.

## Running it locally

### Step 1: Activate the Google Sheets API

 (originally found in the [Google API
 docs](https://developers.google.com/sheets/api/quickstart/python))
 
 1. Use [this
 wizard](https://console.developers.google.com/start/api?id=sheets.googleapis.com)
 to create or select a project in the Google Developers Console and
 activate the Sheets API. Click Continue, then Go to credentials.

 1. On the **Add credentials to your project** page, click the
 **Cancel** button.

 1. At the top of the page, select the **OAuth consent screen**
 tab. Select an **Email address**, enter a **Product name** if not
 already set, and click the **Save** button.

 1. Select the **Credentials** tab, click the **Create credentials**
 button and select **OAuth client ID**.

 1. Select the application type **Other**, enter the name "Singer
 Sheets Tap", and click the **Create** button.

 1. Click **OK** to dismiss the resulting dialog.

 1. Click the Download button to the right of the client ID.

 1. Move this file to your working directory and rename it
 *client_secret.json*.
 
 
 ### Step 2: Configure

Create a file called `config.json` in your working directory,
following [config.sample.json](config.sample.json).

### Step 3: Install the tap and run in discovery mode
1. Run `python3 setup.py develop`, this will install the tap
2. Run `tap-sheets --discover --config config.json`, this will show the names and ids of your spreadsheets available. Use some of these to populate the **properties.json** file
3. Run `tap-sheets --config config.json --properties properties.json`, this will run the tap and give the current, non-singer compliant output.
