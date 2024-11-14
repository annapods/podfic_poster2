
# Set up

## OS and programs

Requires python, gtk, pip and gettext. On Linux, these can be installed with:

```bash
sudo apt-get python3
sudo apt-get pip
sudo apt-get gettext
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

Potentially, also:
```bash
sudo apt install libgirepository1.0-dev
sudo apt-get install libcanberra-gtk-module
unset GTK_PATH`
export GTK_PATH=/usr/lib/x86_64-linux-gnu/gtk-3.0`
```

I just couldn't figure out how to make it work in the VSCode terminal.

This version of the program was written with python3.10 and hasn't been tested with any other version.

## Git

The easiest way to get the files is to clone the git repository.

To install git:

```bash
sudo apt-get git
```

To clone the repository, create a folder wherever you want, open a terminal in the folder/navigate to it, and type:

```bash
git clone https://github.com/annapods/podfic_poster2.git
```

Feel free to create a branch if you want, or whatever else.

## Path to projects

TODO outdated
In src/project_files_tracker.py, edit the path to the parent folder of all the project folders.
In cli files, edit the path to the tracker.

## Virtual environment

Open up a terminal, cd to the repertory.

Linux/Mac:
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows:
```bash
python3.10 -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Ao3 downloader

Code [here](https://github.com/ericfinn/ao3downloader), this is an older version of [nianeyna's project](https://github.com/nianeyna/ao3downloader) that should be compatible with python<3.9. I haven't tested it yet, though.

First time running it, it will ask for user name and password, and save them in settings.json.

WARNING saves settings in plain text, which is not very secure... no idea how to do it
differently though.

## Internet archive

```bash
ia configure
```

Will ask for email and password and save them in ~/.config/internetarchive/ia.ini.

If this step fails with an interpreter error, check that the path to the current directory doesn't contain any whitespace.

## Google drive

- [Set up oauth](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id), with URI `http://localhost:8080`
- [Add the email address attached to the gdrive account as test user](https://console.developers.google.com/apis/credentials/consent?referrer=search&project=delta-entry-341918) (OAuth consent screen -> Test users)

## Ao3 poster

Will use the ao3-downloader settings, no need to do anything.

## Template filler

In order for the template filler to work, it needs some help translating from placeholders to an actual language. Currently, only English and French are suported. To compile the necessary files:

```bash
DIR=.locales
DOMAIN=template_filler
LANG=fr
msgfmt -o $DIR/$LANG/LC_MESSAGES/$DOMAIN.mo $DIR/$LANG/LC_MESSAGES/$DOMAIN.po
LANG=en
msgfmt -o $DIR/$LANG/LC_MESSAGES/$DOMAIN.mo $DIR/$LANG/LC_MESSAGES/$DOMAIN.po
```

See the TRANSLATEME.txt file for information on how to add new languages. To adapt the template itself, you'll most likely need to edit the template_filler.py file and then go through the translation process again.

## Tweeter promo

[Create an app](https://developer.twitter.com/en/portal/dashboard).

- App permission: Read and write and Direct message
- Type of App: Web App, Automated App or Bot
- Callback URI / Redirect URL: https://localhost/
- Website URL: https://twitter.com/

Save the API key and secret in settings.json as twitter_api_key and twitter_api_secret, or justs run the promo program and wait for it to ask you that information.

## Tumblr promo

[Register an app](https://api.tumblr.com/console/calls/user/info):

- Application name: Podfic Promo
- Application Description: Automatically post cover art, description of podfic and link to ao3
- Application Website: https://localhost/
- Default callback URL: https://localhost/
- OAuth2 redirect URLs (space separate): https://localhost/

Save OAuth Consumer Key and Consumer Secret under tumblr_consumer_key and tumblr_consumer_secret
in settings.json, add also the name of your blog under tumblr_blog_name, or just run the promo program and wait for it to ask you those informations.

## Database

The program uses an SQLite database. It is initialized thanks to the `data_model.ods` spreadsheet, which can be edited to pre-fill the data tables.

There is one tab per table, with the exact same name. Two tabs/tables are mandatory: data_table and data_field. Each column of a tab corresponds to a field in the corresponding table.

The data_table tab must contain two columns, table_name and sort_rows_by. The latter is the field to use to order the data in the table. It can be changed to any other field that exists in the data_field tab for that table, or to one of the automatically generated fields.

The data_field tab must contain 9 columns. Each line describes a field in a table:
- table_name, which should match the name in the data_table tab
- field_name
- type, which should match an existing SQL type
- foreign_key_table, the name of the table this field refers to, if applicable,
- mandatory, TRUE if this field must be filled when the line is created in the database
- default_value
- editable, TRUE if the field must be editable in the application when displaying the record
- part_of_display_name, TRUE if the field must be part of the unique identifier of the record and displayed when selecting a record
- display_order, the order in which to show the fields in the application

The columns default_value and display_order can be edited freely. Rows can be added.

3 fields are automatically added to every tableID:
- ID, the technical ID number, which is never shown to the user
- display_name, which is the concatenation of every field that is marked as part_of_display_name in the data_field table, and the unique combination that identifies records in a table
- creation_date, which is also automatically filled

Tabs for other tables can be added in order to pre-fill them in the database. In that case, the name of the tab must correspond to the name of the table, and the label of each column to the fields of the table as described in the data_field tab/table.

Once the spreadsheet ready, (re)initialize the database with the following command:

```Shell
python src\db_init.py
```

Be aware that this will overwrite any changes.

## Adapting the rest

TODO out of date
- template_filler.py: all of it, but mostly the contact info and the feedback policy
- whatever else
