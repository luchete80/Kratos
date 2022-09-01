# STD imports
import sys
from pathlib import Path
from importlib import import_module
import shutil
import subprocess

# External imports
try:
    from mypy.stubgen import parse_options, generate_stubs
except ImportError:
    print("Please install mypy using  \"pip install mypy\" to generate pyi stub files for libraries generated by pybind11.")
    exit(0)


def __AddSubmodules(output_path: Path):
    if output_path.is_dir():
        with open(str(output_path / "__init__.pyi"), "a") as file_output:
            file_output.write("\n\n#   ---- start of includes of sub modules --- \n\n")

            for cpp_sub_module_path in output_path.iterdir():
                if cpp_sub_module_path.is_dir():
                    cpp_sub_module_name = str(cpp_sub_module_path.relative_to(cpp_sub_module_path.parent))
                else:
                    cpp_sub_module_name = str(cpp_sub_module_path.relative_to(cpp_sub_module_path.parent))[:-4]
                if cpp_sub_module_name != "__init__":
                    file_output.write("from . import {:s}\n".format(cpp_sub_module_name))

            file_output.write("\n#   ---- end of includes of sub modules --- \n\n")

        for cpp_sub_module_path in output_path.iterdir():
            __AddSubmodules(cpp_sub_module_path)


def __FindCPPModuleImportsInPythonModules(current_path: Path, cpp_module_names_list: "list[str]", cpp_python_modules_dict: "dict[str, Path]") -> None:

    if len(cpp_module_names_list) != 0:
        for sub_path in current_path.iterdir():
            if sub_path.is_file() and str(sub_path).endswith(".py"):
                with open(str(sub_path), "r") as file_input:
                    data = file_input.read()

                data = data.replace(" ", "")
                for i, cpp_module_name in enumerate(cpp_module_names_list):
                    if "\nfrom{:s}import*".format(cpp_module_name) in data:
                        cpp_python_modules_dict[cpp_module_name] = sub_path
                        print(f"--- Found {cpp_module_name} binary module include in {str(sub_path)}.")
                        del cpp_module_names_list[i]
                        break

        for sub_path in current_path.iterdir():
            if sub_path.is_dir():
                __FindCPPModuleImportsInPythonModules(sub_path, cpp_module_names_list, cpp_python_modules_dict)


def __GetPythonModulesImportingCppModules(kratos_python_module_path: Path, kratos_library_path: Path) -> "dict[Path, Path]":

    # generate list of cpp modules
    list_of_binary_modules = []
    for custom_library_path in kratos_library_path.iterdir():
        custom_library_name = custom_library_path.name

        cpython_location = custom_library_name.find(".cpython")
        if cpython_location != -1:
            custom_library_name = custom_library_name[:cpython_location]
            list_of_binary_modules.append(custom_library_name)

    cpp_python_modules_dict = {}
    copy_list_of_binary_modules = list(list_of_binary_modules)
    __FindCPPModuleImportsInPythonModules(kratos_python_module_path, list_of_binary_modules, cpp_python_modules_dict)

    if len(list_of_binary_modules) != 0:
        print("------ Warning: Could not find imports within python modules for following binaries:")
        print("                    " + "\n                    ".join(list_of_binary_modules))

    return copy_list_of_binary_modules, cpp_python_modules_dict

def __GenerateStubFilesForModule(
        kratos_python_module_path: Path,
        kratos_library_path: Path,
        output_path: Path,
        cpp_module_name: str,
        python_import_module_path_dict: "dict[str, Path]") -> None:


    def __generate(output_path: Path, cpp_module_name: str, custom_args: "list[str]"):

        args = ["-o", str(output_path.absolute())]
        args.extend(custom_args)
        args.append(cpp_module_name)
        options = parse_options(args)
        generate_stubs(options)

    def __append_cpp_module_stub(cpp_module_file_path: Path, python_module_file_path: Path):
        # read python module stub file
        with open(str(python_module_file_path), "r") as file_input:
            data = file_input.read()
        # now delete the python module stub file
        shutil.rmtree(str(python_module_file_path.parent.absolute()))

        # now append cpp module stub file
        with open(str(cpp_module_file_path), "a") as file_output:
            file_output.write("\n\n#   ---- start of includes of python modules --- \n\n")
            file_output.write(data)
            file_output.write("\n#   ---- end of includes of python modules --- \n\n")

    __generate(output_path, cpp_module_name, ["-p"])

    # if sub modules are found, include them in the __init__.pyi
    submodule_path = kratos_library_path / cpp_module_name
    __AddSubmodules(submodule_path)

    # now add appropriate python module hints
    if cpp_module_name in python_import_module_path_dict.keys():
        python_import_module_path = python_import_module_path_dict[cpp_module_name]
        if str(python_import_module_path).endswith("__init__.py"):
            found_package = True
            kratos_full_module_name = str(python_import_module_path.parent.relative_to(kratos_python_module_path)).replace("/", ".")
        else:
            found_package = False
            kratos_full_module_name = str(python_import_module_path.relative_to(kratos_python_module_path)).replace("/", ".")[:-3]

        if (kratos_full_module_name == "."):
            kratos_full_module_name = "KratosMultiphysics"
        else:
            kratos_full_module_name = "KratosMultiphysics." + kratos_full_module_name
        __generate(output_path, kratos_full_module_name, ["--parse-only", "--export-less", "-m"])

        cpp_module_path = output_path / cpp_module_name
        if cpp_module_path.is_dir():
            __append_cpp_module_stub(cpp_module_path / "__init__.pyi", (output_path / kratos_full_module_name.replace(".", "/")) / "__init__.pyi")
            # now move the directory to appropriate python module path
            shutil.copytree(str(cpp_module_path), str(python_import_module_path.parent), dirs_exist_ok=True)
            # delete it from output path
            shutil.rmtree(str(cpp_module_path))
            print(f"-- Moved {str(cpp_module_path)} package and its submodules to {str(python_import_module_path.parent)}")

        else:
            cpp_module_path = output_path / (cpp_module_name + ".pyi")
            if cpp_module_path.is_file():
                if found_package:
                    __append_cpp_module_stub(cpp_module_path, (output_path / kratos_full_module_name.replace(".", "/")) / "__init__.pyi")
                    shutil.move(str(cpp_module_path), str(python_import_module_path.parent / "__init__.pyi"))
                    print(f"-- Moved {str(cpp_module_path)} package to {str(python_import_module_path.parent)}")
                else:
                    __append_cpp_module_stub(cpp_module_path, output_path / (kratos_full_module_name.replace(".", "/") + ".pyi"))
                    stub_file_name = str(python_import_module_path.parent / str(python_import_module_path.relative_to(python_import_module_path.parent)))[:-2] + "pyi"
                    shutil.move(str(cpp_module_path), stub_file_name)
                    print(f"-- Moved {str(cpp_module_path)} module to {stub_file_name}")
    else:
        print(f"------ Warning: No python import module found for binary module {cpp_module_name}. Python hints may not be working for this binary.")

    return cpp_module_name


def Main():
    print("--- Generating python stub files from {:s}".format(sys.argv[1]))
    kratos_installation_path = (Path(sys.argv[1])).absolute()
    kratos_library_path = (kratos_installation_path / "libs").absolute()
    kratos_python_module_path = kratos_installation_path / "KratosMultiphysics"

    sys.path.insert(0, str(kratos_installation_path.absolute()))
    sys.path.insert(0, str(kratos_library_path.absolute()))

    list_of_cpp_libs = []

    # first look for cpp module imports in python modules
    available_cpp_libs, cpp_python_modules_dict = __GetPythonModulesImportingCppModules(kratos_python_module_path, kratos_library_path)

    if len(available_cpp_libs) > 0:
        # generate Kratos core cpp stubs files
        import_module("KratosMultiphysics")
        list_of_cpp_libs.append(__GenerateStubFilesForModule(kratos_python_module_path, kratos_library_path, kratos_library_path, "Kratos", cpp_python_modules_dict))

        # Collect Kratos applications
        from KratosMultiphysics.kratos_utilities import GetListOfAvailableApplications
        list_of_available_applications = GetListOfAvailableApplications()

        # Generate stubs for all installed applications
        for application_name in list_of_available_applications:
            # Import the application
            import_module("KratosMultiphysics." + application_name)
            application_lib_name = "Kratos" + application_name

            # Generate stubs to temporary directory
            list_of_cpp_libs.append(__GenerateStubFilesForModule(kratos_python_module_path, kratos_library_path, kratos_library_path, application_lib_name, cpp_python_modules_dict))

        # now iterate through auxiliary libraries and generate stub files
        for custom_library_path in kratos_library_path.iterdir():
            if custom_library_path.is_file():
                custom_library_name = str(custom_library_path.relative_to(custom_library_path.parent))
                cpython_location = custom_library_name.find(".cpython")
                if cpython_location != -1:
                    custom_library_name = custom_library_name[:cpython_location]
                    if custom_library_name not in list_of_cpp_libs:
                        list_of_cpp_libs.append(__GenerateStubFilesForModule(kratos_python_module_path, kratos_library_path, kratos_library_path, custom_library_name, cpp_python_modules_dict))

        # now check for the empty dir in libs
        if (kratos_library_path / "KratosMultiphysics").is_dir():
            shutil.rmtree(str(kratos_library_path / "KratosMultiphysics"))

if __name__ == "__main__":
    if "--quiet" in sys.argv: # suppress output from Kratos imports
        args = [arg for arg in sys.argv if arg != "--quiet"]
        subprocess.run([sys.executable] + args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    else:
        Main()