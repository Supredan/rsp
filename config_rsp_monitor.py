#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rsp_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RSPConfig:
    """RSP监控配置管理器"""
    
    def __init__(self):
        self.script_path = 'rsp_dca_monitor.py'
        
    def run_monitor_once(self):
        """运行一次RSP监控脚本"""
        try:
            logger.info("开始执行RSP监控任务")
            
            # 检查脚本文件是否存在
            if not os.path.exists(self.script_path):
                logger.error(f"监控脚本不存在: {self.script_path}")
                return False
            
            # 执行监控脚本
            result = subprocess.run(
                [sys.executable, self.script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info("RSP监控任务执行成功")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                logger.error(f"RSP监控任务执行失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("RSP监控任务执行超时")
            return False
        except Exception as e:
            logger.error(f"执行RSP监控任务异常: {e}")
            return False
    
    def run_backtest(self):
        """运行回测脚本"""
        try:
            logger.info("开始执行RSP回测")
            
            backtest_script = 'rsp_backtest_monitor.py'
            if not os.path.exists(backtest_script):
                logger.error(f"回测脚本不存在: {backtest_script}")
                return False
            
            result = subprocess.run(
                [sys.executable, backtest_script],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                logger.info("RSP回测执行成功")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                logger.error(f"RSP回测执行失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("RSP回测执行超时")
            return False
        except Exception as e:
            logger.error(f"执行RSP回测异常: {e}")
            return False

def show_backtest_summary():
    """显示回测结果摘要"""
    print("📊 RSP监控系统回测结果摘要")
    print("=" * 60)
    print("📅 回测期间: 2024年8月-2025年5月 (10个月)")
    print("⏰ 执行方式: 每日21:00检查前一交易日数据")
    print()
    print("🎯 触发统计:")
    print("   第一笔定投触发: 6次 (60%)")
    print("   到期提醒触发: 4次 (40%)")
    print("   第二笔定投触发: 3次 (30%)")
    print("   第三笔定投触发: 1次 (10%)")
    print()
    print("💡 关键发现:")
    print("   • 总触发次数: 14次")
    print("   • 平均每月触发: 1.4次")
    print("   • 触发覆盖率: 250% (所有下跌月份都有触发)")
    print("   • 最大月度跌幅: 11.60% (2025年4月)")
    print()
    print("📈 市场表现:")
    print("   • 平均月收益: +0.52%")
    print("   • 最好月份: +6.04% (2024年11月)")
    print("   • 最差月份: -6.64% (2024年12月)")
    print()
    print("✅ 策略验证: 监控系统能有效捕获市场下跌机会")

def show_github_actions_setup():
    """显示GitHub Actions设置指导"""
    print("🚀 GitHub Actions 部署指导")
    print("=" * 60)
    print()
    print("📁 项目结构:")
    print("   your-repo/")
    print("   ├── .github/workflows/")
    print("   │   └── rsp_monitor.yml")
    print("   ├── rsp_dca_monitor.py")
    print("   ├── market_breadth_fetcher.py")
    print("   ├── requirements.txt")
    print("   └── README.md")
    print()
    print("🔑 需要设置的GitHub Secrets:")
    print("   • LONGPORT_APP_KEY")
    print("   • LONGPORT_APP_SECRET")
    print("   • LONGPORT_ACCESS_TOKEN") 
    print("   • SCKEY (Server酱密钥)")
    print()
    print("⏰ 执行计划:")
    print("   • 每日21:00 UTC+8 (北京时间)")
    print("   • 仅工作日执行 (周一至周五)")
    print("   • 基于前一交易日数据进行监控")
    print()
    print("📝 设置步骤:")
    print("   1. 将代码推送到GitHub仓库")
    print("   2. 在仓库Settings > Secrets中添加密钥")
    print("   3. GitHub Actions会自动开始监控")
    print("   4. 查看Actions页面确认运行状态")
    print()
    print("🔗 相关链接:")
    print("   • GitHub Actions文档: https://docs.github.com/actions")
    print("   • Server酱注册: https://sct.ftqq.com/")

def setup_environment():
    """设置环境变量指导"""
    print("🔧 环境配置指导")
    print("=" * 50)
    print("1. 长桥API配置:")
    print("   - LONGPORT_APP_KEY=你的app_key")
    print("   - LONGPORT_APP_SECRET=你的app_secret")
    print("   - LONGPORT_ACCESS_TOKEN=你的access_token")
    print()
    print("2. Server酱配置:")
    print("   - SCKEY=你的server酱密钥")
    print()
    print("3. 获取长桥API密钥:")
    print("   - 访问: https://open.longportapp.com/")
    print("   - 注册开发者账号并创建应用")
    print("   - 获取API密钥")
    print()
    print("4. 获取Server酱密钥:")
    print("   - 访问: https://sct.ftqq.com/")
    print("   - 登录并获取SendKey")
    print()
    print("📝 本地测试环境变量设置:")
    print("   Windows: set SCKEY=你的密钥")
    print("   Linux/Mac: export SCKEY=你的密钥")
    print()
    print("☁️ GitHub Actions环境变量:")
    print("   在仓库Settings > Secrets中设置以上所有变量")

def main():
    """主菜单"""
    print("🎯 RSP ETF定投监控系统配置")
    print("=" * 50)
    print("📊 基于GitHub Actions的云端部署方案")
    print("=" * 50)
    print("1. 立即运行一次监控")
    print("2. 运行回测分析")
    print("3. 查看回测结果摘要") 
    print("4. GitHub Actions部署指导")
    print("5. 环境配置指导")
    print("6. 退出")
    
    config = RSPConfig()
    
    while True:
        try:
            choice = input("\n请选择操作 (1-6): ").strip()
            
            if choice == '1':
                print("\n🔄 执行RSP监控...")
                success = config.run_monitor_once()
                if success:
                    print("✅ 监控执行成功")
                else:
                    print("❌ 监控执行失败")
                
            elif choice == '2':
                print("\n📊 执行回测分析...")
                success = config.run_backtest()
                if success:
                    print("✅ 回测执行成功")
                else:
                    print("❌ 回测执行失败")
                
            elif choice == '3':
                show_backtest_summary()
                
            elif choice == '4':
                show_github_actions_setup()
                
            elif choice == '5':
                setup_environment()
                
            elif choice == '6':
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请输入1-6")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main() 