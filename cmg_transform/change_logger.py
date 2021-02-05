"""
    Singleton object to permit logging of each value before and after transformation 

"""
from pathlib import Path
from sqlite3 import connect
from colorama import init,Fore,Back,Style
init()

class ChangeLog:
	_instance = None
	_dataset_name = None

	# By Default, let's not log this stuff
	_active_log = False

	def __init__(self, file_path):
		self.cur = None
		if ChangeLog._active_log:
			self.filename = Path(file_path) / "change-log.db"

			must_init_db = not self.filename.is_file()
			self.db = connect(self.filename)
			self.cur = self.db.cursor()

			self.varids = {}

			if must_init_db:
				self.initdb()

			for (varid, name) in self.cur.execute("SELECT variable_id, name FROM variable_names"):
				self.varids[name] = varid

		# Drop everything in from prvious runs

	def purge_priors(self):
		if ChangeLog._active_log:
			# Drop the data from the current dataset
			print(f"Dropping data from {Fore.GREEN}{ChangeLog._dataset_name}{Fore.RESET}")
			self.cur.execute(f"DELETE FROM transformations WHERE dataset_name='{ChangeLog._dataset_name}'")
			print(f"{Fore.GREEN}Dropped{Fore.RESET}.")

	def initdb(self):
		if ChangeLog._active_log:

			print(f"Initializing data tables: {Fore.RED}variable_names, transformations{Fore.RESET}")
			self.cur.execute("""CREATE TABLE variable_names (
									variable_id INTEGER PRIMARY KEY AUTOINCREMENT,
									filename VARCHAR,
									name VARCHAR
								);""")

			self.cur.execute("""CREATE TABLE transformations(
								variable_id INTEGER NOT NULL,
								line_number INTEGER,
								dataset_name VARCHAR,
								orig_val VARCHAR,
								new_val VARCHAR
								);""")

			self.cur.execute("CREATE VIEW var_changes AS SELECT * FROM variable_names INNER JOIN transformations USING (variable_id)")

			# I'm expecting most queries will be by dataset name and maybe by end result values (like '')
			self.cur.execute("""CREATE INDEX tf_by_dataset_name ON transformations(dataset_name, new_val)""")

	def add_transformation(self, filename, varname, line_number, vprev, vnewval):
		if ChangeLog._active_log:

			if varname not in self.varids:
				try:
					self.cur.execute(f"""INSERT INTO 
											variable_names(filename, name) 
											VALUES ('{filename}', '{varname}')""")
					self.varids[varname] = self.cur.lastrowid
				except:
					print(f"There was a problem inserting {varname} into the variable names table")

			varid = self.varids[varname]

			try:
				newval = vnewval
				if newval is None:
					newval = ''

				prev = vprev
				if prev is None:
					prev = ''
				self.cur.execute(f"""INSERT INTO transformations VALUES (
									{varid}, 
									{line_number},
									'{ChangeLog._dataset_name}', 
									'{prev.replace("'", "''")}', 
									'{newval.replace("'", "''")}')""")
			except:
				print(f"""There was a problem inserting {varid}, 
									{line_number},
									'{ChangeLog._dataset_name}', 
									'{prev}', 
									'{newval}' into the transformations table""")

	def commit(self):
		if ChangeLog._active_log:
			self.db.commit()

	@classmethod
	def InitDB(cls, file_path, dataset_name, purge_priors=False):

		cls._dataset_name = dataset_name

		if cls._instance is None:
			cls._instance = cls(file_path)

		if cls._active_log:
			if purge_priors:
				cls._instance.purge_priors()
				
		return cls._instance.cur

	@classmethod
	def Close(cls):
		if cls._active_log:
			if cls._instance:
				cls._instance.commit()
