import subprocess
import sys

class BatchUtilites(object):

    @staticmethod
    def runBatchProcess(python_file, args):
        """
            Run Blender in a headless/background state. Passing in a python file to run and custom args.

        :param python_file: Path to python file to run when blender loads"
        :type python_file: str
        :param args: list of custom args seperated out e.g ["-renderWidth", "1024", "-rh", "1024"]
        :type args: list
        """

        BlENDER_EXE = "C:\\Program Files\\Blender Foundation\\Blender 3.3\\blender.exe"

        args = [
            BlENDER_EXE,
            "--background",
            "--python",
            python_file,
            "--"
        ] + args

        subprocess.run(args)
