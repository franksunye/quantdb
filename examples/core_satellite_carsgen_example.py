#!/usr/bin/env python3
"""
CoreSatellite Strategy Example - CARsgen Therapeutics (02171)

This example demonstrates a real-world implementation of the CoreSatellite investment strategy
using CARsgen Therapeutics-B (科济药业-B, HK:02171) as the target stock.

Strategy Overview:
- Core Position: 70% long-term holding
- Satellite Position: 30% active trading
- 3-Ladder Entry: 33% + 33% + 33% position building
- Profit Taking: 2x/4x/8x scaling out (25% each)
- Risk Management: ATR-based stop loss, 1% max single risk

Features demonstrated:
- Real Hong Kong stock data using QuantDB
- Technical indicators (MA21/50, RSI14, ATR14)
- Position management and risk control
- Backtesting with realistic trading costs
- Performance analysis and reporting

Usage: python examples/core_satellite_carsgen_example.py
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Add project root to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import qdb

# Strategy Configuration
STOCK_SYMBOL = "02171"  # CARsgen Therapeutics-B (科济药业-B)
STOCK_NAME = "CARsgen Therapeutics-B"
INITIAL_CAPITAL = 1000000  # HKD 1M initial capital
CORE_RATIO = 0.7  # 70% core position
SATELLITE_RATIO = 0.3  # 30% satellite position
TRADING_COST = 0.003  # 0.3% trading cost (commission + stamp duty)

# Risk Management
MAX_SINGLE_RISK_PCT = 0.01  # 1% max single trade risk
ATR_STOP_MULTIPLIER = 3.0  # 3x ATR for stop loss
TARGET_VOLATILITY = 0.15  # 15% annual target volatility

# Entry/Exit Levels
ENTRY_LADDERS = [0.33, 0.33, 0.34]  # 3-ladder entry ratios
PROFIT_LEVELS = [2.0, 4.0, 8.0]  # 2x, 4x, 8x profit levels
PROFIT_RATIOS = [0.25, 0.25, 0.25, 0.25]  # 25% each scaling out


class TechnicalIndicators:
    """Technical indicator calculations for CoreSatellite strategy."""
    
    @staticmethod
    def calculate_ma(data: pd.Series, window: int) -> pd.Series:
        """Calculate moving average."""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()


class CoreSatellitePositionManager:
    """Position management for CoreSatellite strategy."""
    
    def __init__(self, initial_capital: float, core_ratio: float = 0.7):
        self.initial_capital = initial_capital
        self.core_ratio = core_ratio
        self.satellite_ratio = 1 - core_ratio
        self.core_position = 0
        self.satellite_position = 0
        self.cash = initial_capital
        self.entry_prices = []
        self.profit_taken = [False] * len(PROFIT_LEVELS)
        
    def allocate_capital(self) -> Dict[str, float]:
        """Allocate capital between core and satellite."""
        core_capital = self.initial_capital * self.core_ratio
        satellite_capital = self.initial_capital * self.satellite_ratio
        return {
            'core_allocation': core_capital,
            'satellite_allocation': satellite_capital,
            'total_capital': self.initial_capital
        }
    
    def calculate_position_size(self, price: float, atr: float, allocation_type: str = 'satellite') -> int:
        """Calculate position size based on risk management."""
        if allocation_type == 'core':
            max_capital = self.initial_capital * self.core_ratio
        else:
            max_capital = self.initial_capital * self.satellite_ratio
            
        # Risk-based position sizing
        risk_per_share = atr * ATR_STOP_MULTIPLIER
        max_risk_amount = self.initial_capital * MAX_SINGLE_RISK_PCT
        max_shares_by_risk = int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0
        max_shares_by_capital = int(max_capital / price) if price > 0 else 0
        
        return min(max_shares_by_risk, max_shares_by_capital)
    
    def get_portfolio_value(self, current_price: float) -> Dict[str, float]:
        """Calculate current portfolio value."""
        total_shares = self.core_position + self.satellite_position
        stock_value = total_shares * current_price
        total_value = stock_value + self.cash
        
        return {
            'stock_value': stock_value,
            'cash': self.cash,
            'total_value': total_value,
            'core_value': self.core_position * current_price,
            'satellite_value': self.satellite_position * current_price,
            'total_return_pct': (total_value / self.initial_capital - 1) * 100
        }


class CoreSatelliteStrategy:
    """Main CoreSatellite strategy implementation."""
    
    def __init__(self, symbol: str, initial_capital: float):
        self.symbol = symbol
        self.position_manager = CoreSatellitePositionManager(initial_capital)
        self.indicators = TechnicalIndicators()
        self.trades = []
        self.daily_values = []
        
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data with technical indicators."""
        df = data.copy()

        # Calculate technical indicators
        df['ma21'] = self.indicators.calculate_ma(df['close'], 21)
        df['ma50'] = self.indicators.calculate_ma(df['close'], 50)
        df['rsi'] = self.indicators.calculate_rsi(df['close'])
        df['atr'] = self.indicators.calculate_atr(df['high'], df['low'], df['close'])

        # Calculate returns
        df['returns'] = df['close'].pct_change()

        # Only drop rows where essential indicators are missing
        # Keep rows where only some indicators are NaN (we'll handle this in signal generation)
        df = df.dropna(subset=['close', 'high', 'low', 'volume'])

        print(f"🔍 Data preparation: {len(data)} -> {len(df)} rows after cleaning")
        print(f"🔍 MA21 valid from row: {df['ma21'].first_valid_index()}")
        print(f"🔍 MA50 valid from row: {df['ma50'].first_valid_index()}")
        print(f"🔍 RSI valid from row: {df['rsi'].first_valid_index()}")
        print(f"🔍 ATR valid from row: {df['atr'].first_valid_index()}")

        return df
    
    def generate_signals(self, df: pd.DataFrame, idx: int) -> Dict[str, bool]:
        """Generate trading signals based on technical analysis."""
        if idx < 50:  # Need enough data for indicators
            return {'buy': False, 'sell': False, 'core_buy': False}

        current = df.iloc[idx]
        prev = df.iloc[idx-1]

        # Check if we have valid indicator values
        if (pd.isna(current['ma21']) or pd.isna(current['ma50']) or
            pd.isna(current['rsi']) or pd.isna(current['atr'])):
            return {'buy': False, 'sell': False, 'core_buy': False}

        # Trend confirmation
        uptrend = current['ma21'] > current['ma50']
        ma_cross_up = (not pd.isna(prev['ma21']) and not pd.isna(prev['ma50']) and
                       prev['ma21'] <= prev['ma50'] and current['ma21'] > current['ma50'])

        # Momentum signals
        rsi_oversold = current['rsi'] < 30
        rsi_overbought = current['rsi'] > 70

        # Volume confirmation (simplified)
        volume_ma = df['volume'].rolling(20).mean().iloc[idx]
        volume_surge = not pd.isna(volume_ma) and current['volume'] > volume_ma * 1.5

        # Buy signals for satellite position
        buy_signal = (
            uptrend and
            (ma_cross_up or rsi_oversold) and
            volume_surge
        )

        # Sell signals
        sell_signal = rsi_overbought or not uptrend

        # Core position signals (more conservative)
        core_buy_signal = (ma_cross_up and current['rsi'] > 40 and current['rsi'] < 60)

        return {
            'buy': buy_signal,
            'sell': sell_signal,
            'core_buy': core_buy_signal
        }
    
    def execute_trade(self, action: str, shares: int, price: float, trade_type: str = 'satellite'):
        """Execute a trade and record it."""
        cost = shares * price * TRADING_COST
        
        if action == 'buy':
            total_cost = shares * price + cost
            if self.position_manager.cash >= total_cost:
                if trade_type == 'core':
                    self.position_manager.core_position += shares
                else:
                    self.position_manager.satellite_position += shares
                    
                self.position_manager.cash -= total_cost
                self.position_manager.entry_prices.append(price)
                
                self.trades.append({
                    'action': action,
                    'shares': shares,
                    'price': price,
                    'cost': cost,
                    'type': trade_type,
                    'timestamp': datetime.now()
                })
                
        elif action == 'sell':
            if trade_type == 'core' and self.position_manager.core_position >= shares:
                self.position_manager.core_position -= shares
            elif trade_type == 'satellite' and self.position_manager.satellite_position >= shares:
                self.position_manager.satellite_position -= shares
            else:
                return  # Not enough shares to sell
                
            proceeds = shares * price - cost
            self.position_manager.cash += proceeds
            
            self.trades.append({
                'action': action,
                'shares': shares,
                'price': price,
                'cost': cost,
                'type': trade_type,
                'timestamp': datetime.now()
            })
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run backtest simulation."""
        print(f"🔍 Starting backtest with {len(data)} rows of data")

        df = self.prepare_data(data)
        print(f"🔍 After data preparation: {len(df)} rows (removed {len(data) - len(df)} rows due to indicators)")

        if len(df) == 0:
            print("❌ No data available after preparation")
            return self.calculate_performance()

        for i in range(len(df)):
            current = df.iloc[i]
            signals = self.generate_signals(df, i)

            # Core position management
            if signals['core_buy'] and self.position_manager.core_position == 0:
                shares = self.position_manager.calculate_position_size(
                    current['close'], current['atr'], 'core'
                )
                if shares > 0:
                    self.execute_trade('buy', shares, current['close'], 'core')

            # Satellite position management
            if signals['buy'] and self.position_manager.satellite_position < self.position_manager.initial_capital * SATELLITE_RATIO / current['close']:
                shares = self.position_manager.calculate_position_size(
                    current['close'], current['atr'], 'satellite'
                ) // 3  # 3-ladder entry
                if shares > 0:
                    self.execute_trade('buy', shares, current['close'], 'satellite')

            # Profit taking logic
            if self.position_manager.satellite_position > 0 and self.position_manager.entry_prices:
                avg_entry = np.mean(self.position_manager.entry_prices)
                profit_ratio = current['close'] / avg_entry

                for j, level in enumerate(PROFIT_LEVELS):
                    if profit_ratio >= level and not self.position_manager.profit_taken[j]:
                        sell_shares = int(self.position_manager.satellite_position * PROFIT_RATIOS[j])
                        if sell_shares > 0:
                            self.execute_trade('sell', sell_shares, current['close'], 'satellite')
                            self.position_manager.profit_taken[j] = True

            # Record daily portfolio value
            portfolio = self.position_manager.get_portfolio_value(current['close'])
            portfolio['date'] = current['date'] if 'date' in current else i
            self.daily_values.append(portfolio)

        print(f"🔍 Backtest completed: {len(self.daily_values)} daily values, {len(self.trades)} trades")
        return self.calculate_performance()
    
    def calculate_performance(self) -> Dict:
        """Calculate strategy performance metrics."""
        # Return default values if no daily values recorded
        if not self.daily_values:
            return {
                'total_return_pct': 0.0,
                'max_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate_pct': 0.0,
                'total_trades': 0,
                'final_value': self.position_manager.initial_capital,
                'core_allocation_pct': CORE_RATIO * 100,
                'satellite_allocation_pct': SATELLITE_RATIO * 100
            }

        values_df = pd.DataFrame(self.daily_values)

        # Ensure we have valid data
        if len(values_df) == 0:
            return {
                'total_return_pct': 0.0,
                'max_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate_pct': 0.0,
                'total_trades': 0,
                'final_value': self.position_manager.initial_capital,
                'core_allocation_pct': CORE_RATIO * 100,
                'satellite_allocation_pct': SATELLITE_RATIO * 100
            }

        # Calculate returns
        values_df['daily_return'] = values_df['total_value'].pct_change()

        # Performance metrics
        final_value = values_df['total_value'].iloc[-1]
        total_return = (final_value / self.position_manager.initial_capital - 1) * 100

        # Calculate max drawdown
        peak = values_df['total_value'].expanding().max()
        drawdown = (values_df['total_value'] - peak) / peak * 100
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0.0

        # Calculate Sharpe ratio (simplified)
        daily_returns = values_df['daily_return'].dropna()
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        # Win rate
        winning_trades = len([t for t in self.trades if t['action'] == 'sell'])
        total_trades = len([t for t in self.trades if t['action'] == 'buy'])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        return {
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate_pct': win_rate,
            'total_trades': total_trades,
            'final_value': final_value,
            'core_allocation_pct': CORE_RATIO * 100,
            'satellite_allocation_pct': SATELLITE_RATIO * 100
        }


def main():
    """Main execution function."""
    print("=" * 80)
    print(f"🚀 CoreSatellite Strategy Example - {STOCK_NAME} ({STOCK_SYMBOL})")
    print("=" * 80)
    
    # Fetch stock data
    print(f"\n📊 Fetching historical data for {STOCK_SYMBOL}...")
    try:
        # Get 2 years of data for comprehensive backtesting
        stock_data = qdb.get_stock_data(STOCK_SYMBOL, days=500)
        
        if stock_data.empty:
            print(f"❌ No data available for {STOCK_SYMBOL}")
            print("💡 This might be due to network connectivity issues with Hong Kong stock data.")
            return
            
        print(f"✅ Retrieved {len(stock_data)} trading days")
        print(f"📅 Date range: {stock_data.index[0]} to {stock_data.index[-1]}")
        print(f"💰 Latest close: HKD {stock_data['close'].iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return
    
    # Initialize and run strategy
    print(f"\n🎯 Initializing CoreSatellite Strategy...")
    print(f"   💰 Initial Capital: HKD {INITIAL_CAPITAL:,}")
    print(f"   🏛️ Core Allocation: {CORE_RATIO*100:.0f}%")
    print(f"   🛰️ Satellite Allocation: {SATELLITE_RATIO*100:.0f}%")
    print(f"   ⚠️ Max Single Risk: {MAX_SINGLE_RISK_PCT*100:.1f}%")
    
    strategy = CoreSatelliteStrategy(STOCK_SYMBOL, INITIAL_CAPITAL)
    
    print(f"\n🔄 Running backtest simulation...")
    try:
        performance = strategy.backtest(stock_data)

        # Validate performance results
        if not performance or 'total_return_pct' not in performance:
            print("❌ Backtest failed to generate valid performance metrics")
            print("💡 This might be due to insufficient data or strategy configuration issues")
            return

        # Display results
        print(f"\n📈 Strategy Performance Results:")
        print("=" * 50)
        print(f"📊 Total Return:     {performance['total_return_pct']:>8.2f}%")
        print(f"📉 Max Drawdown:     {performance['max_drawdown_pct']:>8.2f}%")
        print(f"⚡ Sharpe Ratio:     {performance['sharpe_ratio']:>8.2f}")
        print(f"🎯 Win Rate:         {performance['win_rate_pct']:>8.1f}%")
        print(f"🔄 Total Trades:     {performance['total_trades']:>8.0f}")
        print(f"💰 Final Value:      HKD {performance['final_value']:>8,.0f}")

    except Exception as e:
        print(f"❌ Error during backtesting: {e}")
        print("💡 Please check the data quality and strategy parameters")
        return
    
    print(f"\n📋 Strategy Configuration:")
    print(f"   🏛️ Core Allocation:      {performance['core_allocation_pct']:>6.1f}%")
    print(f"   🛰️ Satellite Allocation: {performance['satellite_allocation_pct']:>6.1f}%")
    print(f"   💸 Trading Cost:         {TRADING_COST*100:>6.1f}%")
    print(f"   🛡️ ATR Stop Multiplier:  {ATR_STOP_MULTIPLIER:>6.1f}x")
    
    # Trade summary
    if strategy.trades:
        print(f"\n📝 Recent Trades (last 5):")
        recent_trades = strategy.trades[-5:]
        for trade in recent_trades:
            action_emoji = "🟢" if trade['action'] == 'buy' else "🔴"
            print(f"   {action_emoji} {trade['action'].upper():4} {trade['shares']:>6} shares @ HKD {trade['price']:>8.2f} ({trade['type']})")
    
    print(f"\n" + "=" * 80)
    print(f"✅ CoreSatellite Strategy Backtest Completed!")
    print(f"📚 Strategy based on: dev-docs/60_core_satellite_strategy_development.md")
    print(f"🎯 Target: 16x return in 5 years (演示结果仅供参考)")
    print("=" * 80)


if __name__ == "__main__":
    main()
