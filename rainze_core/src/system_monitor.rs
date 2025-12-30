//! 系统监控模块 / System Monitor Module
//!
//! 提供 CPU、内存使用率监控以及全屏/会议应用检测。
//! Provides CPU, memory usage monitoring and fullscreen/meeting app detection.
//!
//! # Example / 示例
//!
//! ```python
//! from rainze_core import SystemMonitor
//!
//! monitor = SystemMonitor()
//! print(f"CPU Usage: {monitor.get_cpu_usage():.1f}%")
//! print(f"Memory Usage: {monitor.get_memory_usage():.1f}%")
//! print(f"Is Fullscreen: {monitor.is_fullscreen()}")
//! ```
//!
//! # Reference / 参考
//!
//! - PRD §0.7a: 主动行为触发条件
//! - MOD-RustCore.md §4.2: SystemMonitor

use pyo3::prelude::*;
use sysinfo::System;
use std::sync::Mutex;

/// 系统监控器
/// System Monitor
///
/// 监控系统资源使用情况，支持全屏和会议应用检测。
/// Monitors system resource usage, supports fullscreen and meeting app detection.
///
/// # Thread Safety / 线程安全
///
/// 内部使用 Mutex 保护状态，可安全跨线程使用。
/// Uses internal Mutex for state protection, safe for cross-thread usage.
#[pyclass]
pub struct SystemMonitor {
    /// sysinfo 系统实例 / sysinfo System instance
    system: Mutex<System>,
}

#[pymethods]
impl SystemMonitor {
    /// 创建新的系统监控器实例
    /// Creates a new system monitor instance
    #[new]
    pub fn new() -> Self {
        Self {
            system: Mutex::new(System::new_all()),
        }
    }

    /// 获取 CPU 使用率 (0.0-100.0)
    /// Get CPU usage percentage (0.0-100.0)
    ///
    /// # Returns / 返回
    ///
    /// CPU 使用百分比 / CPU usage percentage
    pub fn get_cpu_usage(&self) -> f32 {
        let mut sys = self.system.lock().unwrap();
        sys.refresh_cpu_usage();
        sys.global_cpu_usage()
    }

    /// 获取内存使用率 (0.0-100.0)
    /// Get memory usage percentage (0.0-100.0)
    ///
    /// # Returns / 返回
    ///
    /// 内存使用百分比 / Memory usage percentage
    pub fn get_memory_usage(&self) -> f32 {
        let mut sys = self.system.lock().unwrap();
        sys.refresh_memory();
        let total = sys.total_memory() as f32;
        let used = sys.used_memory() as f32;
        if total > 0.0 {
            (used / total) * 100.0
        } else {
            0.0
        }
    }

    /// 检测是否有全屏应用运行
    /// Detect if any fullscreen application is running
    ///
    /// # Returns / 返回
    ///
    /// true 表示有全屏应用 / true if fullscreen app is detected
    ///
    /// # Note / 注意
    ///
    /// 当前为占位实现，完整实现需要 Windows API。
    /// Current placeholder implementation, full implementation requires Windows API.
    pub fn is_fullscreen(&self) -> bool {
        // TODO: 实现 Windows 全屏检测 / Implement Windows fullscreen detection
        // 使用 GetForegroundWindow + GetWindowRect 比较屏幕尺寸
        // Use GetForegroundWindow + GetWindowRect to compare with screen size
        false
    }

    /// 检测是否有会议应用运行
    /// Detect if any meeting application is running
    ///
    /// # Returns / 返回
    ///
    /// true 表示检测到会议应用 / true if meeting app is detected
    ///
    /// # Detected Apps / 检测的应用
    ///
    /// - Zoom
    /// - Microsoft Teams
    /// - Tencent Meeting (腾讯会议)
    /// - DingTalk (钉钉)
    /// - Feishu (飞书)
    pub fn is_meeting_app(&self) -> bool {
        let mut sys = self.system.lock().unwrap();
        sys.refresh_processes(sysinfo::ProcessesToUpdate::All, true);

        // 会议应用进程名列表 / Meeting app process names
        let meeting_apps = [
            "zoom",
            "teams",
            "wemeetapp",      // 腾讯会议 / Tencent Meeting
            "dingtalk",       // 钉钉 / DingTalk
            "feishu",         // 飞书 / Feishu
            "webex",
            "slack",
        ];

        for process in sys.processes().values() {
            let name = process.name().to_string_lossy().to_lowercase();
            for app in &meeting_apps {
                if name.contains(app) {
                    return true;
                }
            }
        }
        false
    }

    /// 刷新所有系统信息
    /// Refresh all system information
    pub fn refresh(&self) {
        let mut sys = self.system.lock().unwrap();
        sys.refresh_all();
    }
}

impl Default for SystemMonitor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cpu_usage_range() {
        let monitor = SystemMonitor::new();
        let usage = monitor.get_cpu_usage();
        assert!(usage >= 0.0 && usage <= 100.0);
    }

    #[test]
    fn test_memory_usage_range() {
        let monitor = SystemMonitor::new();
        let usage = monitor.get_memory_usage();
        assert!(usage >= 0.0 && usage <= 100.0);
    }
}
