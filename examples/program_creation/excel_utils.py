"""
Excel utilities for program creation

Provides helper functions for Excel file manipulation, including auto-sizing columns.
"""

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


def auto_adjust_column_widths(
    excel_path: str, min_width: int = 10, max_width: int = 50
):
    """
    Automatically adjust column widths in an Excel file based on content

    Args:
        excel_path: Path to the Excel file
        min_width: Minimum column width (default: 10)
        max_width: Maximum column width (default: 50)
    """
    workbook = load_workbook(excel_path)

    for sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]

        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)

            for cell in column:
                try:
                    # Calculate cell content length
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass

            # Set column width with min/max constraints
            adjusted_width = min(max(max_length + 2, min_width), max_width)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    workbook.save(excel_path)


def create_excel_with_auto_width(
    file_path: str, dataframes: dict, min_width: int = 10, max_width: int = 50
):
    """
    Create an Excel file with multiple sheets and auto-adjusted column widths

    Args:
        file_path: Path for the output Excel file
        dataframes: Dictionary with sheet names as keys and DataFrames as values
        min_width: Minimum column width (default: 10)
        max_width: Maximum column width (default: 50)

    Example:
        create_excel_with_auto_width(
            "output.xlsx",
            {
                "program": program_df,
                "structures": structures_df,
                "sections": sections_df
            }
        )
    """
    import pandas as pd

    # Write DataFrames to Excel
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Auto-adjust column widths
    auto_adjust_column_widths(file_path, min_width=min_width, max_width=max_width)
