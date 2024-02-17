# Database documentation

## Data model

The data model is separate from the data itself.
The DataModel object is initiated from a .ods spreadsheet.
This spreadsheet can be initiated from a database by the DataHandler.
The file contains two tabs, `data_table` and `data_field`.

### `data_table`

The `data_table` tab contains two columns, `table_name` and `sort_rows_by`.

- The values in `table_name` have to be unique, and the values in `table_display_name` as well.
- The column `sort_rows_by` contains the technical name of a field in the table, which is usually `display_name` or `row_order`.

### `data_field`

The `data_field` tab contains nine columns, which are as follows:

- `table_name` matches the technical name of a table in `data_table` and is mandatory.
- `field_name` is the technical name of the field and is mandatory. For any given table, the values in this column have to be unique.
- `type` is mandatory. More on types later.
- `foreign_key_table` is to be filled when the field is a foreign key table. It should contain the `table_name` of that foreign table. More on foreign keys later.
- `mandatory` is a boolean, which means that it can be equal to `TRUE` or `FALSE`. It is mandatory. IF true, the given field is mandatory.
- `default value`, not mandatory.
- `part_of_record_display_name` indicates whether the value of that field will be used to create the display name of the records in the table. It is a boolean and is mandatory. More on display names later on.
- `display_in_table` indicates whether the column will be displayed in generic GUI tables. It is a boolean and is mandatory. It is usually set to true.
- `display_order` indicates the order of the columns in generic GUI tables. It is an int and is not mandatory.

## Field types

There are [TODO] field types.

- [TODO]

## Technical ID, display names and foreign keys

Three fields are automatically added to every table:

- `ID`, the primary key, which is an automatically-incremented integer.
- `display_name`, the readable unique identifier of the record, which is a concatenation of the fields that the data model identifies as part of the display name.
- `creation_date`, the date of creation of the record.

ID are necessary because the components of display names could be edited. Foreign key fields always reference a record's ID but display names are used in the interface.
