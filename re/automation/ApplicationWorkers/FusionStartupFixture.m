#include <Python.h>

int main(int argc, char *argv[]) {
    if (argc != 5) {
        return 64;
    }
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.install_signal_handlers = 0;
    config.site_import = 0;
    config.write_bytecode = 0;
    config.parse_argv = 0;
    PyStatus status = PyConfig_SetBytesString(&config, &config.home, argv[1]);
    if (!PyStatus_Exception(status)) {
        status = PyConfig_SetBytesArgv(&config, argc - 2, argv + 2);
    }
    if (!PyStatus_Exception(status)) {
        status = PyConfig_SetBytesString(&config, &config.run_filename, argv[2]);
    }
    if (!PyStatus_Exception(status)) {
        status = Py_InitializeFromConfig(&config);
    }
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) {
        Py_ExitStatusException(status);
    }
    return Py_RunMain();
}
