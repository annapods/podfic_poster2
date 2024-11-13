""" Database handlers """

from sqlite3 import OperationalError, connect
from typing import Any, Dict, Literal, Optional, List, Tuple, Union
from pandas import ExcelWriter, Series, ExcelFile, read_sql_query, DataFrame
from numpy import nan
from os import remove
from os.path import exists
from db.db_objects import DataModel, Field, Record, Table, clean_df
from src.base_object import BaseObject



class Singleton(type): 
    # Inherit from "type" in order to gain access to method __call__
    def __init__(self, *args, **kwargs):
        self.__instance = None # Create a variable to store the object reference
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            # if the object has not already been created
            self.__instance = super().__call__(*args, **kwargs) # Call the __init__ method of the subclass (Spam) and save the reference
            return self.__instance
        else:
            # if object (Spam) reference already exists; return it
            return self.__instance


class DataHandler(BaseObject, metaclass=Singleton):
    """ Virtual class for Database handlers
    Database handlers load in memory the model of the database, but they don't load the data itself
    They can however read, create, modify and delete the records in the database """

    def __init__(self, database_path:str, datamodel_path:str="db/datamodel.ods", verbose:bool=True):
        super().__init__(verbose)
        self.database_path = database_path
        self.data_model = DataModel(datamodel_path)
    
    def init_db_from_model(self) -> None:
        """ Create/overwrite database based on model """
        raise NotImplementedError
    
    def load_db_from_spreadsheet(self) -> None:
        """ Overwrite database data with spreadsheet data """
        raise NotImplementedError
    
    def export_db_to_spreadsheet(self) -> None:
        """ Create/overwrite spreadsheet data with database data """
        raise NotImplementedError

    def get_records(self) -> List[Record]:
        """ Return records from database """
        raise NotImplementedError
    
    def add_record(self, record:Record) -> None:
        """ Add (insert or fail) a new record in the database """
        raise NotImplementedError
    
    def edit_record(self, record:Record) -> None:
        """ Edit (update or fail) an existing record in the database """
        raise NotImplementedError
    
    def delete_record(self, record:Record) -> None:
        """ Delete a record in the database """
        raise NotImplementedError



class SQLiteHandler(DataHandler):
    """ SQLite database handler """

    # There are more data types in our application than in sqlite3
    type_mapping = {"TEXT": "TEXT", "INTEGER": "INTEGER", "BOOLEAN": "BOOLEAN", "DATE":"DATE", "FILEPATH":"TEXT", "LENGTH":"TEXT"}

    def __init__(
            self, database_path:str="db/podfics.db", datamodel_path:str="db/datamodel.ods",
            verbose:bool=True):
        super().__init__(database_path, datamodel_path, verbose)
        self.con = connect(self.database_path)
        self.cur = self.con.cursor()

    def __del__(self) -> None:
        """ Close connection on deletion of object """
        try: self.con.close()
        except AttributeError as e: pass

    def run_query(self, query:str, parameters:List[Any]) -> List[List[Any]]:
        """ Fetch results of the query """
        try:
            res = self.cur.execute(query, parameters)
        except Exception as e:
            print("DEBUG query failed", query)
            self._vprint("DEBUG headers", list(map(lambda attr : attr[0], self.cur.description)))
            self._vprint("DEBUG data", res.fetchall())
            raise e
        self.con.commit()
        return res
    
    def debug_schema(self, debug_table="archive_warning") -> None:
        """ Print database schema and one table for debug purposes """
        schema = self.run_query("""
            WITH tables AS (SELECT name tableName, sql 
            FROM sqlite_master WHERE type = 'table' AND tableName NOT LIKE 'sqlite_%')
            SELECT fields.name, fields.type, tableName
            FROM tables CROSS JOIN pragma_table_info(tables.tableName) fields""", []).fetchall()
        print("DB schema:", schema)
        try:
            table_contents = self.run_query(f"SELECT * FROM {debug_table};", []).fetchall()
            print(debug_table+":", table_contents)
        except OperationalError as e:
            print(debug_table+":", e)
        print()

    
    def init_db_from_model(self) -> None:
        """ Create/overwrite database based on model """
        
        def get_field_sql(field:Field) -> str:
            sql = f"{field.field_name} {SQLiteHandler.type_mapping[field.type]}"
            sql += " NOT NULL" if field.mandatory else ""
            sql += f" DEFAULT {field.default_value}" if field.default_value else ""
            sql += f" REFERENCES {field.foreign_key_table.display_name}(ID)" +\
                " ON UPDATE CASCADE ON DELETE SET DEFAULT" \
                if field.foreign_key_table else ""
            return sql
        
        def get_table_sql(table:Table) -> str:
            sql = f"CREATE TABLE IF NOT EXISTS {table.table_name}"
            sql += "(ID INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            sql += "display_name STRING UNIQUE GENERATED ALWAYS AS ("
            sql += ' || " - " || '.join([
                    f.field_name for f in table.fields \
                    if f.part_of_display_name])
            sql += "),\n"
            sql += ',\n'.join(
                get_field_sql(field) for field in table.fields
                if field.field_name not in ["ID", "display_name", "creation_date"]) + ",\n"
            sql += "creation_date DATE DEFAULT (datetime(current_timestamp))" + ")"
            return sql

        # Delete and recreate database
        remove(self.database_path)
        self.con = connect(self.database_path)
        self.cur = self.con.cursor()

        # Create tables
        for table in self.data_model.tables:
            self.cur.execute("DROP TABLE IF EXISTS "+table.table_name)
            self.cur.execute(get_table_sql(table))
        self.con.commit()

    def export_db_model_to_spreadsheet(self, spreadsheet_path:str="db/database.ods") -> None:
        """ Overwrite spreadsheet data model with database model """
        schema = self.run_query("""
            WITH tables AS (SELECT name tableName, sql 
            FROM sqlite_master WHERE type = 'table' AND tableName NOT LIKE 'sqlite_%')
            SELECT tableName, name, type, notnull, dflt_value, pk
            FROM tables CROSS JOIN pragma_table_info(tables.tableName) fields""", []).fetchall()
        # TODO
        pass

    
    def load_db_from_spreadsheet(
            self, spreadsheet_path:str="db/database.ods",
            mode:Literal["add or fail", "add or ignore", "update or add", "delete and add"
                ]="update or add"
            ) -> None:
        """ Populates database data with spreadsheet data
        WARNING add or fail mode will fail if a spreadsheet record's display name already exists
        WARNING delete and add mode will delete all prior records in the table """
        # Load spreadsheet data
        excel_file = ExcelFile(spreadsheet_path)
        data = {tab:clean_df(excel_file.parse(tab)) for tab in excel_file.sheet_names}
        # Fill tables
        for table_name in data:
            # Check for unknown table or fields and get the existing ones
            table = self.data_model.get_table(table_name)
            fields = table.get_fields(data[table_name].columns)
            rows = [[i for i in row] for row in data[table_name].itertuples(index=False)]
            # Empty the database table if requested
            if mode == "delete and add": self.clear_table(table)
            # DataFrame.to_sql doesn't fill generated fields so it cannot be used
            # data[table_name].to_sql(name=table_name, con=self.con, if_exists="replace", index=False)
            for row in rows:
                to_add = Record(table, values={field:value for field, value in zip(fields, row)})
                if mode=="add or fail" or mode=="delete and add":
                    self.create_record_or_fail(to_add) 
                elif mode=="update or add":
                    self.create_or_update_record(to_add)
                elif mode=="add or ignore":
                    self.create_record_or_ignore(to_add)
                else: raise ArgumentError(None, message=
                    "mode must be one of: add or fail, update or add, delete and add, add or ignore")

    
    def export_db_to_spreadsheet(
            self, table_names:Optional[List[str]]=[], spreadsheet_path:str="db/database_out.ods",
            ) -> None:
        """ Create/overwrite spreadsheet data with database data
        It is recommended to specify which tables to export
        WARNING will delete the previous file if it exists """

        if table_names:
            # Double check tables
            tables = [self.data_model.get_table(name) for name in table_names]
        else:
            tables = self.data_model.tables
            print("Exporting tables:", tables)
        # Load DB data into dataframes
        data = {
            table.table_name: read_sql_query(f"SELECT * from {table.table_name}", self.con)
            for table in tables}
        
        # Delete existing spreadsheet if it exists
        if exists(spreadsheet_path): remove(spreadsheet_path)
        
        # Write to spreadsheet
        with ExcelWriter(spreadsheet_path, engine='odf') as writer:
            for tab in data:
                # Drop automatically generated columns
                data[tab].drop(["ID", "display_name", "creation_date"], axis=1, inplace=True)
                # Write table to tab
                data[tab].to_excel(writer, sheet_name=tab, index=False)

    
    def get_records(
            self, table:Table|str,
            sort_by:Optional[str]=None,
            where_condition:Optional[str]=None
            ) -> List[Record]:
        """ Return records from database """
        # If table name was given instead of table object, check it exists and get it
        if type(table) == str:
            table = self.data_model.get_table(table)

        # Check or get sort by field
        if sort_by: _ = table.get_field(sort_by)
        elif table.sort_rows_by: sort_by = table.sort_rows_by.field_name  # = None # DEBUG
        else: sort_by = None

        # Build query
        data_query = f'''SELECT *'''
        data_query += f''' FROM {table.table_name}'''
        if where_condition: data_query += f''' WHERE {where_condition}'''
        if sort_by: data_query += f''' ORDER BY {sort_by}'''
        # Fetch data
        data = self.run_query(data_query, []).fetchall()

        # Get non-automatic fields
        # headers = list(map(lambda attr : attr[0], self.cur.description))
        records = [Record(table, {h:v for h, v in zip(table.fields, values)}) for values in data]
        return records
    
    def get_record(
            self, table:Table|str,
            display_name:str
        ) -> Record:
        """ Return record from database """
        # If table name was given instead of table object, check it exists and get it
        if type(table) == str:
            table = self.data_model.get_table(table)
        
        # Build query
        data_query = f'''SELECT *'''
        data_query += f''' FROM {table.table_name}'''
        data_query += f''' WHERE {table.table_name}.display_name = "{display_name}";'''
        # Fetch data
        data = self.run_query(data_query, []).fetchall()[0]

        # Get non-automatic fields
        # headers = list(map(lambda attr : attr[0], self.cur.description))
        record = Record(table, {h:v for h, v in zip(table.fields, data)})
        print("DEBUG","record",record)
        return record

    
    def clear_table(self, table:Table) -> None:
        """ Empty the given table of all records """
        existing_records = self.get_records(table.table_name)
        for record in existing_records:
            self.delete_record_or_fail(record)

    def create_or_update_record(self, record:Record) -> None:
        """ Add a record in the database, update it if it already exists """
        fields = [field.field_name for field in record.values]
        values = [f'"{value}"' for value in record.values.values()]
        sql = f"INSERT INTO {record.parent_table.table_name} ({', '.join(fields)})"
        sql += f" VALUES ({', '.join(values)}) ON CONFLICT(display_name) DO UPDATE SET "
        sql += ', '.join(f'{f}={v}' for f, v in zip(fields, values))
        sql += ";"
        self.run_query(sql, [])

    def create_record_or_fail(self, record:Record) -> None:
        """ Add a record in the database, fail if it already exists """
        sql = f"INSERT OR FAIL INTO {record.parent_table.table_name} ("
        sql += ', '.join([field.field_name for field in record.values])
        sql += ") VALUES ("
        sql += ', '.join(f'"{value}"' for value in record.values.values())
        sql += ");"
        self.run_query(sql, [])

    def create_record_or_ignore(self, record:Record) -> None:
        """ Add a record in the database, pass if it already exists """
        sql = f"INSERT OR IGNORE INTO {record.parent_table.table_name} ("
        sql += ', '.join([field.field_name for field in record.values])
        sql += ") VALUES ("
        sql += ', '.join(f'"{value}"' for value in record.values.values())
        sql += ");"
        self.run_query(sql, [])
    
    def update_record_or_fail(self, record:Record) -> None:
        """ Update a record in the database, fail if it doesn't exist """
        sql = f"UPDATE OR FAIL {record.parent_table.table_name} SET "
        sql += ', '.join([
            '='.join(field.field_name, value)
            for field, value in record.values.items()])
        sql += f"WHERE {record.parent_table.table_name}.ID = {record.ID};"
        self.run_query(sql, [])
    
    def delete_record_or_fail(self, record:Record) -> None:
        """ Delete a record in the database, fail if it doesn't exist """
        raise NotImplementedError  # TODO
    
    def delete_record_or_ignore(self, record:Record) -> None:
        """ Delete a record in the database, pass if it doesn't exist """
        raise NotImplementedError  # TODO


if __name__ == "__main__":
    handler = SQLiteHandler(database_path="db/podfics.db", datamodel_path="db/datamodel.ods")
    handler.init_db_from_model()
    handler.load_db_from_spreadsheet(spreadsheet_path="db/datamodel.ods", mode="delete and add")
    handler.load_db_from_spreadsheet(spreadsheet_path="db/set_options.ods", mode="delete and add")
    handler.load_db_from_spreadsheet(spreadsheet_path="db/parameters.ods", mode="delete and add")
    handler.export_db_to_spreadsheet(spreadsheet_path="db/database_out.ods")
