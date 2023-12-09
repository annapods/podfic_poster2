from sqlite3 import connect
from typing import Any, Optional, List, Tuple, Union
from pandas import ExcelWriter, Series, ExcelFile, read_sql_query
from numpy import nan
from os import remove
from os.path import exists
from src.base_object import BaseObject


class DBHanler(BaseObject):
    """ Virtual class for Database handlers """

    def __init__(self, database_path:str, verbose:bool=True):
        self.database_path = database_path
        super().__init__(verbose)
    
    def fetch_query(self):
        raise NotImplementedError
    
    def run_query(self):
        raise NotImplementedError
    
    def init_db_from_spreadsheet(self, spreadsheet_path:str="data_model_test.ods") -> None:
        """ Create/overwrite database based on spreadsheet """
        raise NotImplementedError
    
    def export_db_to_spreadsheet(self, spreadsheet_path:str="data_model_test.ods") -> None:
        """ Create/overwrite spreadsheet based on database """
        raise NotImplementedError


class SQLiteHandler(DBHanler):
    """ SQLite database handler """

    def __init__(self, database_path:str="db/podfics.db", verbose:bool=True):
        super().__init__(database_path, verbose)
        self.con = connect(self.database_path)
        self.cur = self.con.cursor()

    def __del__(self) -> None:
        """ Close connection on deletion of object """
        try: self.con.close()
        except AttributeError as e: pass


    def fetch_query(self, query:str, parameters:List[Any]) -> Tuple[List[str], List[List[Any]]]:
        """ Fetch results of the query, return headers and data """
        try:
            res = self.cur.execute(query, parameters)
        except Exception as e:
            print(query)
            raise e
        headers = list(map(lambda attr : attr[0], self.cur.description))
        data = res.fetchall()
        return headers, data

    def run_query(self, query:Union[str, Tuple[str,List[Any]]]) -> None:
        """ Run query """
        res = self.cur.execute(query)

    def _get_table_sort_by(self, table_name:str) -> str:
        """ Return sort_rows_by field for the given table """
        query = f'SELECT sort_rows_by FROM data_table WHERE table_name = "{table_name}"'
        headers, data = self.fetch_query(query, [])
        sort_by = data[0][0]
        return sort_by


    def get_table_contents_for_gui(
            self, table_name:str,
            field_names:Optional[List[str]]=[],
            sort_by:Optional[str]=None,
            where_condition:Optional[str]=None,
            ) -> Tuple[List[str], List[type], List[List[Any]]]:
        """ Get column names, column types, and data """

        # Get data fields info for the given table
        fields_info_query = f'''SELECT * FROM data_field WHERE table_name="{table_name}"'''
        if field_names:
            fields_info_query += f''' AND field_name IN ({", ".join("?"*len(field_names))})'''
        fields_info_query += ''' AND display_in_table = TRUE ORDER BY display_order'''
        field_names, field_info_lists = self.fetch_query(fields_info_query, field_names)
        field_info_dicts = [
            {column:value for column, value in zip(field_names, info)}
            for info in field_info_lists]
        
        # Get column names
        column_names = [field["field_name"] for field in field_info_dicts]
        
        # Get column types
        type_mapping = {"TEXT": str, "INTEGER": int, "BOOLEAN": bool, "DATE":str}
        column_types = [type_mapping[field["type"]] for field in field_info_dicts]

        # Get sort order
        if not sort_by: sort_by = self._get_table_sort_by(table_name)

        # Get data
        data_query = f'''SELECT {", ".join(column_names)} FROM {table_name}'''
        if where_condition: data_query += f''' WHERE {where_condition}'''
        data_query += f''' ORDER BY {sort_by}'''
        _, data = self.fetch_query(data_query, [])

        return column_names, column_types, data 
    

    def init_db_from_spreadsheet(
            self, spreadsheet_path:str="db/data_model.ods") -> None:
        """ Create/overwrite database based on spreadsheet """

        # Load model and data
        excel_file = ExcelFile(spreadsheet_path)
        data = {tab:excel_file.parse(tab) for tab in excel_file.sheet_names}

        # Clean data
        for tab in data:
            data[tab].dropna(how="all", inplace=True)
            data[tab].fillna(nan, inplace=True)
            data[tab].replace([nan], [None], inplace=True)

        # Generate sql for fields and tables

        def sql_field(x:Series) -> str:
            """ Generate sql code for one field.
            To be used with DataFrame.apply on data_field. """
            res = x["field_name"]+" "+x["type"]
            res += " NOT NULL" if x["mandatory"] else ""
            res += " DEFAULT "+str(x["default_value"]) if x["default_value"] else ""
            res += " REFERENCES "+x["foreign_key_table"]+\
                    "(display_name) ON UPDATE CASCADE ON DELETE SET DEFAULT" \
                if x["foreign_key_table"] else ""
            return res

        def sql_table(x:Series) -> str:
            """ Generate sql code for one table.
            To be used with DataFrame.apply on data_table. """
            res = "CREATE TABLE IF NOT EXISTS "+x["table_name"]+\
                "(ID INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            res += "display_name STRING GENERATED ALWAYS AS ("
            res += ' || " - " || '.join(data["data_field"][
                    (data["data_field"]["table_name"]==x["table_name"]) & \
                    (data["data_field"]["part_of_display_name"]==True)
                ]["field_name"]) + "),\n"
            res += ',\n'.join(data["data_field"][
                    data["data_field"]["table_name"]==x["table_name"]
                ]["sql"]) + ",\n"
            res += "creation_date DATE DEFAULT (datetime(current_timestamp))" + ")"
            return res

        data["data_field"]["sql"] = data["data_field"].apply(sql_field, axis=1)
        data["data_table"]["sql"] = data["data_table"].apply(sql_table, axis=1)

        # Delete and recreate database
        remove(self.database_path)
        self.con = connect(self.database_path)
        self.cur = self.con.cursor()

        # Create tables
        for table, command in zip(data["data_table"]["table_name"], data["data_table"]["sql"]):
            self.cur.execute("DROP TABLE IF EXISTS "+table)
            self.cur.execute(command)
        self.con.commit()

        # Drop working columns
        data["data_field"].drop("sql", axis=1, inplace=True)
        data["data_table"].drop("sql", axis=1, inplace=True)

        # Fill tables
        for table in data:
            # TODO check unknown fields and field order
            # TODO force type?
            data[table].to_sql(name=table, con=self.con, if_exists="append", index=False)
            # # Debug print
            # if self._verbose:
            #     headers, results = self.fetch_query(f"""SELECT * FROM {table}""")
            #     self._vprint(table)
            #     self._vprint(headers)
            #     self._vprint(results)
            #     self._vprint()


    def export_db_to_spreadsheet(
            self, spreadsheet_path:str="db/data_model_test.ods") -> None:
        """ Create/overwrite spreadsheet based on database """

        # Load DB data into dataframes
        tables = list(read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table';", self.con)['name'])
        data = {tbl : read_sql_query(f"SELECT * from {tbl}", self.con) for tbl in tables}
        
        # Delete existing spreadsheet if it exists
        if exists(spreadsheet_path): remove(spreadsheet_path)
        
        # Write to spreadsheet
        with ExcelWriter(spreadsheet_path, engine='odf') as writer:
            for tab in data:
                if tab == "sqlite_sequence": continue
                # Drop automatically generated columns
                data[tab].drop(["ID", "display_name", "creation_date"], axis=1, inplace=True)
                # Write table to tab
                data[tab].to_excel(writer, sheet_name=tab, index=False)
    
