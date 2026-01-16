
#ifndef SYSTEM_CORE_H
#define SYSTEM_CORE_H

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
    #ifdef BUILDING_DLL
        #define DLL_EXPORT __declspec(dllexport)
    #else
        #define DLL_EXPORT __declspec(dllimport)
    #endif
#else
    #define DLL_EXPORT
#endif

/**
 * @brief Start system resource monitoring
 */
DLL_EXPORT void start_monitoring();

/**
 * @brief Stop system resource monitoring
 */
DLL_EXPORT void stop_monitoring();

/**
 * @brief Get current CPU usage percentage
 * @return CPU usage as double (0-100)
 */
DLL_EXPORT double get_cpu_usage();

/**
 * @brief Get current memory usage in MB
 * @return Memory usage in megabytes
 */
DLL_EXPORT double get_memory_usage();

/**
 * @brief Get list of active processes
 * @return Array of process names, terminated by NULL
 */
DLL_EXPORT char** get_active_processes();

/**
 * @brief Free memory allocated for process list
 * @param processes Array of process names
 */
DLL_EXPORT void free_process_list(char** processes);

/**
 * @brief Limit CPU usage for child processes
 * @param percentage Maximum CPU percentage (0-100)
 * @return 0 on success, -1 on error
 */
DLL_EXPORT int limit_cpu_usage(int percentage);

#ifdef __cplusplus
}
#endif

#endif // SYSTEM_CORE_H