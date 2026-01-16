
#include "system_core.h"
#include "process_monitor.h"
#include <memory>
#include <cstring>
#include <vector>

// Global monitor instance
static std::unique_ptr<ProcessMonitor> g_monitor = nullptr;

extern "C" {

DLL_EXPORT void start_monitoring() {
    if (!g_monitor) {
        g_monitor = std::make_unique<ProcessMonitor>();
        g_monitor->start();
    }
}

DLL_EXPORT void stop_monitoring() {
    if (g_monitor) {
        g_monitor->stop();
        g_monitor.reset();
    }
}

DLL_EXPORT double get_cpu_usage() {
    if (g_monitor) {
        return g_monitor->get_cpu_usage();
    }
    return 0.0;
}

DLL_EXPORT double get_memory_usage() {
    if (g_monitor) {
        return g_monitor->get_memory_usage();
    }
    return 0.0;
}

DLL_EXPORT char** get_active_processes() {
    if (!g_monitor) {
        return nullptr;
    }
    
    auto processes = g_monitor->get_active_processes();
    char** result = new char*[processes.size() + 1];
    
    for (size_t i = 0; i < processes.size(); ++i) {
        result[i] = new char[processes[i].size() + 1];
        strcpy(result[i], processes[i].c_str());
    }
    
    result[processes.size()] = nullptr;
    return result;
}

DLL_EXPORT void free_process_list(char** processes) {
    if (!processes) return;
    
    for (int i = 0; processes[i] != nullptr; ++i) {
        delete[] processes[i];
    }
    
    delete[] processes;
}

DLL_EXPORT int limit_cpu_usage(int percentage) {
    if (g_monitor) {
        return g_monitor->limit_cpu_usage(percentage) ? 0 : -1;
    }
    return -1;
}

} // extern "C"