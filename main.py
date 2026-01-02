import yfinance as yf
import datetime
import json
import os

# 存档文件名
FILE_NAME = 'portfolio_status.json'

class AutoBot:
    def __init__(self):
        self.ticker_symbol = "QQQ"
        self.ticker = yf.Ticker(self.ticker_symbol)
        
        # 加载或初始化数据
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "cash": 0,
                "shares": 0,
                "total_invested": 0,
                "last_pe": 35.0,
                "funded_years": [],
                "history": []
            }

    def save_portfolio(self):
        with open(FILE_NAME, 'w') as f:
            json.dump(self.state, f, indent=4)

    def run(self):
        # 1. 检查每年2月充值
        today = datetime.date.today()
        current_year = today.year
        
        # 只要是2月或之后，且今年没充过，就充值
        if today.month >= 2 and current_year not in self.state["funded_years"]:
            self.state["cash"] += 10000
            self.state["total_invested"] += 10000
            self.state["funded_years"].append(current_year)
            self.state["history"].append(f"{today}: 年度充值 +$10,000")
            print(f"💰 {current_year} 年度充值完成")

        # 2. 获取数据
        try:
            # 获取最新收盘价
            data = self.ticker.history(period="1d")
            if data.empty:
                print("❌ 无法获取股价，跳过本次运行")
                return
            price = data['Close'].iloc[-1]
            
            # 获取PE (GitHub Action中获取不到时，使用简单的估算或上次数据)
            try:
                pe = self.ticker.info.get('trailingPE')
            except:
                pe = None
            
            if pe is None:
                # 如果获取失败，沿用上次的PE，避免报错导致程序中断
                pe = self.state["last_pe"]
                print(f"⚠️ 无法获取实时PE，沿用上次数据: {pe}")

            print(f"当前价格: {price}, 当前PE: {pe}")

            # 3. 策略执行 (简化版)
            base_buy = 200
            if pe >= 38 and self.state['shares'] > 0:
                # 卖出
                val = self.state['shares'] * price
                self.state['cash'] += val
                self.state['shares'] = 0
                self.state['history'].append(f"{today}: 清仓卖出 @ {price}")
                
            elif pe <= 34:
                # 定投买入
                buy_amt = base_buy
                # 简单判断余额是否足够
                if self.state['cash'] >= buy_amt:
                    shares = buy_amt / price
                    self.state['shares'] += shares
                    self.state['cash'] -= buy_amt
                    self.state['history'].append(f"{today}: 买入 {shares:.4f}股 @ {price}")

            # 更新 PE 记录
            self.state['last_pe'] = pe
            
            # 4. 保存
            self.save_portfolio()
            print("✅ 运行结束，数据已更新")

        except Exception as e:
            print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    bot = AutoBot()
    bot.run()
