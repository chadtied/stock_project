import backtrader as bt
import yfinance as yf
import numpy as np
import json
import calendar
import matplotlib.pyplot as plt
from datetime import date
import math


#buy and hold 策略
class BuyAndHold_More_Fund(bt.Strategy):
    params = dict(
        monthly_cash= 1000.0,  # amount of cash to buy every month
    )

    def start(self):
        # Activate the fund mode and set the default value at 100
        #self.broker.set_fundmode(fundmode=True, fundstartval=100.00)
        self.cash_start = self.broker.get_cash()
        self.yearly_cash= dict()
        #self.val_start = 100.0
        # Add a timer which will be called on the 1st trading day of the month
        self.add_timer(
            bt.timer.SESSION_START,  # when it will be called
            monthdays=[1],  # called on the 1st day of the month
            monthcarry=True,  # called on the 2nd day if the 1st is holiday
        )

    def notify_timer(self, timer, when, *args, **kwargs):
        # Add the influx of monthly cash to the broker
        self.broker.add_cash(self.p.monthly_cash)
        self.cash_start+= self.p.monthly_cash
        if self.data.datetime.date(0).year in self.yearly_cash:  self.yearly_cash[self.data.datetime.date(0).year]+= self.p.monthly_cash
        else:   self.yearly_cash[self.data.datetime.date(0).year]= 0
        # buy available cash
        print(self.broker.get_value())
        print(self.broker.get_cash())
        target_value = self.broker.get_value()
        self.order_target_value(target= int(target_value*0.99))

    def stop(self):
        # calculate the actual returns
        #self.froi = self.broker.get_fundvalue() - self.val_start
        #print('Fund Value: {:.2f}%'.format(self.froi))
        pass
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 訂單已提交/接受 - 什麼也不做
            return
        # 檢查訂單是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('買入執行, 價格: {:.2f}, 成交量: {:.2f}'.format(
                    order.executed.price,
                    order.executed.size))
            elif order.issell():
                self.log('賣出執行, 價格: {:.2f}, 成交量: {:.2f}'.format(
                    order.executed.price,
                    order.executed.size))

            self.bar_executed = len(self)
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('淨利潤, 淨利: {:.2f}, 毛利: {:.2f}, 佣金: {:.2f}'.format(
            trade.pnl,
            trade.pnlcomm,
            trade.commission))
    def log(self, text, dt=None):
        ''' 日誌函數，用於記錄策略的執行信息 '''
        dt = dt or self.data.datetime.date(0)
        print(f'{dt.isoformat()}, {text}')
#線性策略
class MyStrategy(bt.Strategy):
    
    def __init__(self):
        self.dataclose= self.data0.close
        self.sma_buy_stragy= {"中多趨勢": False, "短多趨勢": False, "突破年季線": False}
        self.sma_close_stragy= {"出量上引線": False, "型態破壞": False}

        self.sma5= bt.indicators.MovingAverageSimple(self.data0, period= 5)
        self.sma10= bt.indicators.MovingAverageSimple(self.data0, period= 10)
        self.sma20= bt.indicators.MovingAverageSimple(self.data0, period= 20)
        self.sma60= bt.indicators.MovingAverageSimple(self.data0, period= 60)
        self.sma120= bt.indicators.MovingAverageSimple(self.data0, period= 120)
        self.sma240= bt.indicators.MovingAverageSimple(self.data0, period= 240)
    def vol_stragy(self):
        if self.data0.volume[0]> self.data0.volume[-2] or self.data0.volume[0]> self.data0.volume[-3] or self.data0.volume[0]> self.data0.volume[-1]:
            upper_shadow= self.data0.high[0]- self.data0.close[0]
            rate= self.data0.close[0]- self.data0.open[0]
            if upper_shadow> rate:  self.sma_close_stragy["出量上引線"]= True
            else:   self.sma_close_stragy["出量上引線"]= False

    def sma_stragy(self):
        over_sma5= self.dataclose[0]> self.sma5[0]
        slot_sma5= self.sma5[0]- self.sma5[-1]
        over_sma10= self.dataclose[0]> self.sma10[0]
        slot_sma10= self.sma10[0]- self.sma10[-1]
        over_sma20= self.dataclose[0]> self.sma20[0]
        slot_sma20= self.sma20[0]- self.sma20[-1]
        over_sma60= self.dataclose[0]> self.sma60[0]
        slot_sma60= self.sma60[0]- self.sma60[-1]
        
        over_sma120= self.dataclose[0]> self.sma120[0]
        over_sma240= self.dataclose[0]> self.sma240[0]

        #print("收盤價: ", self.dataclose[0], "五日均: ", self.sma5[0], "十日均: ", slot_sma10, "二十日均: ", self.sma20[0], "一百二十日均: ", self.sma120[0])
        if over_sma5 and over_sma10 and slot_sma5> 0 and slot_sma10> 0:    self.sma_buy_stragy["短多趨勢"]= True
        else:   self.sma_buy_stragy["短多趨勢"]= False

        if over_sma20 and over_sma60 and slot_sma20> 0 and slot_sma60> 0:    self.sma_buy_stragy["中多趨勢"]= True
        else:   self.sma_buy_stragy["中多趨勢"]= False

        if slot_sma5< 0 and over_sma5:  self.sma_close_stragy["型態破壞"]= True
        else:   self.sma_close_stragy["型態破壞"]= False

        if over_sma120 and over_sma240: self.sma_buy_stragy["突破年季線"]= True
        else:   self.sma_buy_stragy["突破年季線"]= False
    
    def log(self, text, dt=None):
        ''' 日誌函數，用於記錄策略的執行信息 '''
        dt = dt or self.data.datetime.date(0)
        print(f'{dt.isoformat()}, {text}')

    
    def next(self):
        ''' 主要的策略邏輯，每個 bar 呼叫一次 '''
        self.log(f'收盤價: {self.data.close[0]}')
        self.sma_stragy()
        self.vol_stragy()
        print(self.sma_buy_stragy)
        print(self.sma_close_stragy)

        #if self.sma_close_stragy["出量上引線"] or self.sma_close_stragy["型態破壞"]:
        if self.sma_close_stragy["型態破壞"]:
            self.close()
        elif self.sma_buy_stragy["短多趨勢"] and self.sma_buy_stragy["中多趨勢"] and self.sma_buy_stragy["突破年季線"]:
            self.buy(price= self.data0.close[0], )
        print("=====================\n")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 訂單已提交/接受 - 什麼也不做
            return
        # 檢查訂單是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('買入執行, 價格: {:.2f}, 成交量: {:.2f}'.format(
                    order.executed.price,
                    order.executed.size))
            elif order.issell():
                self.log('賣出執行, 價格: {:.2f}, 成交量: {:.2f}'.format(
                    order.executed.price,
                    order.executed.size))

            self.bar_executed = len(self)
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('淨利潤, 淨利: {:.2f}, 毛利: {:.2f}, 佣金: {:.2f}'.format(
            trade.pnl,
            trade.pnlcomm,
            trade.commission))

#索蒂諾比率
class SortinoRatio(bt.Analyzer):

    def __init__(self):
        self.returns = []

    def next(self):
        if len(self.data) > 1:
            ret = (self.data.close[0] / self.data.close[-1]) - 1
            self.returns.append(ret)

    def get_analysis(self):
        rf = 0
        downside_risk = np.std([r for r in self.returns if r < rf]) * np.sqrt(252)
        mean_return = np.mean(self.returns) * 252
        sortino_ratio = (mean_return - rf) / downside_risk if downside_risk != 0 else 0
        return {'sortino_ratio': sortino_ratio}


#獲取傳入json檔資料
with open('./buy_and_hold.json', 'r') as f:
    data = json.load(f)

#設立變數
    #Portfolios= data['Portfolios']
Timeperiod= data['EndYear']- data['StartYear']+ 1
StartYear, StartMonth= data['StartYear'], data['FirstMonth']
EndYear, EndMonth= data['EndYear'], data['LastMonth']
Timeperiod_month= Timeperiod*12- (StartMonth-1)- (12- EndMonth)
EndYear= data['EndYear']
initial_Amount= data['initialAmount']
ContributionAmount= 0
if data['CashFlows']== 'Contribute fixed amount':    ContributionAmount= data['ContributionAmount']
elif data['CashFlows']== 'Withdraw fixed amount':    ContributionAmount= -data['ContributionAmount']

# 初始化 Cerebro 引擎
cerebro = bt.Cerebro()

# 添加策略
cerebro.addstrategy(BuyAndHold_More_Fund, monthly_cash= ContributionAmount)

# 設置初始資金
cerebro.broker.setcash(initial_Amount)
# 設置手續費
cerebro.broker.setcommission(commission=0.001)
#cerebro.addsizer(bt.sizers.PercentSizer, percents= 90)


# 添加數據
data = bt.feeds.PandasData(dataname=yf.download("2330.TW", start= date(StartYear, StartMonth, 1), end= date(EndYear, EndMonth, calendar.monthrange(EndYear, EndMonth)[1])))
cerebro.adddata(data)

# 添加分析器
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name= 'annualreturn')
cerebro.addanalyzer(bt.analyzers.Returns, _name= 'returns')
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name= 'sharpe_ratio')
cerebro.addanalyzer(SortinoRatio, _name= 'sortino_ratio')
cerebro.addanalyzer(bt.analyzers.Calmar, _name= 'calmar')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name= 'drawdown')
cerebro.addanalyzer(bt.analyzers.PeriodStats, _name= 'periodstats')
# 運行策略
results= cerebro.run()

# 獲取初始资金
initial_cash = cerebro.broker.startingcash
#獲取分析結果

Roi= (cerebro.broker.getvalue()/results[0].cash_start)-1
FinalBalance= cerebro.broker.getvalue()- initial_cash- Timeperiod_month*ContributionAmount
CAGR= math.pow(Roi+1, 1/(Timeperiod_month/12))-1
BestYear= initial_cash*(1+max(results[0].analyzers.annualreturn.get_analysis().values()))-results[0].yearly_cash[max(results[0].analyzers.annualreturn.get_analysis(), key=results[0].analyzers.annualreturn.get_analysis().get)]
WorstYear= initial_cash*(1+min(results[0].analyzers.annualreturn.get_analysis().values()))-results[0].yearly_cash[min(results[0].analyzers.annualreturn.get_analysis(), key=results[0].analyzers.annualreturn.get_analysis().get)]
sharpe_ratio = results[0].analyzers.sharpe_ratio.get_analysis()
drawdown = results[0].analyzers.drawdown.get_analysis()
periodstats= results[0].analyzers.periodstats.get_analysis()
sortino_ratio = results[0].analyzers.sortino_ratio.get_analysis()
#empyrical.sortino_ratio(returns= Roi/Timeperiod_month ,annualization= 12)

print("投資報酬率:", round(Roi,2))
print("年均複合成長率: ", round(CAGR,2))
print("標準差:", round(periodstats['stddev'],2))
print("總複利回報:", round(FinalBalance,2))
print("最佳年收入:", round(BestYear,2))
print("最差年收入", round(WorstYear,2))
print(f"夏普比率: {round(sharpe_ratio['sharperatio'],2)}")
print(f"最大回撤: {round(drawdown['max']['drawdown'],2)}")
print('索蒂諾比率:', round(sortino_ratio['sortino_ratio'],2))

# 繪製結果
cerebro.plot(style='candlestick', iplot=False,  start= date(2023,6,1), end= date(2024,5,4))
