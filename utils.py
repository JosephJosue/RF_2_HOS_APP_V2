import io
import pandas as pd
import zipfile

def to_excel(df: pd.DataFrame) -> bytes:
    """
    Converts a pandas DataFrame to an Excel file in memory.

    Args:
        df: The DataFrame to convert.

    Returns:
        bytes: The Excel file as a byte string.
    """
    output = io.BytesIO()
    # Use a with statement to ensure the writer is closed properly
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

def to_zip(files: dict[str, pd.DataFrame]) -> bytes:
    """
    Creates a zip archive from a dictionary of DataFrames.
    Each key-value pair in the dictionary corresponds to a file in the zip archive,
    where the key is the filename and the value is the DataFrame.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, df in files.items():
            # Convert DataFrame to Excel bytes
            excel_bytes = to_excel(df)
            # Write the bytes to the zip file
            zip_file.writestr(file_name, excel_bytes)
    
    return zip_buffer.getvalue()