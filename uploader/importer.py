from .data import RowData, validate_data
from tkinter.filedialog import askopenfilename
from os.path import splitext
from csv import DictReader



VALID_FORMATS = [("CSV", ".csv")]
REQUIRED_FIELDS = {"system", "assembly", "part", "make_or_buy",
                   "step_type", "subtype", "comment", "quantity",
                   "cost", "cost_comment", "carbon_footprint", "carbon_comment"}



def load_data(delimiter: str = "|") -> list[RowData]:

    print("Please select a file to upload.")
    filepath = select_file()
    if filepath == "":
        raise Exception("No file selected. Exiting programme.")
    
    print(f"Loading data from '{filepath}'...")
    data = load_data_from_file(filepath, delimiter=delimiter)
    print(f"Loaded {len(data)} rows of data.\n")
    
    print("Validating data...")
    error_count = validate_data(data)
    if error_count > 0:
        message = f"{error_count} error(s) detected in data. Exiting programme."
        raise Exception(message)
    print("Successfully validated data.\n")

    return data



def select_file() -> str:
    title_text = "Select a Bill of Materials to upload"
    filepath = askopenfilename(title = title_text, filetypes = VALID_FORMATS)
    return filepath



def load_data_from_file(filepath: str, delimiter: str = "|") -> list[RowData]:

    _, file_extension = splitext(filepath)

    if file_extension not in [format[1] for format in VALID_FORMATS]:
        raise Exception(f"Unsupported file format '{file_extension}'")

    file = open(filepath, newline="")
    reader = DictReader(file, delimiter=delimiter)

    if reader.fieldnames == None:
        raise Exception(f"No data found in '{filepath}'")
    
    if not REQUIRED_FIELDS.issubset(set(reader.fieldnames)):
        raise Exception(f"Incorrect columns in '{filepath}'\n" \
                        f"Expected: {REQUIRED_FIELDS}")
    
    data: list[RowData] = []

    for row in reader:

        if row["quantity"] is None: row["quantity"] = 0
        if row["cost"] is None: row["cost"] = "NaN"
        if row["carbon_footprint"] is None: row["carbon_footprint"] = "NaN"

        data.append(RowData(
            system=row["system"],
            assembly=row["assembly"],
            part=row["part"],
            make_or_buy=row["make_or_buy"],
            step_type=row["step_type"],
            subtype=row["subtype"],
            comment=row["comment"],
            quantity=int(row["quantity"]),
            cost=float(row["cost"]),
            cost_comment=row["cost_comment"],
            carbon_footprint=float(row["carbon_footprint"]),
            carbon_comment=row["carbon_comment"]
        ))

    file.close()

    return data