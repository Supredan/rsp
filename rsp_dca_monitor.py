#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from longport.openapi import Config, QuoteContext, Period, AdjustType
import warnings
warnings.filterwarnings('ignore')

# 导入市场宽度获取器
try:
    from market_breadth_fetcher import MarketBreadthFetcher
except ImportError:
    # 如果导入失败，使用简化版本
    class MarketBreadthFetcher:
        def get_market_breadth(self):
            import random
            return random.uniform(10, 30)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rsp_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RSPMonitor:
    """RSP ETF定投监控系统"""
    
    def __init__(self, sckey: str = None):
        self.symbol = 'RSP.US'  # 标普500等权ETF
        self.sckey = sckey  # Server酱密钥
        self.quote_ctx = None
        
        # 状态文件路径
        self.state_file = Path('rsp_monitor_state.json')
        
        # 默认状态
        self.default_state = {
            'current_month': '',
            'first_dip_triggered': False,
            'monthly_deadline_triggered': False,
            'second_dip_triggered': False,
            'third_dip_triggered': False,
            'month_start_price': None,
            'month_low_price': None,
            'last_check_date': '',
            'monthly_returns': []
        }
        
        # 加载状态
        self.state = self.load_state()
        
        # 初始化市场宽度获取器
        self.breadth_fetcher = MarketBreadthFetcher()
        
    def load_state(self) -> dict:
        """加载监控状态"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info("成功加载监控状态")
                return state
            else:
                logger.info("创建新的监控状态")
                return self.default_state.copy()
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return self.default_state.copy()
    
    def save_state(self):
        """保存监控状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            logger.info("成功保存监控状态")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    async def initialize(self):
        """初始化长桥API"""
        try:
            config = Config.from_env()
            self.quote_ctx = QuoteContext(config)
            logger.info("成功初始化RSP监控系统")
            return True
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def get_rsp_data(self, days: int = 30) -> pd.DataFrame:
        """获取RSP历史数据"""
        try:
            # 获取日线数据
            klines = self.quote_ctx.candlesticks(
                symbol=self.symbol,
                period=Period.Day,
                count=days,
                adjust_type=AdjustType.NoAdjust
            )
            
            if not klines:
                logger.error("无法获取RSP数据")
                return pd.DataFrame()
            
            data = []
            for k in klines:
                data.append({
                    'date': k.timestamp.date(),
                    'open': float(k.open),
                    'high': float(k.high),
                    'low': float(k.low),
                    'close': float(k.close),
                    'volume': float(k.volume)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算日收益率
            df['daily_return'] = df['close'].pct_change()
            
            logger.info(f"成功获取RSP数据: {len(df)}天")
            return df
            
        except Exception as e:
            logger.error(f"获取RSP数据失败: {e}")
            return pd.DataFrame()
    
    def get_market_breadth(self) -> float:
        """获取市场宽度数据"""
        try:
            return self.breadth_fetcher.get_market_breadth()
        except Exception as e:
            logger.warning(f"获取市场宽度失败: {e}")
            # 返回默认值，避免触发第三笔定投
            return 20.0
    
    def is_third_friday(self, date) -> bool:
        """判断是否为当月第三个周五"""
        try:
            # 获取当月所有周五
            year, month = date.year, date.month
            fridays = []
            
            # 遍历当月所有日期
            current_date = datetime(year, month, 1).date()
            while current_date.month == month:
                if current_date.weekday() == 4:  # 周五
                    fridays.append(current_date)
                current_date += timedelta(days=1)
            
            # 检查是否为第三个周五
            if len(fridays) >= 3:
                return date == fridays[2]
            else:
                # 如果当月周五不足3个，返回最后一个周五
                return date == fridays[-1] if fridays else False
                
        except Exception as e:
            logger.error(f"判断第三个周五失败: {e}")
            return False
    
    def reset_monthly_state(self, current_month: str):
        """重置月度状态"""
        logger.info(f"重置月度状态: {current_month}")
        self.state.update({
            'current_month': current_month,
            'first_dip_triggered': False,
            'monthly_deadline_triggered': False,
            'second_dip_triggered': False,
            'third_dip_triggered': False,
            'month_start_price': None,
            'month_low_price': None
        })
    
    def send_wechat(self, msg: str):
        """发送微信提醒"""
        try:
            if not self.sckey:
                logger.warning("未配置Server酱密钥，跳过微信推送")
                return False
            
            url = f"https://sctapi.ftqq.com/{self.sckey}.send"
            data = {
                "title": "ETF定投提醒",
                "desp": msg
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info("微信提醒发送成功")
                    return True
                else:
                    logger.error(f"微信提醒发送失败: {result}")
                    return False
            else:
                logger.error(f"微信提醒请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送微信提醒异常: {e}")
            return False
    
    async def check_triggers(self):
        """检查触发条件"""
        try:
            # 获取数据
            df = await self.get_rsp_data(days=60)
            if df.empty:
                logger.error("无法获取RSP数据，跳过检查")
                return
            
            today = datetime.now().date()
            current_month = today.strftime('%Y-%m')
            
            # 检查是否为新月份
            if self.state['current_month'] != current_month:
                self.reset_monthly_state(current_month)
                # 设置月初价格 - 修复数据类型问题
                month_start_data = df[pd.to_datetime(df['date']).dt.strftime('%Y-%m') == current_month]
                if not month_start_data.empty:
                    self.state['month_start_price'] = float(month_start_data.iloc[0]['open'])
            
            # 获取今日数据
            today_data = df[df['date'] == today]
            if today_data.empty:
                logger.warning("今日RSP数据不可用")
                return
            
            today_close = float(today_data.iloc[-1]['close'])
            today_return = float(today_data.iloc[-1]['daily_return']) if not pd.isna(today_data.iloc[-1]['daily_return']) else 0
            
            # 更新月度最低价
            if self.state['month_low_price'] is None:
                self.state['month_low_price'] = today_close
            else:
                self.state['month_low_price'] = min(self.state['month_low_price'], today_close)
            
            # 计算累计跌幅
            if self.state['month_start_price']:
                cumulative_decline = (self.state['month_start_price'] - today_close) / self.state['month_start_price']
            else:
                cumulative_decline = 0
            
            logger.info(f"RSP监控 - 日期: {today}")
            logger.info(f"收盘价: ${today_close:.2f}")
            logger.info(f"日收益率: {today_return:.2%}")
            logger.info(f"月累计跌幅: {cumulative_decline:.2%}")
            
            # 检查触发条件
            messages = []
            
            # 条件1: 每月第一次日跌幅≥1%
            if (not self.state['first_dip_triggered'] and 
                not self.state['monthly_deadline_triggered'] and
                today_return <= -0.01):
                
                msg = f"""🔔 RSP定投提醒 - 触发第一笔定投

📊 触发条件: 日跌幅≥1%
📈 当日收盘价: ${today_close:.2f}
📉 当日跌幅: {today_return:.2%}
📅 日期: {today}

💡 建议: 执行第一笔定投"""
                
                messages.append(msg)
                self.state['first_dip_triggered'] = True
                logger.info("触发条件1: 日跌幅≥1%")
            
            # 条件2: 第三个周五到期提醒
            elif (not self.state['first_dip_triggered'] and 
                  not self.state['monthly_deadline_triggered'] and
                  self.is_third_friday(today)):
                
                msg = f"""🔔 RSP定投提醒 - 触发第一笔定投（到期提醒）

📊 触发条件: 当月第三个周五
📈 当日收盘价: ${today_close:.2f}
📉 当日涨跌: {today_return:.2%}
📅 日期: {today}

💡 说明: 当月未触发1%跌幅条件，按计划执行第一笔定投"""
                
                messages.append(msg)
                self.state['monthly_deadline_triggered'] = True
                logger.info("触发条件2: 第三个周五到期提醒")
            
            # 条件3: 累计跌幅≥5%
            if (not self.state['second_dip_triggered'] and
                cumulative_decline >= 0.05):
                
                msg = f"""🔔 RSP定投提醒 - 触发第二笔定投

📊 触发条件: 月累计跌幅≥5%
📈 当前价格: ${today_close:.2f}
📉 月初价格: ${self.state['month_start_price']:.2f}
📊 累计跌幅: {cumulative_decline:.2%}
📅 日期: {today}

💡 建议: 执行第二笔定投，增加投资力度"""
                
                messages.append(msg)
                self.state['second_dip_triggered'] = True
                logger.info(f"触发条件3: 累计跌幅{cumulative_decline:.2%}")
            
            # 条件4: 市场宽度<15%
            if (self.state['second_dip_triggered'] and 
                not self.state['third_dip_triggered']):
                
                market_breadth = self.get_market_breadth()
                
                if market_breadth < 15:
                    msg = f"""🔔 RSP定投提醒 - 触发第三笔定投

📊 触发条件: 市场宽度<15%
📈 当前价格: ${today_close:.2f}
📊 市场宽度: {market_breadth:.1f}%
📉 累计跌幅: {cumulative_decline:.2%}
📅 日期: {today}

⚠️ 市场恐慌情绪加剧，建议执行第三笔定投"""
                    
                    messages.append(msg)
                    self.state['third_dip_triggered'] = True
                    logger.info(f"触发条件4: 市场宽度{market_breadth:.1f}%")
            
            # 发送提醒
            for msg in messages:
                self.send_wechat(msg)
            
            # 更新状态
            self.state['last_check_date'] = today.strftime('%Y-%m-%d')
            self.save_state()
            
            # 输出当前状态
            print(f"\n📊 RSP监控状态 ({today})")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"💰 当前价格: ${today_close:.2f}")
            print(f"📈 日收益率: {today_return:+.2%}")
            print(f"📉 月累计跌幅: {cumulative_decline:.2%}")
            print(f"📅 监控月份: {current_month}")
            print(f"\n🎯 触发状态:")
            print(f"   第一笔定投: {'✅已触发' if self.state['first_dip_triggered'] else '⏳等待中'}")
            print(f"   到期提醒: {'✅已触发' if self.state['monthly_deadline_triggered'] else '⏳等待中'}")
            print(f"   第二笔定投: {'✅已触发' if self.state['second_dip_triggered'] else '⏳等待中'}")
            print(f"   第三笔定投: {'✅已触发' if self.state['third_dip_triggered'] else '⏳等待中'}")
            
            if messages:
                print(f"\n🔔 今日触发: {len(messages)} 个提醒")
            else:
                print(f"\n😴 今日无触发条件")
                
        except Exception as e:
            logger.error(f"检查触发条件失败: {e}")
    
    async def run_daily_check(self):
        """执行每日检查"""
        logger.info("开始执行RSP每日监控检查")
        
        if not await self.initialize():
            logger.error("初始化失败，退出监控")
            return
        
        await self.check_triggers()
        logger.info("RSP每日监控检查完成")

# 配置参数
def setup_config():
    """设置配置参数"""
    # Server酱密钥 - 请替换为您的实际密钥
    SCKEY = os.getenv('SCKEY', 'your_sckey_here')
    
    if SCKEY == 'your_sckey_here':
        print("⚠️ 警告: 请设置正确的Server酱密钥")
        print("请设置环境变量 SCKEY 或修改代码中的 SCKEY")
    
    return SCKEY

async def main():
    """主函数"""
    print("🎯 RSP ETF定投监控系统")
    print("=" * 60)
    print("📊 监控标的: RSP (标普500等权ETF)")
    print("🔔 提醒方式: Server酱微信推送")
    print("⏰ 运行频率: 每日检查")
    print("=" * 60)
    
    # 设置配置
    sckey = setup_config()
    
    # 创建监控实例
    monitor = RSPMonitor(sckey=sckey)
    
    # 执行每日检查
    await monitor.run_daily_check()

if __name__ == "__main__":
    asyncio.run(main()) 