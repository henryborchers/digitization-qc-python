from typing import List, Mapping, Sequence, Any

import speedwagon
from speedwagon.job import _T
from speedwagon import workflow
from speedwagon.tasks import Result, TaskBuilder
from . import file_checker

@speedwagon.hookimpl
def registered_workflows():
    return {"File Checker" : FileCheckerWorkflow}


class FileCheckerWorkflow(speedwagon.Workflow):
    name = "File Checker"

    def job_options(self):
        file_type = workflow.ChoiceSelection("File Type", required=True)
        file_type.add_selection("Archival")
        file_type.add_selection("Cataloged")
        return [
            speedwagon.workflow.DirectorySelect("Input Directory", required=True),
            file_type
        ]

    def discover_task_metadata(
            self,
            initial_results: List[Result],
            additional_data: Mapping[str, Any],
            user_args: _T,
    ) -> Sequence[Mapping[str, object]]:
        access_directory, directories, pres_directory, report_location = file_checker.get_directories(user_args["Input Directory"])
        print(user_args)
        return [
            {
                "access_directory": access_directory,
                "directories": directories,
                "pres_directory": pres_directory,
                "report_location": report_location,
                "file_type": user_args["File Type"]
            }
        ]

    def create_new_task(self, task_builder: TaskBuilder, job_args) -> None:
        task_builder.add_subtask(
            FileCheckerTask(
                access_directory=job_args["access_directory"],
                pres_directory=job_args["pres_directory"],
                directories=job_args["directories"],
                report_location=job_args["report_location"],
                file_type=job_args["file_type"],
            )
        )

class FileCheckerTask(speedwagon.tasks.Subtask[None]):
    name = "File Checker Task"

    def __init__(self, access_directory: str, directories: List[str], pres_directory: str, report_location: str, file_type: str):
        super().__init__()
        self.access_directory = access_directory
        self.directories = directories
        self.pres_directory = pres_directory
        self.report_location = report_location
        self.file_type = file_type

    def task_description(self) -> str:
        return f"Checking files in {self.access_directory} and {self.pres_directory}"

    def work(self) -> bool:
        with open(self.report_location, 'a') as outfile:
            file_checker.make_report_header(self.directories, outfile)

            for directory in self.directories:
                outfile.write(f'\nREPORT FOR {directory}')
                error_list = file_checker.check_filenames(directory, self.file_type)
                for error in error_list:
                    outfile.write(f'\n{error}')

            access_list_trimmed, pres_list_trimmed = file_checker.make_file_number_lists(self.access_directory, self.pres_directory)
            matching_error_list = file_checker.validate_files(access_list_trimmed, pres_list_trimmed)

            for error in matching_error_list:
                outfile.write(f'\n{error}')

            total_errors = len(error_list) + len(matching_error_list)

            self.log(f'{total_errors} discrepancies were discovered. Detailed report saved to {self.report_location}')
        return True