#include "process_monitor.h"
#include <chrono>
#include <algorithm>
#include <fstream>
#include <sstream>

#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <processthreadsapi.h>
#else
#include <sys/types.h>
#include <sys/sysinfo.h>
#include <sys/resource.h>
#include <unistd.h>
#include <dirent.h>
#include <cstdio>
#include <cstring>
#endif

using namespace std::chrono_literals;

ProcessMonitor::ProcessMonitor() 
    : running_(false)
    , cpu_usage_(0.0)
    , memory_usage_mb_(0.0) {
}

ProcessMonitor::~ProcessMonitor() {
    stop();
}

void ProcessMonitor::start() {
    if (!running_) {
        running_ = true;
        monitor_thread_ = std::thread(&ProcessMonitor::monitoring_thread, this);
    }
}

void ProcessMonitor::stop() {
    running_ = false;
    if (monitor_thread_.joinable()) {
        monitor_thread_.join();
    }
}

void ProcessMonitor::monitoring_thread() {
    while (running_) {
        update_system_stats();
        std::this_thread::sleep_for(1s);
    }
}

void ProcessMonitor::update_system_stats() {
    std::lock_guard<std::mutex> lock(data_mutex_);
    
#ifdef _WIN32
    update_stats_windows();
#elif defined(__APPLE__)
    update_stats_macos();
#else
    update_stats_linux();
#endif
}

double ProcessMonitor::get_cpu_usage() const {
    std::lock_guard<std::mutex> lock(data_mutex_);
    return cpu_usage_;
}

double ProcessMonitor::get_memory_usage() const {
    std::lock_guard<std::mutex> lock(data_mutex_);
    return memory_usage_mb_;
}

std::vector<std::string> ProcessMonitor::get_active_processes() const {
    std::lock_guard<std::mutex> lock(data_mutex_);
    return active_processes_;
}

bool ProcessMonitor::limit_cpu_usage(int percentage) {
#ifdef _WIN32
    return set_cpu_limit_windows(percentage);
#elif defined(__APPLE__)
    return set_cpu_limit_macos(percentage);
#else
    return set_cpu_limit_linux(percentage);
#endif
}

// Windows Implementation
#ifdef _WIN32

static ULARGE_INTEGER last_cpu_total = {0};
static ULARGE_INTEGER last_cpu_idle = {0};

void ProcessMonitor::update_stats_windows() {
    // CPU Usage
    FILETIME idle_time, kernel_time, user_time;
    if (GetSystemTimes(&idle_time, &kernel_time, &user_time)) {
        ULARGE_INTEGER idle, kernel, user;
        idle.LowPart = idle_time.dwLowDateTime;
        idle.HighPart = idle_time.dwHighDateTime;
        kernel.LowPart = kernel_time.dwLowDateTime;
        kernel.HighPart = kernel_time.dwHighDateTime;
        user.LowPart = user_time.dwLowDateTime;
        user.HighPart = user_time.dwHighDateTime;
        
        ULARGE_INTEGER total = {kernel.QuadPart + user.QuadPart};
        
        if (last_cpu_total.QuadPart != 0) {
            ULONGLONG total_diff = total.QuadPart - last_cpu_total.QuadPart;
            ULONGLONG idle_diff = idle.QuadPart - last_cpu_idle.QuadPart;
            
            if (total_diff > 0) {
                cpu_usage_ = 100.0 * (total_diff - idle_diff) / total_diff;
            }
        }
        
        last_cpu_total = total;
        last_cpu_idle = idle;
    }
    
    // Memory Usage
    MEMORYSTATUSEX mem_info;
    mem_info.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&mem_info)) {
        DWORDLONG used_memory = mem_info.ullTotalPhys - mem_info.ullAvailPhys;
        memory_usage_mb_ = used_memory / (1024.0 * 1024.0);
    }
    
    // Active Processes
    active_processes_ = get_processes_windows();
}

std::vector<std::string> ProcessMonitor::get_processes_windows() const {
    std::vector<std::string> processes;
    
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot != INVALID_HANDLE_VALUE) {
        PROCESSENTRY32 process_entry;
        process_entry.dwSize = sizeof(PROCESSENTRY32);
        
        if (Process32First(snapshot, &process_entry)) {
            do {
                processes.push_back(process_entry.szExeFile);
            } while (Process32Next(snapshot, &process_entry));
        }
        
        CloseHandle(snapshot);
    }
    
    return processes;
}

bool ProcessMonitor::set_cpu_limit_windows(int percentage) {
    // Windows CPU limiting requires job objects
    // This is a simplified implementation
    HANDLE job = CreateJobObject(NULL, NULL);
    if (job) {
        JOBOBJECT_CPU_RATE_CONTROL_INFORMATION cpu_limit;
        cpu_limit.ControlFlags = JOB_OBJECT_CPU_RATE_CONTROL_ENABLE | 
                                JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP;
        cpu_limit.CpuRate = percentage * 100; // Convert to units of 0.01%
        
        if (SetInformationJobObject(job, 
            JobObjectCpuRateControlInformation, 
            &cpu_limit, 
            sizeof(cpu_limit))) {
            CloseHandle(job);
            return true;
        }
        CloseHandle(job);
    }
    return false;
}

#elif defined(__APPLE__)
// macOS Implementation
void ProcessMonitor::update_stats_macos() {
    // For macOS, use system calls or parse /proc/stat
    // This is a simplified placeholder
    cpu_usage_ = 0.0;
    memory_usage_mb_ = 0.0;
    
    // Parse /proc/stat for CPU (if available on macOS)
    std::ifstream stat_file("/proc/stat");
    if (stat_file.is_open()) {
        std::string line;
        std::getline(stat_file, line);
        std::istringstream iss(line);
        std::string cpu_label;
        long user, nice, system, idle;
        iss >> cpu_label >> user >> nice >> system >> idle;
        
        static long prev_total = 0, prev_idle = 0;
        long total = user + nice + system + idle;
        
        if (prev_total != 0) {
            long total_diff = total - prev_total;
            long idle_diff = idle - prev_idle;
            
            if (total_diff > 0) {
                cpu_usage_ = 100.0 * (total_diff - idle_diff) / total_diff;
            }
        }
        
        prev_total = total;
        prev_idle = idle;
    }
    
    // Get memory usage
    std::ifstream meminfo("/proc/meminfo");
    if (meminfo.is_open()) {
        long total_mem = 0, free_mem = 0;
        std::string line;
        
        while (std::getline(meminfo, line)) {
            if (line.find("MemTotal:") == 0) {
                std::istringstream(line.substr(9)) >> total_mem;
            } else if (line.find("MemFree:") == 0) {
                std::istringstream(line.substr(8)) >> free_mem;
            }
        }
        
        if (total_mem > 0) {
            memory_usage_mb_ = (total_mem - free_mem) / 1024.0;
        }
    }
    
    active_processes_ = get_processes_macos();
}

std::vector<std::string> ProcessMonitor::get_processes_macos() const {
    std::vector<std::string> processes;
    
    // Use ps command on macOS
    FILE* pipe = popen("ps -A -o comm=", "r");
    if (pipe) {
        char buffer[256];
        while (fgets(buffer, sizeof(buffer), pipe)) {
            std::string process(buffer);
            process.erase(process.find_last_not_of(" \n\r\t") + 1);
            if (!process.empty()) {
                processes.push_back(process);
            }
        }
        pclose(pipe);
    }
    
    return processes;
}

bool ProcessMonitor::set_cpu_limit_macos(int percentage) {
    // macOS CPU limiting using setrlimit
    rlimit limit;
    limit.rlim_cur = (percentage * 1000000) / 100; // Convert to microseconds
    limit.rlim_max = RLIM_INFINITY;
    
    return setrlimit(RLIMIT_CPU, &limit) == 0;
}

#else
// Linux Implementation
void ProcessMonitor::update_stats_linux() {
    // CPU Usage
    std::ifstream stat_file("/proc/stat");
    if (stat_file.is_open()) {
        std::string line;
        std::getline(stat_file, line);
        std::istringstream iss(line);
        std::string cpu_label;
        long user, nice, system, idle, iowait, irq, softirq;
        iss >> cpu_label >> user >> nice >> system >> idle >> iowait >> irq >> softirq;
        
        static long prev_total = 0, prev_idle = 0;
        long total = user + nice + system + idle + iowait + irq + softirq;
        
        if (prev_total != 0) {
            long total_diff = total - prev_total;
            long idle_diff = idle - prev_idle;
            
            if (total_diff > 0) {
                cpu_usage_ = 100.0 * (total_diff - idle_diff) / total_diff;
            }
        }
        
        prev_total = total;
        prev_idle = idle;
    }
    
    // Memory Usage
    std::ifstream meminfo("/proc/meminfo");
    if (meminfo.is_open()) {
        long total_mem = 0, free_mem = 0, buffers = 0, cached = 0;
        std::string line;
        
        while (std::getline(meminfo, line)) {
            if (line.find("MemTotal:") == 0) {
                std::istringstream(line.substr(9)) >> total_mem;
            } else if (line.find("MemFree:") == 0) {
                std::istringstream(line.substr(8)) >> free_mem;
            } else if (line.find("Buffers:") == 0) {
                std::istringstream(line.substr(8)) >> buffers;
            } else if (line.find("Cached:") == 0) {
                std::istringstream(line.substr(7)) >> cached;
            }
        }
        
        if (total_mem > 0) {
            long used_mem = total_mem - free_mem - buffers - cached;
            memory_usage_mb_ = used_mem / 1024.0;
        }
    }
    
    active_processes_ = get_processes_linux();
}

std::vector<std::string> ProcessMonitor::get_processes_linux() const {
    std::vector<std::string> processes;
    
    DIR* dir = opendir("/proc");
    if (dir) {
        struct dirent* entry;
        while ((entry = readdir(dir)) != nullptr) {
            // Check if directory name is a number (PID)
            if (isdigit(entry->d_name[0])) {
                std::string cmdline_path = std::string("/proc/") + entry->d_name + "/cmdline";
                std::ifstream cmdline(cmdline_path);
                if (cmdline.is_open()) {
                    std::string process_name;
                    std::getline(cmdline, process_name);
                    if (!process_name.empty()) {
                        // Extract basename
                        size_t pos = process_name.find_last_of('/');
                        if (pos != std::string::npos) {
                            process_name = process_name.substr(pos + 1);
                        }
                        processes.push_back(process_name);
                    }
                }
            }
        }
        closedir(dir);
    }
    
    return processes;
}

bool ProcessMonitor::set_cpu_limit_linux(int percentage) {
    // Linux CPU limiting using setrlimit
    rlimit limit;
    limit.rlim_cur = (percentage * 1000000) / 100; // Convert to microseconds
    limit.rlim_max = RLIM_INFINITY;
    
    return setrlimit(RLIMIT_CPU, &limit) == 0;
}

#endif