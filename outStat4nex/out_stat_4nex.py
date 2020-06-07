'''

This is a utility program to retrieve well status information from Nexus output file
into Excel or simple text file.
Well rate and cumulative summary section are joined together into a single spreadsheet
indexed by reservoir name + well name + time
Status summary is added to each row together with basic rate, fluid ratios and
pressure related quantities for each well.

Usage: python outStat4nex.py <model.out> -o <out file name> -f <xls|txt>
'''
import os
import re
import sys
import getopt
from datetime import datetime
import pandas as pd
import xlsxwriter

# Global regex search pattern
PAT_US_TIME = re.compile(
    r"\s+MO/DAY/YR:\s+(?P<date>[0-9]{2}/[0-9]{2}/[0-9]{4})\s+(?P<time>[0-9.]+)")
PAT_EU_TIME = re.compile(
    r"\s+DAY/MO/YR:\s+(?P<date>[0-9]{2}/[0-9]{2}/[0-9]{4})\s+(?P<time>[0-9.]+)")
PAT_TOTAL_RES = re.compile(
    r"\s+Total\s+(?P<res>\w+)\s+")

def entry():
    '''
    Entry point for package distribution
    '''
    main(sys.argv[1:])

def _extract_summary(well_df, res_list, file_in, pat_header, items, items_index,
                     split_index=None, echo_date=False):
    '''
    Extract well summary table from Nexus .out file and generate a single summary table
    into a file either in Excel or ascii format

    Parameters:
    -----------
    well_df (dataframe) : dataframe to append parsed data t0
    res_list (list) : list of available reservoir, can be empty for single reservoir
    file_in (file object) : pointer to .out file to retrieve data from
    pat_header (regex pattern) : pattern to match to locate summary section
    items (list) : list of column names to fill with parsed data
    items_index (list of int) : list of index with parsed data positions on the .out line
    split_index (list of int) : list of index for which 1st part of item is kept
    echo_date (bool) : if true echo to stdout date found during parsing

    Returns:
    --------
    last line read when attempting to parse the summary section
    '''

    # Set current reservoir (for multifield)
    current_res = ""

    # Skip next line
    line = file_in.readline()
    line = file_in.readline()
    match_us = PAT_US_TIME.match(line)
    if match_us:
        current_date = datetime.strptime(match_us.group("date"), '%m/%d/%Y')
        current_time = float(match_us.group("time"))
    else:
        match_eu = PAT_EU_TIME.match(line)
        if match_eu:
            current_date = datetime.strptime(match_eu.group("date"), '%d/%m/%Y')
            current_time = float(match_eu.group("time"))

    # Echo date
    if echo_date:
        print("-->Extracting well status summary at {}".format(current_date.strftime("%d-%b-%Y")))

    # Read next till header match
    line = file_in.readline()
    while line:
        if pat_header.match(line):
            # Read next 2 lines
            # --- headers for fields delimiters
            line_sep = file_in.readline()
            index_list = [i for i in range(len(line_sep)) \
                          if (line_sep[i] == '-' and line_sep[i-1] == " ")]

            # Start with first res
            if len(res_list) > 0:
                current_res = res_list[0]

            # First data
            line = file_in.readline()
            while line:
                if re.match(r"\s+Total", line):
                    if len(res_list) == 0 or (len(res_list) > 1 and \
                       re.match(r"\s+Total\s+All\s+Reservoirs", line)):
                        line = file_in.readline()
                        break
                    else:
                        match_res = PAT_TOTAL_RES.match(line)
                        if match_res:
                            res_index = res_list.index(match_res.group("res")) + 1
                            current_res = res_list[res_index] if res_index < len(res_list) else ""
                elif line.count('-') < 100 and len(line) > 40:
                    # Format uses fixed length string with blanks for fields status
                    # reason plus constrained node/connection might be blank
                    item_list = []
                    for i, _ in enumerate(index_list):
                        idx_1 = index_list[i]
                        idx_2 = index_list[i + 1] if (i + 1) < len(index_list) else -1
                        item = line[idx_1:idx_2].strip()
                        if split_index is not None and i in split_index:
                            item = item.split()[0]
                        item_list.append(item)

                    # Append
                    row_index = (current_res, item_list[0], current_time)
                    is_in_index = well_df.index.isin([row_index])
                    if not is_in_index.any():
                        well_df.loc[row_index, "DATE"] = current_date

                    # Set properties from CUM table
                    well_df.loc[row_index, items] = [item_list[i] if i < len(item_list) else '' for i in items_index]
                    # print(well_df)

                line = file_in.readline()
            break
        line = file_in.readline()
    return line

def main(argv):
    '''
    Entry point for Nexus output file extraction module
    Parameters:
    -----------
    argv (list of str): command line arguments

    Returns:
    --------
    Subprocess int error code or 0 if successful
    '''

    # Command line arguments
    report_format, report_file = None, None
    try:
        opts, _ = getopt.getopt(argv[1:], "ho:f:", ["help", "out", "format"])
    except getopt.GetoptError:
        print("outStat4nex.py myNexusModel.out -o <report file name> -f <xls|txt>")
        sys.exit(2)

    # Make sure 1st argument is a valid file
    if len(argv) < 1:
        print("Missing Nexus output file argument")
        sys.exit(2)
    elif argv[0] in ("-h", "--help"):
        print("outStat4nex.py myNexusModel.out -o <report file name> -f <xls|txt>")
        sys.exit()
    else:
        fcs_out = argv[0]
        if not os.path.isfile(fcs_out):
            print("{} Nexus model output file does not exist".format(fcs_out))
            sys.exit(2)

    # Validate arguments
    for opt, arg in opts:
        if opt in ("-o", "-out"):
            report_file = arg
        elif opt in ("-f", "-format"):
            report_format = arg
            if not report_format in ("xlsx", "txt"):
                print("Report format must be either xlsx (Excel) or txt (ascii) : {}".format(arg))
                sys.exit(2)

    # Default value
    if report_format is None:
        report_format = "xlsx"
    if report_file is None:
        report_file = os.path.splitext(fcs_out)[0] + "_stat." + report_format

    # Setup patterns for faster match
    pat_rat_report = re.compile(r"\s+Active Well Rate Summary")
    pat_rat_header = re.compile(r"\s+Name\s+Number\s+CELL\s+IJK")
    pat_cum_report = re.compile(r"\s+Well Cumulative Summary")
    pat_cum_header = re.compile(r"\s+Name\s+Status\s+Reason\s+Connection\s+Number\s+CELL\s+IJK")
    res_list = []

    # Item headers for data frame
    item_headers = ["RESERVOIR", "WELL", "TIME", "DATE",
                    "STATUS", "STATUS_REASON", "STATUS_CONTROL_CON",
                    "1ST_COMPLETION",
                    "QOP", "QGP", "QWP", "QOI", "QGI", "QWI", "QGLG",
                    "WCUT", "GOR",
                    "WPAV", "BHP", "THP", "SAL"]
    # Items to retrieve from Cumulative wells summary:
    # note that index will work with 4.12 & 4.13 Nexus version
    # -> a change in version might cause issues
    cum_items = ["STATUS", "STATUS_REASON", "STATUS_CONTROL_CON", "1ST_COMPLETION", "WPAV"]
    cum_items_index = [1, 2, 3, 5, 15]
    # Items to retrieve from Rate wells summary:
    # note that index will work with 4.12 & 4.13 Nexus version
    # -> a change in version might cause issues
    rat_items = ["QOP", "QGP", "QWP", "QOI", "QGI", "QWI",
                 "GOR", "WCUT", "QGLG",
                 "BHP", "THP", "SAL"]
    rat_items_index = [3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 16, 17]


    # Instantiate a dict for keeping parsed data
    well_stat_df = pd.DataFrame(columns=item_headers)
    well_stat_df.set_index(item_headers[0:3], inplace=True)

    with open(fcs_out, 'r') as file_in:
        line = file_in.readline()
        while line:
            if pat_cum_report.match(line):
                line = _extract_summary(well_stat_df, res_list, file_in,
                                        pat_cum_header,
                                        cum_items, cum_items_index,
                                        split_index=[cum_items_index[-1]],
                                        echo_date=True)  # tokenize WPAV entry for comment
            elif pat_rat_report.match(line):
                line = _extract_summary(well_stat_df, res_list, file_in,
                                        pat_rat_header,
                                        rat_items, rat_items_index)
            elif len(res_list) == 0 and re.match(r"\s+Reservoir Summary", line):
                # Skip next 3 lines
                for _ in range(3):
                    next(file_in)
                line = file_in.readline()
                while line:
                    line_items = line.split()
                    if len(line_items) == 3:
                        res_list.append(line_items[0])
                        line = file_in.readline()
                    else:
                        break
            else:
                # Read next
                line = file_in.readline()

        # Close file
        file_in.close()

    # Reindex for multifield & easier excel generation
    well_stat_df = well_stat_df.sort_values(
        ['TIME', 'RESERVOIR', 'WELL']).reset_index(
            level='RESERVOIR')

    # Make sure some data were found
    if len(well_stat_df.index) > 0:

        # Make sure columns use proper format of data
        well_stat_df['DATE'] = pd.to_datetime(well_stat_df['DATE'])
        # Make sure all columns from rate summary are defined as float
        for col in rat_items:
            well_stat_df[col] = pd.to_numeric(
                well_stat_df[col], errors='coerce')
        # Make sure wpav column from cum summary is defined as float
        well_stat_df["WPAV"] = pd.to_numeric(
            well_stat_df["WPAV"], errors='coerce')

        # Get absolute path of report file
        data_folder = os.path.dirname(report_file)
        if not os.path.isabs(data_folder):
            data_folder = os.path.join(os.getcwd(), data_folder)

        print("-->Found {} records for well status, check file {} in folder {} for data".format(
            len(well_stat_df.index), 
            os.path.basename(report_file),
            os.path.normpath(data_folder)))
        if report_format == "xlsx":
            # Create a Pandas Excel writer using XlsxWriter as the engine.
            writer = pd.ExcelWriter(
                report_file, engine='xlsxwriter', datetime_format="dd-mmm-yyyy")

            # Convert the dataframe to an XlsxWriter Excel object.
            # startcol=0 if len(res_list) > 0 else 1)
            well_stat_df.to_excel(
                writer, sheet_name='Well_Status', float_format="%.2f")

            # Get the xlsxwriter workbook and worksheet objects.
            workbook = writer.book
            worksheet = writer.sheets['Well_Status']

            # Add some cell formats.
            format1 = workbook.add_format({'num_format': '0.00'})
            format2 = workbook.add_format({'num_format': '0.0000'})

            # Add a header format.
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'fg_color': '#D7E4BC',
                'border': 2})

            # Set col format
            col_headers = list(well_stat_df.index.names) + list(well_stat_df.columns)

            # header_first = 0 if len(res_list) > 0 else 1
            for id_col, col in enumerate(col_headers):
                # Reset col header
                worksheet.write(0, id_col, col, header_format)

                # Set the column width and format.
                if col in rat_items:
                    worksheet.set_column(
                        id_col, id_col, 12, format2 if col == "WCUT" else format1)
                elif col.startswith("STATUS"):
                    worksheet.set_column(id_col, id_col, 30)
                elif col.startswith("1ST"):
                    worksheet.set_column(id_col, id_col, 18)
                elif col.startswith("RES") and len(res_list) == 0:
                    worksheet.set_column(id_col, id_col, None, None, {'hidden': 1})
                else:
                    worksheet.set_column(id_col, id_col, 12)

            # Add filter on 1st columns (skip reservoir col for single field)
            worksheet.autofilter(0, 0, len(well_stat_df.index), 5)

            # Close writer and save
            writer.save()
        else:  # ascii
            well_stat_df.to_csv(
                report_file, float_format="%.2f", date_format="%d-%b-%Y")
    else:
        print("-->No well status record found in {}".format(os.path.basename(fcs_out)))
        sys.exit(2)


# Entry point when run as a script
if __name__ == "__main__":
    main(sys.argv[1:])
