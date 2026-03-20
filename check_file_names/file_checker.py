"""Checks that files are consistent with DS conventions."""

import os
import sys
from datetime import date


def main():
    print('This program checks that files are consistent with DS conventions for archival and cataloged collections:'
          '\n\t- All files are either .tifs or .jp2s'
          '\n\t- File names do not contain any spaces'
          '\n\t- File names contain a hyphen'
          '\n\t- File names contain the appropriate level of padding (3 or 8 digits)'
          '\n\t- File names are sequential'
          '\n\t- All files that are in the access directory are also present in the corresponding preservation directory,'
          ' and vice versa.')

    day = str(date.today())
    report_title = f'{day}_file_checker_report.txt'

    directories = []
    access_directory = ''
    pres_directory = ''
    report_location = ''
    directory = input('\nPlease enter the directory (e.g. /Volumes/digitize/project/QAqueue/session) in which your '
                      'files are stored: ')
    if sys.platform == 'win32':
        access_directory = f'{directory}\\access'
        directories.append(access_directory)
        pres_directory = f'{directory}\\preservation'
        directories.append(pres_directory)
        desktop_path = os.path.expanduser('~\\Desktop')
        report_location = f'{desktop_path}\\{report_title}'
    if sys.platform == 'darwin':
        access_directory = f'{directory}/access'
        directories.append(access_directory)
        pres_directory = f'{directory}/preservation'
        directories.append(pres_directory)
        desktop_path = os.path.expanduser('~/Desktop')
        report_location = f'{desktop_path}/{report_title}'

    outfile = open(report_location, 'a')
    make_report_header(directories, outfile)
    file_type, directories = run_file_type_check(directories)
    error_list = check_filenames(directories, file_type)
    for error in error_list:
        print(error, file=outfile)
    matching_errors = validate_files(access_directory, pres_directory,outfile)

    total_errors = len(error_list) + matching_errors

    print(f'{total_errors} discrepancies were discovered. Detailed report saved to {report_location}')
    outfile.close()


def make_report_header(directories, outfile):
    print('REPORT FOR THE FOLLOWING DIRECTORIES:', file=outfile)
    for directory in directories:
        print(f'\t{directory}', file=outfile)
    print(f'\n', file=outfile)
    

def run_file_type_check(directories):
    file_type = input('\nEnter file type ["A" for Archival or "C" for cataloged]: ')
    if file_type.casefold() != 'A'.casefold() and file_type.casefold() != 'C'.casefold():
        print(f'ERROR: Invalid file type. You entered {file_type}.')
        print('The program is ending. Please run it again with proper input.')
        exit()
    return file_type, directories


def check_filenames(directories, file_type):
    error_list = []

    for directory in directories:
        file_list = os.listdir(directory)
        file_tree = {}
        for file in file_list:
            if file != '.Ds_Store':
                filename, suffix = file.split(".")
                if suffix != 'tif' and suffix != 'tiff' and suffix != 'jp2':
                    error_list.append(f'{directory}/{file} is not a tif or jp2 file.')
                if ' ' in filename:
                    error_list.append(f'{file} in {directory} does not adhere to the correct naming convention (no spaces allowed).')
                if "-" in filename:
                    prefix, file_number = filename.split("-")
                    if str(prefix) not in file_tree.keys():
                        file_tree[str(prefix)] = [file_number]
                    else:
                        file_tree[prefix].append(file_number)
                    if file_type.casefold() == "A".casefold():
                        if len(file_number) != 3:
                            error_list.append(
                                f'{file} in {directory} does not adhere to the correct naming convention (3 '
                                f'digits after hyphen).')
                        try:
                            part1, part2, part3, part4 = prefix.split("_")
                            if len(part2) != 3:
                                error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                                  f'convention (3 digits for box number).')
                            if len(part3) != 3:
                                error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                                  f'convention (3 digits for folder number).')
                            if len(part4) != 3:
                                error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                                  f'convention (3 digits for item number).')
                        except ValueError:
                            try:
                                part1, part2, part3 = prefix.split("_")
                                error_list.append(f'WARNING: {file} in {directory} is missing one part of the '
                                                  f'conventional naming scheme (collection_box_folder_item-pad)')
                                if len(file_number) != 3:
                                    error_list.append(
                                        f'{file} in {directory} does not adhere to the correct naming convention (3 '
                                        f'digits after hyphen).')
                                if len(part2) != 3:
                                    error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                                      f'convention (3 digits for box number).')
                                if len(part3) != 3:
                                    error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                                      f'convention (3 digits for folder number).')
                            except ValueError:
                                error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                                  f'convention (collection_box_folder_item-pad)')
                    if file_type.casefold() == "C".casefold():
                        if len(file_number) != 8:
                            error_list.append(
                                f'{file} in {directory} does not adhere to the correct naming convention (8 '
                                f'digits after hyphen).')
                else:
                    error_list.append(f'{file} in {directory} does not adhere to the correct naming '
                                      f'conventions (missing hyphen).')
        sequence_errors = check_sequential(file_tree, directory)
        if sequence_errors:
            error_list.extend(sequence_errors)

    return error_list


def check_sequential(file_tree, directory):
    sequence_errors = []
    for prefix in file_tree:
        file_numbers = file_tree[prefix]
        numbers_only_list = []
        for file_number in file_numbers:
            stripped_file = str(file_number).lstrip('0')
            if stripped_file != '':
                numbers_only_list.append(int(stripped_file))
        numbers_only_list.sort()
        position_counter = 0
        for file in numbers_only_list:
            position_counter += 1
            if file != numbers_only_list[-1]:
                if (int(file) + 1) != int(numbers_only_list[position_counter]):
                    sequence_errors.append(
                        f'Files in the directory {directory} with the prefix {prefix} ending in {file} and '
                        f'{str(numbers_only_list[position_counter])} are not sequential.')
            else:
                pass
    return sequence_errors


def validate_files(access_directory, pres_directory, outfile):
    matching_errors = 0
    access_list = os.listdir(access_directory)
    access_list_trimmed = []
    for file in access_list:
        trimmed_file = file.split(".")[0]
        access_list_trimmed.append(trimmed_file)
    pres_list = os.listdir(pres_directory)
    pres_list_trimmed = []
    for file in pres_list:
        trimmed_file = file.split(".")[0]
        pres_list_trimmed.append(trimmed_file)

    pres_missing = list(filter(lambda x: x not in pres_list_trimmed, access_list_trimmed))
    access_missing = list(filter(lambda x: x not in access_list_trimmed, pres_list_trimmed))

    if pres_missing:
        matching_errors += len(pres_missing)
        print(f'\nThe following files are present in the access directory, but are not present in '
                               f'the preservation directory: ', file=outfile)
        for file in pres_missing:
            print(f'\t{file}', file=outfile)
    if access_missing:
        matching_errors += len(access_missing)
        print(f'The following files are present in the preservation directory, but are not present '
                               f'in the access directory: ', file=outfile)
        for file in access_missing:
            print(f'\t{file}',file=outfile)
    return matching_errors


if __name__ == '__main__':
    main()
