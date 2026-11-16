#include <Python.h>
#import <Cocoa/Cocoa.h>

static int RunEmbedded(int argc, char *argv[]) {
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

int main(int argc, char *argv[]) {
    @autoreleasepool {
        if (argc == 5) {
            return RunEmbedded(argc, argv);
        }
        NSArray *arguments = [[NSBundle mainBundle] objectForInfoDictionaryKey:@"KitColdStartFixture"];
        if (![arguments isKindOfClass:[NSArray class]] || [arguments count] != 4) {
            return 64;
        }
        char *supplied[] = {
            argv[0], (char *)[arguments[0] UTF8String], (char *)[arguments[1] UTF8String],
            (char *)[arguments[2] UTF8String], (char *)[arguments[3] UTF8String], NULL
        };
        NSApplication *application = [NSApplication sharedApplication];
        [application setActivationPolicy:NSApplicationActivationPolicyAccessory];
        [application finishLaunching];
        return RunEmbedded(5, supplied);
    }
}
