#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <functional>
#include <memory>
#include <unordered_map>
#include <cmath>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <future>

#ifdef _WIN32
#include <windows.h>
#endif


class HardwareMonitor {
private:
    struct CoreMetrics {
        std::atomic<double> usage_percent{0};
        std::atomic<long long> execution_time_ns{0};
        std::atomic<int> task_count{0};
        std::atomic<bool> is_busy{false};
        std::chrono::steady_clock::time_point last_sample;
    };
    
    std::vector<std::unique_ptr<CoreMetrics>> cores_;
    std::atomic<size_t> total_ram_mb_{0};
    std::atomic<size_t> used_ram_mb_{0};
    std::atomic<size_t> cache_l1_{0};
    std::atomic<size_t> cache_l2_{0};
    std::atomic<size_t> cache_l3_{0};
    
public:
    HardwareMonitor() {
        unsigned int core_count = std::thread::hardware_concurrency();
        for (unsigned int i = 0; i < core_count; ++i) {
            cores_.push_back(std::make_unique<CoreMetrics>());
        }
        
        #ifdef _WIN32
        MEMORYSTATUSEX mem_status;
        mem_status.dwLength = sizeof(mem_status);
        GlobalMemoryStatusEx(&mem_status);
        total_ram_mb_ = mem_status.ullTotalPhys / (1024 * 1024);
        #endif
    }
    
    void SampleCoreUsage(int core_id) {
        if (core_id >= cores_.size()) return;
        
        auto now = std::chrono::steady_clock::now();
        auto& core = cores_[core_id];
        
        if (core->last_sample.time_since_epoch().count() != 0) {
            auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
                now - core->last_sample
            ).count();
            
            if (elapsed > 0) {
                double busy_time = core->execution_time_ns.load() / 1000.0;
                core->usage_percent = std::min(100.0, (busy_time / elapsed) * 100.0);
            }
        }
        
        core->last_sample = now;
        core->execution_time_ns = 0;
    }
    
    int GetOptimalCore() {
        int best_core = 0;
        double min_usage = 100.0;
        
        for (size_t i = 0; i < cores_.size(); ++i) {
            double usage = cores_[i]->usage_percent.load();
            if (usage < min_usage && !cores_[i]->is_busy.load()) {
                min_usage = usage;
                best_core = i;
            }
        }
        
        return best_core;
    }
};

enum class TaskPriority {
    CRITICAL = 0,
    HIGH = 1,
    NORMAL = 2,
    LOW = 3,
    BACKGROUND = 4
};

enum class TaskType {
    CPU_INTENSIVE,
    IO_INTENSIVE,
    MEMORY_INTENSIVE,
    MIXED
};

struct Task {
    int id;
    TaskPriority priority;
    TaskType type;
    std::function<void()> function;
    std::chrono::steady_clock::time_point enqueue_time;
    std::chrono::microseconds estimated_duration{0};
    size_t memory_requirement_mb{0};
    int affinity_core{-1};
    bool is_completed{false};
    
    bool operator<(const Task& other) const {
        return static_cast<int>(priority) > static_cast<int>(other.priority);
    }
};

class AdaptiveTaskScheduler {
private:
    std::vector<std::queue<Task>> priority_queues_;
    std::vector<std::thread> worker_threads_;
    std::atomic<bool> running_{true};
    std::mutex queue_mutex_;
    std::condition_variable cv_;
    std::unordered_map<int, std::chrono::steady_clock::time_point> task_execution_times_;
    HardwareMonitor& hardware_monitor_;
    
    struct PerformanceMetrics {
        std::atomic<long long> total_tasks_executed{0};
        std::atomic<double> avg_wait_time_ms{0};
        std::atomic<double> avg_execution_time_ms{0};
        std::atomic<double> throughput_per_second{0};
        std::chrono::steady_clock::time_point last_metrics_update;
    } metrics_;
    
public:
    AdaptiveTaskScheduler(HardwareMonitor& monitor) : hardware_monitor_(monitor) {
        priority_queues_.resize(5);
        
        unsigned int num_threads = std::thread::hardware_concurrency();
        for (unsigned int i = 0; i < num_threads; ++i) {
            worker_threads_.emplace_back(&AdaptiveTaskScheduler::WorkerLoop, this, i);
        }
        
        std::thread(&AdaptiveTaskScheduler::PerformanceOptimizer, this).detach();
    }
    
    ~AdaptiveTaskScheduler() {
        running_ = false;
        cv_.notify_all();
        for (auto& thread : worker_threads_) {
            if (thread.joinable()) thread.join();
        }
    }
    
    void SubmitTask(Task&& task) {
        task.enqueue_time = std::chrono::steady_clock::now();
        
        if (task.estimated_duration.count() == 0) {
            task.estimated_duration = EstimateTaskDuration(task.function);
        }
        
        {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            priority_queues_[static_cast<int>(task.priority)].push(std::move(task));
        }
        cv_.notify_one();
    }
    
private:
    void WorkerLoop(int thread_id) {
        while (running_) {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            
            cv_.wait(lock, [this] {
                for (const auto& queue : priority_queues_) {
                    if (!queue.empty()) return true;
                }
                return !running_;
            });
            
            Task task = GetNextTask();
            if (task.function) {
                lock.unlock();
                
                if (task.affinity_core >= 0) {
                    SetThreadAffinity(thread_id, task.affinity_core);
                }
                
                auto start = std::chrono::steady_clock::now();
                task.function();
                auto end = std::chrono::steady_clock::now();
                
                auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
                
                UpdateMetrics(start - task.enqueue_time, duration);
                
                lock.lock();
                task.is_completed = true;
            }
        }
    }
    
    Task GetNextTask() {
        for (int priority = 0; priority < 5; ++priority) {
            auto& queue = priority_queues_[priority];
            if (!queue.empty()) {
                Task task = std::move(queue.front());
                queue.pop();
                return task;
            }
        }
        return Task{};
    }
    
    std::chrono::microseconds EstimateTaskDuration(const std::function<void()>& func) {
        return std::chrono::microseconds(100);
    }
    
    void SetThreadAffinity(int thread_id, int core_id) {
        #ifdef __linux__
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(core_id, &cpuset);
        pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
        #endif
    }
    
    void UpdateMetrics(std::chrono::steady_clock::duration wait_time, 
                       std::chrono::milliseconds exec_time) {
        long long wait_ms = std::chrono::duration_cast<std::chrono::milliseconds>(wait_time).count();
        long long exec_ms = exec_time.count();
        
        long long total = metrics_.total_tasks_executed++;
        double alpha = 2.0 / (total + 1);
        
        double old_wait_avg = metrics_.avg_wait_time_ms;
        double old_exec_avg = metrics_.avg_execution_time_ms;
        
        metrics_.avg_wait_time_ms = old_wait_avg * (1 - alpha) + wait_ms * alpha;
        metrics_.avg_execution_time_ms = old_exec_avg * (1 - alpha) + exec_ms * alpha;
        
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - metrics_.last_metrics_update
        ).count();
        
        if (elapsed >= 1) {
            metrics_.throughput_per_second = total;
            metrics_.last_metrics_update = now;
        }
    }
    
    void PerformanceOptimizer() {
        while (running_) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            if (metrics_.avg_wait_time_ms > 100) {
                AdjustConcurrency(true);
            }
            
            if (metrics_.throughput_per_second < 10) {
                AdjustConcurrency(false);
            }
        }
    }
    
    void AdjustConcurrency(bool increase) {
        static int current_concurrency = std::thread::hardware_concurrency();
        
        if (increase && current_concurrency < std::thread::hardware_concurrency() * 2) {
            current_concurrency++;
            std::thread(&AdaptiveTaskScheduler::WorkerLoop, this, current_concurrency).detach();
        } else if (!increase && current_concurrency > 1) {
            current_concurrency--;
        }
    }
};


class MemoryManager {
private:
    struct MemoryBlock {
        void* ptr;
        size_t size;
        bool is_free;
        std::chrono::steady_clock::time_point allocation_time;
    };
    
    std::vector<MemoryBlock> blocks_;
    std::mutex memory_mutex_;
    size_t total_allocated_{0};
    size_t peak_usage_{0};
    std::unordered_map<std::string, std::vector<void*>> pool_cache_;
    
public:
    void* Allocate(size_t size, const std::string& pool = "") {
        std::lock_guard<std::mutex> lock(memory_mutex_);
        
        if (!pool.empty() && !pool_cache_[pool].empty()) {
            void* ptr = pool_cache_[pool].back();
            pool_cache_[pool].pop_back();
            return ptr;
        }
        
        size_t aligned_size = ((size + 63) / 64) * 64;
        
        void* ptr = malloc(aligned_size);
        if (ptr) {
            blocks_.push_back({ptr, aligned_size, false, std::chrono::steady_clock::now()});
            total_allocated_ += aligned_size;
            peak_usage_ = std::max(peak_usage_, total_allocated_);
        }
        
        return ptr;
    }
    
    void Deallocate(void* ptr, const std::string& pool = "") {
        std::lock_guard<std::mutex> lock(memory_mutex_);
        
        if (!pool.empty()) {
            pool_cache_[pool].push_back(ptr);
            return;
        }
        
        for (auto& block : blocks_) {
            if (block.ptr == ptr && !block.is_free) {
                block.is_free = true;
                total_allocated_ -= block.size;
                free(ptr);
                break;
            }
        }
        
        Defragment();
    }
    
private:
    void Defragment() {
        blocks_.erase(
            std::remove_if(blocks_.begin(), blocks_.end(),
                [](const MemoryBlock& block) { return block.is_free; }),
            blocks_.end()
        );
    }
};


template<typename K, typename V>
class AdaptiveCache {
private:
    struct CacheEntry {
        V value;
        std::chrono::steady_clock::time_point last_access;
        int access_count;
        size_t size_bytes;
    };
    
    std::unordered_map<K, CacheEntry> cache_;
    size_t max_size_bytes_;
    size_t current_size_{0};
    std::mutex cache_mutex_;
    
public:
    AdaptiveCache(size_t max_size) : max_size_bytes_(max_size) {}
    
    void Put(const K& key, const V& value, size_t size) {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        
        while (current_size_ + size > max_size_bytes_ && !cache_.empty()) {
            auto victim = SelectVictim();
            current_size_ -= victim->second.size_bytes;
            cache_.erase(victim);
        }
        
        cache_[key] = {value, std::chrono::steady_clock::now(), 1, size};
        current_size_ += size;
    }
    
    bool Get(const K& key, V& value) {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            it->second.last_access = std::chrono::steady_clock::now();
            it->second.access_count++;
            value = it->second.value;
            return true;
        }
        
        return false;
    }
    
private:
    auto SelectVictim() {
        return std::min_element(cache_.begin(), cache_.end(),
            [](const auto& a, const auto& b) {
                double score_a = static_cast<double>(a.second.access_count) /
                                std::chrono::duration_cast<std::chrono::seconds>(
                                    std::chrono::steady_clock::now() - a.second.last_access
                                ).count();
                double score_b = static_cast<double>(b.second.access_count) /
                                std::chrono::duration_cast<std::chrono::seconds>(
                                    std::chrono::steady_clock::now() - b.second.last_access
                                ).count();
                return score_a < score_b;
            });
    }
};


class ResourceMonitor {
private:
    HardwareMonitor hardware_;
    AdaptiveTaskScheduler scheduler_;
    MemoryManager memory_manager_;
    AdaptiveCache<std::string, std::string> cache_{1024 * 1024 * 100}; // 100MB cache
    
    std::atomic<bool> monitoring_{true};
    std::thread monitoring_thread_;
    
public:
    ResourceMonitor() : scheduler_(hardware_) {
        monitoring_thread_ = std::thread(&ResourceMonitor::MonitorLoop, this);
    }
    
    ~ResourceMonitor() {
        monitoring_ = false;
        if (monitoring_thread_.joinable()) {
            monitoring_thread_.join();
        }
    }
    
    void ProcessDataAsync(const std::string& input, std::function<void(std::string)> callback) {
        Task task;
        task.id = GenerateTaskId();
        task.priority = TaskPriority::NORMAL;
        task.type = TaskType::CPU_INTENSIVE;
        task.function = [this, input, callback]() {
            auto result = HeavyProcessing(input);
            callback(result);
        };
        task.affinity_core = hardware_.GetOptimalCore();
        
        scheduler_.SubmitTask(std::move(task));
    }
    
    std::string ProcessDataSync(const std::string& input) {
        return HeavyProcessing(input);
    }
    
    void OptimizePerformance() {
        std::vector<std::future<void>> optimizations;
        
        for (int i = 0; i < std::thread::hardware_concurrency(); ++i) {
            optimizations.push_back(std::async(std::launch::async, [this, i]() {
                OptimizeCore(i);
            }));
        }
        
        for (auto& opt : optimizations) {
            opt.wait();
        }
    }
    
private:
    std::string HeavyProcessing(const std::string& input) {
        std::string result;
        result.reserve(input.size() * 2);
        
        #pragma omp parallel for
        for (size_t i = 0; i < input.size(); ++i) {
            char processed = TransformCharacter(input[i]);
            #pragma omp critical
            result.push_back(processed);
        }
        
        result = ApplyComplexAlgorithm(result);
        result = OptimizeMemoryLayout(result);
        
        return result;
    }
    
    char TransformCharacter(char c) {
        if (c >= 'a' && c <= 'z') {
            return ((c - 'a' + 13) % 26) + 'a';
        } else if (c >= 'A' && c <= 'Z') {
            return ((c - 'A' + 13) % 26) + 'A';
        }
        return c;
    }
    
    std::string ApplyComplexAlgorithm(const std::string& input) {
        std::string output = input;
        
        for (size_t i = 0; i < output.size(); ++i) {
            output[i] ^= 0x55;
            output[i] = (output[i] << 1) | ((output[i] >> 7) & 1);
        }
        
        return output;
    }
    
    std::string OptimizeMemoryLayout(const std::string& input) {
        std::string optimized;
        optimized.resize(input.size());
        
        const size_t BLOCK_SIZE = 64;
        for (size_t block = 0; block < input.size(); block += BLOCK_SIZE) {
            size_t end = std::min(block + BLOCK_SIZE, input.size());
            for (size_t i = block; i < end; ++i) {
                optimized[i] = input[block + (end - 1 - (i - block))];
            }
        }
        
        return optimized;
    }
    
    void MonitorLoop() {
        while (monitoring_) {
            for (size_t i = 0; i < std::thread::hardware_concurrency(); ++i) {
                hardware_.SampleCoreUsage(i);
            }
            
            if (ShouldOptimize()) {
                OptimizePerformance();
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
    
    bool ShouldOptimize() {
        static std::chrono::steady_clock::time_point last_optimization = std::chrono::steady_clock::now();
        auto now = std::chrono::steady_clock::now();
        
        if (std::chrono::duration_cast<std::chrono::seconds>(now - last_optimization).count() > 5) {
            last_optimization = now;
            return true;
        }
        
        return false;
    }
    
    void OptimizeCore(int core_id) {
        std::this_thread::sleep_for(std::chrono::microseconds(100));
        #ifdef __linux__
        struct sched_param param;
        param.sched_priority = sched_get_priority_max(SCHED_FIFO) / 2;
        pthread_setschedparam(pthread_self(), SCHED_FIFO, &param);
        #endif
    }
    
    int GenerateTaskId() {
        static std::atomic<int> counter{0};
        return counter++;
    }
};


class UltraPerformanceSystem {
private:
    std::unique_ptr<ResourceMonitor> monitor_;
    std::unique_ptr<MemoryManager> memory_manager_;
    
public:
    UltraPerformanceSystem() {
        monitor_ = std::make_unique<ResourceMonitor>();
        memory_manager_ = std::make_unique<MemoryManager>();
        
        InitializeHighPerformanceMode();
    }
    
    std::string ProcessData(const std::string& input) {
        auto* buffer = static_cast<char*>(memory_manager_->Allocate(input.size() + 1, "processing"));
        memcpy(buffer, input.c_str(), input.size());
        buffer[input.size()] = '\0';
        
        std::string result = monitor_->ProcessDataSync(buffer);
        
        memory_manager_->Deallocate(buffer, "processing");
        return result;
    }
    
    void ProcessDataAsync(const std::string& input, std::function<void(std::string)> callback) {
        monitor_->ProcessDataAsync(input, callback);
    }
    
private:
    void InitializeHighPerformanceMode() {
        #ifdef _WIN32
        SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS);
        #elif defined(__linux__)
        nice(-20);
        #endif
        
        #ifdef __linux__
        mlockall(MCL_CURRENT | MCL_FUTURE);
        #endif
    }
};


int main() {
    UltraPerformanceSystem system;
    
    std::string result = system.ProcessData("Hello World");
    
    system.ProcessDataAsync("Complex data", [](std::string result) {
    });
    
    return 0;
}