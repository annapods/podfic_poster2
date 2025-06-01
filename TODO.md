# TODO

## Database

[x] init from spreadsheet
[x] save in spreadsheet
[x] debug_schema
[x] fill static tables
[x] debug display name concatenation
[x] delete_record_or_fail
[x] delete_record_or_ignore
[x] data validation functions -> used at Record creation

[ ] parameter table and secrets
[ ] DBHandler() returns the singleton object -> no need to pass the reference in calls
[ ] save data model to spreadsheet
[ ] test saving to spreadsheet then init from spreadsheet with all data types/configs


## Graphic interface

[ ] Database Manager / bricks
    [x] pick database
    [x] pick table
        [x] column order
    [x] pick record
    [x] reload dynamically
    [x] show record
        [x] text
        [x] boolean
        [x] int
        [x] filepath
        [x] length
        [x] date
        [x] ext no options
        [x] ext radio buttons
        [x] ext dropdown
        [x] ext table
        [x] ext popup to create/modify/delete
        [x] ext switch between widget types
    [ ] table search
    [x] create record
        [x] autoselect the newly created record
    [x] modify record
        [x] keep modified record selected
    [x] delete record
        [x] sql handler functions
        [x] if record selected, confirmation popup
        [x] if no record selected, info popup and no action
        [ ] remove horizontal scroll on popup
    [x] cancel
        [x] if record selected, reset to current record
        [x] if no record selected, reset to default values
    [ ] fix horizontal stretch when showing record form

[ ] Projects
    [ ] KPIs?
    [ ] project structures?
    [ ] Project overview + select table?
        [ ] projects
        [ ] project sections?
        [ ] stage+status
        [ ] sum up stage+status?
        [ ] edit selected?
    [ ] Project sections overview + selection?
        [ ] based on project selected
        [ ] view+edit stage+status
        [ ] edit selected?
    [ ] Create new
        [ ] new project
            [ ] from folder?
            [ ] from html?
            [ ] from scratch?
            [ ] save to db
        [ ] new section
            [ ] from folder?
            [ ] from html?
            [ ] from scratch?
            [ ] save to db
    [ ] actions
        [ ] setup
            [ ] download from ao3
            [ ] extract info from html -> placeholders? approval before creation?
        [ ] post
            [ ] project as a whole as a single chaptered work
            [ ] project as a multichaptered work
            [ ] section as a new chapter in a work
            [ ] section as a new work (+occasions to tie it back?)
            [ ] automatic file discovery and setup
            [ ] gd setup
            [ ] ia setup
            [ ] aa setup?
            [ ] ao3 draft
            [ ] ia summary
        [ ] promo
            [ ] bsky?
            [ ] tumblr
            [ ] mastodon??
            [ ] dw
        [ ] archive
            [ ] backup audio??
            [ ] gd metadata?
            [ ] ia metadata?

[ ] user settings
    [ ] secrets
    [ ] database file
    [ ] me person?
    [ ] log level

## Basics

[ ] Gtk app??? how to automate tests pls
[ ] separate GUI and workflow? -> turn GUI bricks into a python library/separate project
[ ] turn db handler into another library? or already separate enough?
[ ] model view controler whatever??
