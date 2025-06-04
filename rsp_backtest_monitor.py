#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
import pandas as pd
import numpy as np
from longport.openapi import Config, QuoteContext, Period, AdjustType
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rsp_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RSPBacktestMonitor:
    """RSP ETF定投监控系统 - 回测版本"""
    
    def __init__(self):
        self.symbol = 'RSP.US'  # 标普500等权ETF
        self.quote_ctx = None
        
        # 回测结果存储
        self.backtest_results = []
        self.trigger_summary = {
            'first_dip_triggered': 0,
            'monthly_deadline_triggered': 0,
            'second_dip_triggered': 0,
            'third_dip_triggered': 0,
            'total_months': 0
        }
        
    async def initialize(self):
        """初始化长桥API"""
        try:
            config = Config.from_env()
            self.quote_ctx = QuoteContext(config)
            logger.info("成功初始化RSP回测系统")
            return True
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def get_historical_data(self, days: int = 400) -> pd.DataFrame:
        """获取历史数据"""
        try:
            all_data = []
            
            # 分批获取更多历史数据
            batches = max(days // 200, 2)
            for batch in range(batches):
                try:
                    klines = self.quote_ctx.candlesticks(
                        symbol=self.symbol,
                        period=Period.Day,
                        count=min(200, days - len(all_data)),
                        adjust_type=AdjustType.NoAdjust
                    )
                    
                    batch_data = []
                    for k in klines:
                        batch_data.append({
                            'date': k.timestamp.date(),
                            'open': float(k.open),
                            'high': float(k.high),
                            'low': float(k.low),
                            'close': float(k.close),
                            'volume': float(k.volume)
                        })
                    
                    if not batch_data:
                        break
                        
                    all_data.extend(batch_data)
                    await asyncio.sleep(0.5)  # 避免API限制
                    
                    if len(all_data) >= days:
                        break
                        
                except Exception as e:
                    logger.warning(f"批次{batch+1}数据获取失败: {e}")
                    continue
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            df = df.sort_values('date').drop_duplicates(subset=['date'])
            df = df.reset_index(drop=True)
            
            # 计算日收益率
            df['daily_return'] = df['close'].pct_change()
            
            # 添加月份信息
            df['year_month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
            
            logger.info(f"成功获取RSP历史数据: {len(df)}天")
            logger.info(f"数据范围: {df['date'].min()} 至 {df['date'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def is_third_friday(self, check_date: date) -> bool:
        """判断是否为当月第三个周五"""
        try:
            year, month = check_date.year, check_date.month
            fridays = []
            
            current_date = date(year, month, 1)
            while current_date.month == month:
                if current_date.weekday() == 4:  # 周五
                    fridays.append(current_date)
                current_date += timedelta(days=1)
            
            if len(fridays) >= 3:
                return check_date == fridays[2]
            else:
                return check_date == fridays[-1] if fridays else False
                
        except Exception as e:
            logger.error(f"判断第三个周五失败: {e}")
            return False
    
    def simulate_market_breadth(self, date_val: date, volatility: float) -> float:
        """模拟市场宽度数据"""
        try:
            # 基于日期和波动率生成伪随机但一致的市场宽度
            import random
            seed = int(date_val.strftime('%Y%m%d')) % 10000
            random.seed(seed)
            
            # 高波动时市场宽度更低
            base_breadth = 30.0 - (volatility * 100)  # 波动率越高，市场宽度越低
            variation = random.uniform(-15, 15)
            breadth = max(5.0, min(50.0, base_breadth + variation))
            
            return breadth
            
        except Exception as e:
            logger.error(f"模拟市场宽度失败: {e}")
            return 25.0
    
    def analyze_month(self, monthly_data: pd.DataFrame, month_str: str) -> dict:
        """分析单个月份的触发情况"""
        try:
            if monthly_data.empty:
                return None
            
            # 初始化月度状态
            month_state = {
                'month': month_str,
                'first_dip_triggered': False,
                'monthly_deadline_triggered': False,
                'second_dip_triggered': False,
                'third_dip_triggered': False,
                'triggers': [],
                'month_start_price': None,
                'month_end_price': None,
                'month_return': 0,
                'max_decline': 0,
                'trading_days': len(monthly_data)
            }
            
            # 获取月初和月末价格
            month_state['month_start_price'] = float(monthly_data.iloc[0]['open'])
            month_state['month_end_price'] = float(monthly_data.iloc[-1]['close'])
            month_state['month_return'] = (month_state['month_end_price'] - month_state['month_start_price']) / month_state['month_start_price']
            
            # 逐日分析
            for i, (idx, row) in enumerate(monthly_data.iterrows()):
                current_date = row['date']
                current_close = float(row['close'])
                daily_return = float(row['daily_return']) if not pd.isna(row['daily_return']) else 0
                
                # 计算累计跌幅（从月初到当前）
                cumulative_decline = (month_state['month_start_price'] - current_close) / month_state['month_start_price']
                month_state['max_decline'] = max(month_state['max_decline'], cumulative_decline)
                
                # 模拟每天晚上9点检查（基于当天收盘数据）
                
                # 条件1: 每月第一次日跌幅≥1%
                if (not month_state['first_dip_triggered'] and 
                    not month_state['monthly_deadline_triggered'] and
                    daily_return <= -0.01):
                    
                    trigger = {
                        'date': current_date,
                        'type': 'first_dip',
                        'condition': '日跌幅≥1%',
                        'daily_return': daily_return,
                        'price': current_close,
                        'cumulative_decline': cumulative_decline
                    }
                    month_state['triggers'].append(trigger)
                    month_state['first_dip_triggered'] = True
                
                # 条件2: 第三个周五到期提醒
                elif (not month_state['first_dip_triggered'] and 
                      not month_state['monthly_deadline_triggered'] and
                      self.is_third_friday(current_date)):
                    
                    trigger = {
                        'date': current_date,
                        'type': 'monthly_deadline',
                        'condition': '第三个周五到期',
                        'daily_return': daily_return,
                        'price': current_close,
                        'cumulative_decline': cumulative_decline
                    }
                    month_state['triggers'].append(trigger)
                    month_state['monthly_deadline_triggered'] = True
                
                # 条件3: 累计跌幅≥5%
                if (not month_state['second_dip_triggered'] and
                    cumulative_decline >= 0.05):
                    
                    trigger = {
                        'date': current_date,
                        'type': 'second_dip',
                        'condition': '月累计跌幅≥5%',
                        'daily_return': daily_return,
                        'price': current_close,
                        'cumulative_decline': cumulative_decline
                    }
                    month_state['triggers'].append(trigger)
                    month_state['second_dip_triggered'] = True
                
                # 条件4: 市场宽度<15%（在第二笔触发后）
                if (month_state['second_dip_triggered'] and 
                    not month_state['third_dip_triggered']):
                    
                    # 计算最近几天的波动率
                    if i >= 5:
                        recent_returns = monthly_data.iloc[max(0, i-4):i+1]['daily_return'].dropna()
                        volatility = recent_returns.std() if len(recent_returns) > 1 else 0.01
                    else:
                        volatility = 0.01
                    
                    market_breadth = self.simulate_market_breadth(current_date, volatility)
                    
                    if market_breadth < 15:
                        trigger = {
                            'date': current_date,
                            'type': 'third_dip',
                            'condition': '市场宽度<15%',
                            'daily_return': daily_return,
                            'price': current_close,
                            'cumulative_decline': cumulative_decline,
                            'market_breadth': market_breadth
                        }
                        month_state['triggers'].append(trigger)
                        month_state['third_dip_triggered'] = True
            
            return month_state
            
        except Exception as e:
            logger.error(f"分析月份{month_str}失败: {e}")
            return None
    
    async def run_backtest(self, days: int = 365):
        """运行回测"""
        logger.info(f"开始RSP监控系统{days}天回测")
        
        # 获取历史数据
        df = await self.get_historical_data(days + 30)  # 多获取一些数据确保覆盖
        if df.empty:
            logger.error("无法获取历史数据")
            return
        
        # 按月份分组分析
        monthly_groups = df.groupby('year_month')
        
        for month_str, monthly_data in monthly_groups:
            if len(monthly_data) < 5:  # 跳过数据不足的月份
                continue
                
            month_result = self.analyze_month(monthly_data, month_str)
            if month_result:
                self.backtest_results.append(month_result)
                
                # 更新统计
                self.trigger_summary['total_months'] += 1
                if month_result['first_dip_triggered']:
                    self.trigger_summary['first_dip_triggered'] += 1
                if month_result['monthly_deadline_triggered']:
                    self.trigger_summary['monthly_deadline_triggered'] += 1
                if month_result['second_dip_triggered']:
                    self.trigger_summary['second_dip_triggered'] += 1
                if month_result['third_dip_triggered']:
                    self.trigger_summary['third_dip_triggered'] += 1
        
        # 生成报告
        self.generate_backtest_report()
    
    def generate_backtest_report(self):
        """生成回测报告"""
        print("\n" + "="*80)
        print("📊 RSP ETF定投监控系统 - 回测报告")
        print("="*80)
        print(f"📅 回测期间: {len(self.backtest_results)} 个月")
        print(f"⏰ 执行时间: 每日21:00（基于前一交易日数据）")
        print(f"📈 监控标的: RSP (标普500等权ETF)")
        
        if not self.backtest_results:
            print("❌ 无回测数据")
            return
        
        # 统计摘要
        print(f"\n📊 触发统计摘要:")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"总监控月数: {self.trigger_summary['total_months']}")
        print(f"第一笔定投触发: {self.trigger_summary['first_dip_triggered']} 次 ({self.trigger_summary['first_dip_triggered']/self.trigger_summary['total_months']:.1%})")
        print(f"到期提醒触发: {self.trigger_summary['monthly_deadline_triggered']} 次 ({self.trigger_summary['monthly_deadline_triggered']/self.trigger_summary['total_months']:.1%})")
        print(f"第二笔定投触发: {self.trigger_summary['second_dip_triggered']} 次 ({self.trigger_summary['second_dip_triggered']/self.trigger_summary['total_months']:.1%})")
        print(f"第三笔定投触发: {self.trigger_summary['third_dip_triggered']} 次 ({self.trigger_summary['third_dip_triggered']/self.trigger_summary['total_months']:.1%})")
        
        # 详细触发记录
        print(f"\n📋 详细触发记录:")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        total_triggers = 0
        for result in self.backtest_results:
            if result['triggers']:
                print(f"\n📅 {result['month']} (月收益: {result['month_return']:+.2%}, 最大跌幅: {result['max_decline']:.2%})")
                for trigger in result['triggers']:
                    total_triggers += 1
                    breadth_info = f", 市场宽度: {trigger['market_breadth']:.1f}%" if 'market_breadth' in trigger else ""
                    print(f"   🔔 {trigger['date']} - {trigger['condition']} (日收益: {trigger['daily_return']:+.2%}, 价格: ${trigger['price']:.2f}){breadth_info}")
        
        print(f"\n💡 回测洞察:")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"总触发次数: {total_triggers}")
        print(f"平均每月触发: {total_triggers/self.trigger_summary['total_months']:.1f} 次")
        
        # 月收益率分析
        monthly_returns = [r['month_return'] for r in self.backtest_results]
        max_declines = [r['max_decline'] for r in self.backtest_results]
        
        print(f"月收益率统计:")
        print(f"   平均月收益: {np.mean(monthly_returns):+.2%}")
        print(f"   月收益标准差: {np.std(monthly_returns):.2%}")
        print(f"   最好月份: {max(monthly_returns):+.2%}")
        print(f"   最差月份: {min(monthly_returns):+.2%}")
        
        print(f"最大跌幅统计:")
        print(f"   平均最大跌幅: {np.mean(max_declines):.2%}")
        print(f"   最大跌幅: {max(max_declines):.2%}")
        
        # 策略有效性分析
        trigger_months = len([r for r in self.backtest_results if r['triggers']])
        decline_months = len([r for r in self.backtest_results if r['month_return'] < 0])
        
        print(f"\n🎯 策略有效性:")
        print(f"触发月份数: {trigger_months}")
        print(f"下跌月份数: {decline_months}")
        print(f"触发覆盖率: {trigger_months/decline_months:.1%}" if decline_months > 0 else "触发覆盖率: N/A")
        
        # 保存详细结果
        self.save_backtest_results()
    
    def save_backtest_results(self):
        """保存回测结果"""
        try:
            # 保存详细结果到CSV
            detailed_results = []
            for result in self.backtest_results:
                base_record = {
                    'month': result['month'],
                    'month_start_price': result['month_start_price'],
                    'month_end_price': result['month_end_price'],
                    'month_return': result['month_return'],
                    'max_decline': result['max_decline'],
                    'trading_days': result['trading_days'],
                    'total_triggers': len(result['triggers'])
                }
                
                if result['triggers']:
                    for trigger in result['triggers']:
                        record = base_record.copy()
                        record.update({
                            'trigger_date': trigger['date'],
                            'trigger_type': trigger['type'],
                            'trigger_condition': trigger['condition'],
                            'trigger_daily_return': trigger['daily_return'],
                            'trigger_price': trigger['price'],
                            'trigger_cumulative_decline': trigger['cumulative_decline'],
                            'trigger_market_breadth': trigger.get('market_breadth', None)
                        })
                        detailed_results.append(record)
                else:
                    detailed_results.append(base_record)
            
            df_results = pd.DataFrame(detailed_results)
            df_results.to_csv('rsp_backtest_results.csv', index=False, encoding='utf-8-sig')
            
            # 保存汇总统计
            summary = {
                'backtest_summary': self.trigger_summary,
                'total_triggers': sum(len(r['triggers']) for r in self.backtest_results),
                'backtest_period': f"{self.backtest_results[0]['month']} to {self.backtest_results[-1]['month']}" if self.backtest_results else "No data"
            }
            
            with open('rsp_backtest_summary.json', 'w', encoding='utf-8') as f:
                import json
                json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n📁 回测结果已保存:")
            print(f"   详细结果: rsp_backtest_results.csv")
            print(f"   汇总统计: rsp_backtest_summary.json")
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {e}")

async def main():
    """主函数"""
    print("🎯 RSP ETF定投监控系统 - 回测模式")
    print("=" * 60)
    print("📊 监控标的: RSP (标普500等权ETF)")
    print("⏰ 模拟执行: 每日21:00 (基于前一交易日数据)")
    print("📅 回测期间: 过去1年")
    print("=" * 60)
    
    backtest = RSPBacktestMonitor()
    
    if not await backtest.initialize():
        logger.error("系统初始化失败")
        return
    
    await backtest.run_backtest(days=365)

if __name__ == "__main__":
    asyncio.run(main()) 