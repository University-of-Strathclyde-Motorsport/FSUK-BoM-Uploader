from . import importer
from .data import RowData, RowType
from .webinterface import WebInterface
import datetime as dt



class Uploader:
    def __init__(self,
                 base_revision: int = 1,
                 snapshot_label: str = "Bill of Materials",
                 upload_cost: bool = True):

        self.base_revision = base_revision
        self.snapshot_label = snapshot_label
        self.upload_cost = upload_cost
        self.upload_bill_of_materials()



    def upload_bill_of_materials(self) -> None:

        print("\nRunning FSUK Bill of Materials Uploader\n")

        data = importer.load_data() # Load and validate data
        self.web_interface = create_web_interface() # Log into FSUK account

        # Create new snapshot
        timestamp = dt.datetime.now().strftime("%d %b %y %H:%M")
        label = f"{self.snapshot_label} ({timestamp})"
        print(f"Creating new snapshot '{label}' " \
              f"from base revision {self.base_revision}...")
        self.web_interface.create_snapshot(self.base_revision, label)

        # Upload data
        print("Uploading bill of materials...")
        self.upload_data(data)
        print("Bill of materials uploaded successfully.")
    


    def upload_data(self, data: list[RowData]) -> None:

        self.current_system = ""
        self.current_assembly = ""
        self.current_part = ""

        for index, row in enumerate(data):

            current_row = f"({index + 1}/{len(data)})"
            row_type = row.row_type.lower()
            row_identifier = row.get_identifier()
            print(f"{current_row} Uploading {row_type} '{row_identifier}'...")

            if row.row_type == RowType.SYSTEM:
                self.current_system = row.system

            elif row.row_type == RowType.ASSEMBLY:
                self.current_assembly = row.assembly

            elif row.row_type == RowType.PART:
                self.upload_part(row)

            elif row.row_type == RowType.STEP:
                self.upload_step(row)



    def upload_part(self, data: RowData) -> None:
        try:
            self.web_interface.upload_part(data, system = self.current_system,
                                           assembly = self.current_assembly, upload_cost=self.upload_cost)
            self.current_part = data.part
        except:
            print(f"Error: Unable to upload part '{data.get_identifier()}'")
            self.current_part = ""



    def upload_step(self, data: RowData) -> None:
        if self.current_part == "":
            print(f"Error: Unable to upload step '{data.get_identifier()}; " \
                  "no parent part exists")
            return

        part_found = self.web_interface.select_part(self.current_part)
        if not part_found:
            print(f"Error: Unable to upload step '{data.get_identifier()}; " \
                  f"unable to locate parent part '{self.current_part}'")
            return
        
        self.web_interface.upload_step(data, upload_cost=self.upload_cost)



def create_web_interface() -> WebInterface:
    while True:
        username, password = get_username_and_password()
        print("Attempting to log into FSUK account...")
        try:
            web_interface = WebInterface()
            web_interface.log_in_to_account(username, password)
            print("Login successful.\n")
            return web_interface
        except:
            print("Login failed: invalid credentials.")
            try_again = input("Would you like to try again? (yes/no)")
            if try_again.lower() not in ["yes", "y"]:
                raise Exception("User exited programme.")



def get_username_and_password() -> tuple[str, str]:
    print("Please enter your FSUK credentials:")
    username = input("Username: ")
    password = input("Password: ")
    return username, password