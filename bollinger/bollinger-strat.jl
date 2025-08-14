//@version=5
strategy("Swing Bollinger Mean Reversion (Hybrid + SR + Dynamic Volatility + TP/SL Labels)", 
     overlay=true,
     initial_capital=10000,
     default_qty_type=strategy.fixed,
     default_qty_value=1,
     pyramiding=0)

// === Inputs ===
enableBreakeven = input.bool(false, "Enable Breakeven Stop")
breakevenTrigger = input.float(0.5, "Breakeven Trigger (% of Entry)", step=0.01)
bbLength      = input.int(20, "Bollinger Length")
bbStdDev      = input.float(2.0, "Bollinger StdDev")
rsiLength     = input.int(14, "RSI Length")
rsiOversold   = input.float(30, "RSI Oversold")
rsiOverbought = input.float(70, "RSI Overbought")
atrLength     = input.int(14, "ATR Length")
atrMultiplier = input.float(1.2, "ATR Stop Multiplier")
riskReward    = input.float(2.7, "Base Risk/Reward Ratio")

useSessionFilter   = input.bool(false, "Enable Session Filter")
useADXFilter       = input.bool(false, "Enable ADX Filter")
adxLength          = input.int(14, "ADX Length")
adxThreshold       = input.float(30, "ADX Threshold")

enableMidlineExit  = input.bool(false, "Enable Midline Early Exit")
partialExit        = input.bool(false, "Partial Exit (50%) at Midline")

useTrendFilter     = input.bool(false, "Enable Higher TF Trend Filter")
trendTF            = input.timeframe("60", "Trend Higher Timeframe")

useCandleFilter    = input.bool(false, "Enable Candle Confirmation Filter")
useRSIDivergence   = input.bool(false, "Enable RSI Divergence Filter")
useDynamicRR       = input.bool(false, "Enable Dynamic Risk/Reward")

useLimitOrders     = input.bool(true, "Use Limit Orders for Entries")
entryOffsetPips    = input.float(10, "Limit Order Offset (pips)")
limitOrderTimeout  = input.int(3, "Limit Order Timeout (bars)")

// === Hybrid Mode Inputs ===
enableHybridMode   = input.bool(false, "Enable Hybrid Mode")
trendADXMin        = input.float(25, "ADX Min for Trend Mode")
bandwidthThreshold = input.float(0.05, "Bollinger Bandwidth Threshold (5%)")
trendTrailATRmult  = input.float(2.0, "ATR Multiplier for Trailing Stop")

// === Time Exit Inputs ===
enableTimeExit     = input.bool(false, "Enable Time-Based Exit")
maxBarsInTrade     = input.int(20, "Max Bars in Trade Before Exit")

// === Support/Resistance Filter Inputs ===
enableSRFilter     = input.bool(false, "Enable Support/Resistance Filter")
pivotLen           = input.int(10, "Pivot Length")
srThresholdATR     = input.float(1.0, "Max Distance to S/R (ATR multiples)")

// === Volatility Filter Inputs ===
enableVolatilityFilter = input.bool(true, "Enable Volatility Breakout Filter")
volatilityMode         = input.string("Dynamic", "Volatility Mode", options=["Static", "Dynamic"])
volatilityThreshold    = input.float(0.5, "Static: Min ATR % of Price")
volatilityLookback     = input.int(200, "Dynamic: Baseline Lookback")
volatilityMultiplier   = input.float(0.8, "Dynamic: Min Volatility Multiplier")

// === TP/SL Label Option ===
showTP_SL_Labels = input.bool(false, "Show TP/SL Price & Distance Labels")

// === Sessions ===
londonSessionStart = input.int(7, "London Session Start Hour (UTC)")
londonSessionEnd   = input.int(16, "London Session End Hour (UTC)")
nySessionStart     = input.int(13, "NY Session Start Hour (UTC)")
nySessionEnd       = input.int(22, "NY Session End Hour (UTC)")

//
// === High-Spread Window Inputs (DST-aware) ===
enableNoTradeWindow = input.bool(true, "Block High-Spread Window")
// NOTE: Pine expects session strings in HHMM-HHMM (no colons). Default covers typical FX rollover.
noTradeSession      = input.session("2300-0000", "No-Trade Session (local to chosen timezone)")
// Allow users to type with colons; sanitize to HHMM-HHMM for time() calls.
sessionRaw = noTradeSession
sessionFixed = str.replace(sessionRaw, ":", "")
// Timezone used for the no-trade session (DST handled automatically for IANA zones)
noTradeTZ = input.string("Europe/Paris", "No-Trade Timezone (IANA)", 
     options=["UTC","Europe/London","Europe/Paris","America/New_York","America/Chicago","Asia/Tokyo","Australia/Sydney"])

// Visual shading options for no-trade window
showNoTradeShading = input.bool(true, "Shade No-Trade Window")
noTradeShadeColor  = input.color(color.red, "No-Trade Shade Color")
noTradeShadeTransp = input.int(85, "No-Trade Shade Transparency (0-100)", minval=0, maxval=100)

coolDownBars = input.int(5, "Cool-Down Period (Bars)")
riskPercent  = input.float(0.25, "Risk per Trade (%)")

// === Indicators ===
basis = ta.sma(close, bbLength)
dev = bbStdDev * ta.stdev(close, bbLength)
upperBand = basis + dev
lowerBand = basis - dev
rsi = ta.rsi(close, rsiLength)
atr = ta.atr(atrLength)

// === Band Width for Regime Detection ===
bandWidth = (upperBand - lowerBand) / basis
dynRiskReward = riskReward * (1 + (bandWidth - 0.02))

// === Manual ADX Calculation ===
upMove = high - high[1]
downMove = low[1] - low
plusDM = (upMove > downMove and upMove > 0) ? upMove : 0
minusDM = (downMove > upMove and downMove > 0) ? downMove : 0
trur = ta.rma(ta.tr(true), adxLength)
plusDI = 100 * ta.rma(plusDM, adxLength) / trur
minusDI = 100 * ta.rma(minusDM, adxLength) / trur
dx = 100 * math.abs(plusDI - minusDI) / (plusDI + minusDI)
adx = ta.rma(dx, adxLength)

// === Market Regime Detection ===
isTrending = (adx > trendADXMin) and (bandWidth > bandwidthThreshold)
isRanging  = not isTrending

// === Higher TF Trend Filter ===
htf_basis = request.security(syminfo.tickerid, trendTF, ta.sma(close, bbLength))
trendConditionLong  = (not useTrendFilter) or (close <= htf_basis)
trendConditionShort = (not useTrendFilter) or (close >= htf_basis)

// === Candle Confirmation ===
bullishEngulfing = close > open and open <= close[1] and open[1] > close[1] and close >= open[1]
bullishPin = (open - low > (high - low) * 0.4) and (math.abs(close - open) < (high - low) * 0.3)
bearishEngulfing = open > close and open >= close[1] and open[1] < close[1] and close <= open[1]
bearishPin = (high - open > (high - low) * 0.4) and (math.abs(open - close) < (high - low) * 0.3)

bullishCandle = bullishEngulfing or bullishPin
bearishCandle = bearishEngulfing or bearishPin

candleConditionLong  = (not useCandleFilter) or bullishCandle
candleConditionShort = (not useCandleFilter) or bearishCandle

// === RSI Divergence ===
bullishDiv = (low < low[1]) and (rsi > rsi[1])
bearishDiv = (high > high[1]) and (rsi < rsi[1])

rsiDivConditionLong  = (not useRSIDivergence) or bullishDiv
rsiDivConditionShort = (not useRSIDivergence) or bearishDiv

// === Session Filter ===
currentHour = hour(time, "UTC")
inLondon = (currentHour >= londonSessionStart and currentHour < londonSessionEnd)
inNY = (currentHour >= nySessionStart and currentHour < nySessionEnd)
allowedSession = (not useSessionFilter) or (inLondon or inNY)

//
// === High-Spread Window Blocker ===
// If the current bar time is inside the configured no-trade session, block entries.
noTradeActive = enableNoTradeWindow and not na(time(timeframe.period, sessionFixed, noTradeTZ))
spreadOK      = not noTradeActive

// Shade the chart background during the no-trade window
bgcolor(showNoTradeShading and noTradeActive ? color.new(noTradeShadeColor, noTradeShadeTransp) : na)

// === ADX Filter ===
adxCondition = (not useADXFilter) or (adx < adxThreshold)

// === Volatility Filter ===
atrPercent = (atr / close) * 100
baselineVolatility = ta.sma(atrPercent, volatilityLookback)
dynamicThreshold = baselineVolatility * volatilityMultiplier
volatilityCondition = not enableVolatilityFilter or ( (volatilityMode == "Static" and atrPercent >= volatilityThreshold) or (volatilityMode == "Dynamic" and atrPercent >= dynamicThreshold))

// === Cool-Down ===
var lastTradeBar = -coolDownBars * 2
coolDownActive = (bar_index - lastTradeBar) < coolDownBars

// === Support/Resistance ===
support = ta.pivotlow(low, pivotLen, pivotLen)
resistance = ta.pivothigh(high, pivotLen, pivotLen)

var float lastSupport = na
var float lastResistance = na

if not na(support)
    lastSupport := support
if not na(resistance)
    lastResistance := resistance

distToSupport = na(lastSupport) ? na : math.abs(close - lastSupport)
distToResistance = na(lastResistance) ? na : math.abs(close - lastResistance)

atrVal = ta.atr(atrLength)
nearSupport = not na(lastSupport) and distToSupport <= srThresholdATR * atrVal
nearResistance = not na(lastResistance) and distToResistance <= srThresholdATR * atrVal

srConditionLong  = (not enableSRFilter) or nearSupport
srConditionShort = (not enableSRFilter) or nearResistance

plot(enableSRFilter ? lastSupport : na, title="Support", color=color.green, style=plot.style_linebr, linewidth=2)
plot(enableSRFilter ? lastResistance : na, title="Resistance", color=color.red, style=plot.style_linebr, linewidth=2)

// === Position sizing ===
accountEquity = strategy.equity
riskValue = accountEquity * (riskPercent / 100)
longStopDist = atr * atrMultiplier
shortStopDist = atr * atrMultiplier

longQty = riskValue / longStopDist
shortQty = riskValue / shortStopDist

RR_long  = useDynamicRR ? dynRiskReward : riskReward
RR_short = useDynamicRR ? dynRiskReward : riskReward

pipValue = syminfo.mintick
limitPriceLong  = close - (entryOffsetPips * pipValue)
limitPriceShort = close + (entryOffsetPips * pipValue)

// === Entry Logic ===
longRevert  = allowedSession and not coolDownActive and adxCondition and trendConditionLong  and candleConditionLong  and rsiDivConditionLong  and close < lowerBand and rsi < rsiOversold and spreadOK
shortRevert = allowedSession and not coolDownActive and adxCondition and trendConditionShort and candleConditionShort and rsiDivConditionShort and close > upperBand and rsi > rsiOverbought and spreadOK
longTrend   = allowedSession and not coolDownActive and close > upperBand and adx > trendADXMin and spreadOK
shortTrend  = allowedSession and not coolDownActive and close < lowerBand and adx > trendADXMin and spreadOK

longEntry  = longRevert
shortEntry = shortRevert

if (enableHybridMode)
    longEntry  := (isRanging and longRevert) or (isTrending and longTrend)
    shortEntry := (isRanging and shortRevert) or (isTrending and shortTrend)

longEntry  := longEntry  and srConditionLong and volatilityCondition
shortEntry := shortEntry and srConditionShort and volatilityCondition

// === SL & TP ===
sl_long = close - longStopDist
tp_long = close + (close - sl_long) * RR_long
sl_short = close + shortStopDist
tp_short = close - (sl_short - close) * RR_short

// === Breakeven Conditions ===
// (Breakeven logic now evaluated directly inside strategy.exit for dynamic recalculation)

// === Order Tracking ===
var int longOrderBar = na
var int shortOrderBar = na

var line longSLLine = na
var line longTPLine = na
var line shortSLLine = na
var line shortTPLine = na

var label longSLLabel = na
var label longTPLabel = na
var label shortSLLabel = na
var label shortTPLabel = na
plotchar(sl_long, char = "")
plotchar(tp_long, char = "")
plotchar(sl_short, char = "")
plotchar(tp_short, char = "")
plotchar(strategy.equity, char = "")
// === Prevent Duplicate Orders at Same Bar ===
var int lastLongEntryBar = na
var int lastShortEntryBar = na

// === Place Orders ===
if (longEntry and (na(lastLongEntryBar) or bar_index > lastLongEntryBar) and strategy.opentrades == 0)
    if (useLimitOrders)
        strategy.order("Long", strategy.long, qty=longQty, limit=limitPriceLong, comment="TP:" + str.tostring(tp_long, format.mintick) +
                   " SL:" + str.tostring(sl_long, format.mintick) +
                   " EQ:" + str.tostring(strategy.equity, format.mintick))
        strategy.exit("Exit Long", "Long", stop=sl_long, limit=tp_long)
        longOrderBar := bar_index
        label.new(bar_index, low, "🟢 Long Limit", color=color.green, style=label.style_label_up, size=size.small)
    else
        if strategy.opentrades == 0
            strategy.entry("Long", strategy.long, qty=longQty, comment="TP:" + str.tostring(tp_long, format.mintick) + " SL:" + str.tostring(sl_long, format.mintick) + " EQ:" + str.tostring(strategy.equity, format.mintick))
            strategy.exit("Exit Long", "Long", stop=sl_long, limit=tp_long)
    lastTradeBar := bar_index
    lastLongEntryBar := bar_index

if (shortEntry and (na(lastShortEntryBar) or bar_index > lastShortEntryBar) and strategy.opentrades == 0)
    if (useLimitOrders)
        strategy.order("Short", strategy.short, qty=shortQty, limit=limitPriceShort, comment="TP:" + str.tostring(tp_short, format.mintick) +
                   " SL:" + str.tostring(sl_short, format.mintick) +
                   " EQ:" + str.tostring(strategy.equity, format.mintick))
        strategy.exit("Exit Short", "Short", stop=sl_short, limit=tp_short)
        shortOrderBar := bar_index
        label.new(bar_index, high, "🔴 Short Limit", color=color.red, style=label.style_label_down, size=size.small)
    else
        if strategy.opentrades == 0
            strategy.entry("Short", strategy.short, qty=shortQty, comment="TP:" + str.tostring(tp_short, format.mintick) + " SL:" + str.tostring(sl_short, format.mintick) + " EQ:" + str.tostring(strategy.equity, format.mintick))
            strategy.exit("Exit Short", "Short", stop=sl_short, limit=tp_short)
    lastTradeBar := bar_index
    lastShortEntryBar := bar_index


// === Breakeven Exit Logic (Corrected: overlays original SL/TP logic) ===
if enableBreakeven and strategy.position_size > 0
    breakEvenLong = close >= strategy.position_avg_price * (1 + breakevenTrigger)
    if breakEvenLong
        strategy.exit(id="Exit Long BE", from_entry="Long", stop=strategy.position_avg_price, limit=tp_long, comment="BE Long")

if enableBreakeven and strategy.position_size < 0
    breakEvenShort = close <= strategy.position_avg_price * (1 - breakevenTrigger)
    if breakEvenShort
        strategy.exit(id="Exit Short BE", from_entry="Short", stop=strategy.position_avg_price, limit=tp_short, comment="BE Short")

// === Reset tracking ===
if (strategy.position_size > 0)
    longOrderBar := na
if (strategy.position_size < 0)
    shortOrderBar := na

// === Timeout cancel ===
if (useLimitOrders)
    if (not na(longOrderBar) and strategy.position_size == 0 and bar_index - longOrderBar >= limitOrderTimeout)
        strategy.cancel("Long")
        lastLongEntryBar := bar_index
        label.new(bar_index, low, "⚪️ Long Cancel", color=color.white, style=label.style_label_up, size=size.tiny)
        longOrderBar := na
    if (not na(shortOrderBar) and strategy.position_size == 0 and bar_index - shortOrderBar >= limitOrderTimeout)
        strategy.cancel("Short")
        lastShortEntryBar := bar_index
        label.new(bar_index, high, "⚪️ Short Cancel", color=color.white, style=label.style_label_down, size=size.tiny)
        shortOrderBar := na

// === TP/SL Lines ===
if (strategy.position_size > 0)
    entry = strategy.position_avg_price
    longSL = entry - atr * atrMultiplier
    longTP = entry + (entry - longSL) * RR_long
    if na(longSLLine)
        longSLLine := line.new(bar_index, longSL, bar_index+1, longSL, color=color.red, style=line.style_dashed, width=2, extend=extend.right)
        longTPLine := line.new(bar_index, longTP, bar_index+1, longTP, color=color.green, style=line.style_dashed, width=2, extend=extend.right)
    line.set_y1(longSLLine, longSL)
    line.set_y2(longSLLine, longSL)
    line.set_y1(longTPLine, longTP)
    line.set_y2(longTPLine, longTP)
    line.set_x2(longSLLine, bar_index+1)
    line.set_x2(longTPLine, bar_index+1)
    
    if (showTP_SL_Labels)
        pipDistSL = (entry - longSL) / syminfo.mintick
        pipDistTP = (longTP - entry) / syminfo.mintick
        if na(longSLLabel)
            longSLLabel := label.new(bar_index, longSL, "SL\n" + str.tostring(longSL, format.mintick) + "\n" + str.tostring(pipDistSL, "#") + " pips", 
                                     color=color.red, style=label.style_label_left, textcolor=color.white, size=size.tiny)
        else
            label.set_xy(longSLLabel, bar_index, longSL)
            label.set_text(longSLLabel, "SL\n" + str.tostring(longSL, format.mintick) + "\n" + str.tostring(pipDistSL, "#") + " pips")
        if na(longTPLabel)
            longTPLabel := label.new(bar_index, longTP, "TP\n" + str.tostring(longTP, format.mintick) + "\n" + str.tostring(pipDistTP, "#") + " pips", 
                                     color=color.green, style=label.style_label_left, textcolor=color.white, size=size.tiny)
        else
            label.set_xy(longTPLabel, bar_index, longTP)
            label.set_text(longTPLabel, "TP\n" + str.tostring(longTP, format.mintick) + "\n" + str.tostring(pipDistTP, "#") + " pips")

if (strategy.position_size < 0)
    entry = strategy.position_avg_price
    shortSL = entry + atr * atrMultiplier
    shortTP = entry - (shortSL - entry) * RR_short
    if na(shortSLLine)
        shortSLLine := line.new(bar_index, shortSL, bar_index+1, shortSL, color=color.red, style=line.style_dashed, width=2, extend=extend.right)
        shortTPLine := line.new(bar_index, shortTP, bar_index+1, shortTP, color=color.green, style=line.style_dashed, width=2, extend=extend.right)
    line.set_y1(shortSLLine, shortSL)
    line.set_y2(shortSLLine, shortSL)
    line.set_y1(shortTPLine, shortTP)
    line.set_y2(shortTPLine, shortTP)
    line.set_x2(shortSLLine, bar_index+1)
    line.set_x2(shortTPLine, bar_index+1)
    
    if (showTP_SL_Labels)
        pipDistSL = (shortSL - entry) / syminfo.mintick
        pipDistTP = (entry - shortTP) / syminfo.mintick
        if na(shortSLLabel)
            shortSLLabel := label.new(bar_index, shortSL, "SL\n" + str.tostring(shortSL, format.mintick) + "\n" + str.tostring(pipDistSL, "#") + " pips", 
                                      color=color.red, style=label.style_label_left, textcolor=color.white, size=size.tiny)
        else
            label.set_xy(shortSLLabel, bar_index, shortSL)
            label.set_text(shortSLLabel, "SL\n" + str.tostring(shortSL, format.mintick) + "\n" + str.tostring(pipDistSL, "#") + " pips")
        if na(shortTPLabel)
            shortTPLabel := label.new(bar_index, shortTP, "TP\n" + str.tostring(shortTP, format.mintick) + "\n" + str.tostring(pipDistTP, "#") + " pips", 
                                      color=color.green, style=label.style_label_left, textcolor=color.white, size=size.tiny)
        else
            label.set_xy(shortTPLabel, bar_index, shortTP)
            label.set_text(shortTPLabel, "TP\n" + str.tostring(shortTP, format.mintick) + "\n" + str.tostring(pipDistTP, "#") + " pips")

// === Delete lines & labels when flat ===
if (strategy.position_size == 0)
    if not na(longSLLine)
        line.delete(longSLLine)
        longSLLine := na
    if not na(longTPLine)
        line.delete(longTPLine)
        longTPLine := na
    if not na(shortSLLine)
        line.delete(shortSLLine)
        shortSLLine := na
    if not na(shortTPLine)
        line.delete(shortTPLine)
        shortTPLine := na

    if not na(longSLLabel)
        label.delete(longSLLabel)
        longSLLabel := na
    if not na(longTPLabel)
        label.delete(longTPLabel)
        longTPLabel := na
    if not na(shortSLLabel)
        label.delete(shortSLLabel)
        shortSLLabel := na
    if not na(shortTPLabel)
        label.delete(shortTPLabel)
        shortTPLabel := na

// === Plots ===
plot(basis, color=color.blue, title="BB Basis")
plot(upperBand, color=color.red, title="BB Upper")
plot(lowerBand, color=color.green, title="BB Lower")
plot(adx, title="ADX", color=color.orange)
hline(adxThreshold, "ADX Threshold", color=color.gray, linestyle=hline.style_dotted)
plot(htf_basis, color=color.purple, title="HTF Bollinger Basis")
plot(bandWidth, title="Bollinger Band Width", color=color.fuchsia)