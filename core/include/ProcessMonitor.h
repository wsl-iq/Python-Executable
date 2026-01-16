#ifndef PROCESS_MONITOR_H
#define PROCESS_MONITOR_H

#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>

class ProcessMonitor {
public:
    ProcessMonitor();
    ~ProcessMonitor();
    
    void start();
    void stop();
    
    double get_cpu_usage() const;
    double get_memory_usage() const;
    std::vector<std::string> get_active_processes() const;
    bool limit_cpu_usage(int percentage);
    
private:
    void monitoring_thread();
    void update_system_stats();
    
    std::atomic<bool> running_;
    std::thread monitor_thread_;
    mutable std::mutex data_mutex_;
    
    double cpu_usage_;
    double memory_usage_mb_;
    std::vector<std::string> active_processes_;
    
    // Platform-specific implementations
    void update_stats_windows();
    void update_stats_linux();
    void update_stats_macos();
    
    std::vector<std::string> get_processes_windows() const;
    std::vector<std::string> get_processes_linux() const;
    std::vector<std::string> get_processes_macos() const;
    
    // CPU limiting
    bool set_cpu_limit_windows(int percentage);
    bool set_cpu_limit_linux(int percentage);
    bool set_cpu_limit_macos(int percentage);
};

#endif // PROCESS_MONITOR_H