#include <Zmq/Zmq.mqh>
#include <Trade\SymbolInfo.mqh>

extern string PROJECT_NAME = "TradeServer";
extern string ZEROMQ_PROTOCOL = "tcp";
extern string HOSTNAME = "*";
extern int REP_PORT = 10000;
extern int MILLISECOND_TIMER = 1;  // 1 millisecond

extern string t0 = "--- Trading Parameters ---";
extern int MagicNumber = 123456;


#include <Trade\Trade.mqh>
CTrade trade;

// CREATE ZeroMQ Context
Context context(PROJECT_NAME);

// CREATE ZMQ_REP SOCKET
Socket repSocket(context,ZMQ_REP);

// VARIABLES FOR LATER
uchar myData[];
ZmqMsg request;


int OnInit()
{
    EventSetMillisecondTimer(MILLISECOND_TIMER);     // Set Millisecond Timer to get client socket input
    repSocket.bind(StringFormat("%s://%s:%d", ZEROMQ_PROTOCOL, HOSTNAME, REP_PORT));
    repSocket.setLinger(1000);  // 1000 milliseconds
    repSocket.setSendHighWaterMark(99);     // 5 messages only.

    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
    repSocket.unbind(StringFormat("%s://%s:%d", ZEROMQ_PROTOCOL, HOSTNAME, REP_PORT));
}

void OnTimer()
{
    repSocket.recv(request,true);
    MessageHandler(request);
}

void MessageHandler(ZmqMsg &localRequest)
{

    ZmqMsg reply;
    string components[];


    if(localRequest.size() > 0) {


        ArrayResize(myData, localRequest.size());
        localRequest.getData(myData);
        string dataStr = CharArrayToString(myData);
        ParseZmqMessage(dataStr, components);
        InterpretZmqMessage(components);

    }
}

ENUM_TIMEFRAMES TFMigrate(int tf)
{
    switch(tf)
    {
        case 0: return(PERIOD_CURRENT);
        case 1: return(PERIOD_M1);
        case 5: return(PERIOD_M5);
        case 15: return(PERIOD_M15);
        case 30: return(PERIOD_M30);
        case 60: return(PERIOD_H1);
        case 240: return(PERIOD_H4);
        case 1440: return(PERIOD_D1);
        case 10080: return(PERIOD_W1);
        case 43200: return(PERIOD_MN1);

        case 2: return(PERIOD_M2);
        case 3: return(PERIOD_M3);
        case 4: return(PERIOD_M4);
        case 6: return(PERIOD_M6);
        case 10: return(PERIOD_M10);
        case 12: return(PERIOD_M12);
        case 16385: return(PERIOD_H1);
        case 16386: return(PERIOD_H2);
        case 16387: return(PERIOD_H3);
        case 16388: return(PERIOD_H4);
        case 16390: return(PERIOD_H6);
        case 16392: return(PERIOD_H8);
        case 16396: return(PERIOD_H12);
        case 16408: return(PERIOD_D1);
        case 32769: return(PERIOD_W1);
        case 49153: return(PERIOD_MN1);
        default: return(PERIOD_CURRENT);
    }
}





void InterpretZmqMessage(string& compArray[])
{
    Print("ZMQ: Interpreting..");



    int switch_action = 0;
    string volume;

    if (compArray[0] == "OPEN")
        switch_action = 1;
    else if (compArray[0] == "RATES")
        switch_action = 2;
    else if (compArray[0] == "CLOSE")
        switch_action = 3;
    else if (compArray[0] == "DATA")
        switch_action = 4;
    else if (compArray[0] == "BOOK")
        switch_action = 5;
    else if (compArray[0] == "LAST")
        switch_action = 6;
    else if (compArray[0] == "OPENBOOK")
        switch_action = 7;



    string ret = "";
    int ticket = -1;
    bool ans = false;

    MqlRates rates[];
    //ArraySetAsSeries(rates, true);

    int price_count = 0;

    ZmqMsg msg("[SERVER] Processing");
    Print("switch_actions :  " + switch_action);

    string _order;

    switch(switch_action){

        case 1:
            //  0      1     2     3       4        5
            //OPEN|TYPE|SYMBOL|STOPLOSS|STOPGAIN|VOLUME

            _order = OrderPlacer(StringToInteger(compArray[1]),
                                 compArray[2],
                                 StringToDouble(compArray[3]),
                                 StringToDouble(compArray[4]),
                                 StringToDouble(compArray[5]));


            Print("ORDER : ",_order);
            repSocket.send(_order, false);


        break;
        case 7:
            //  0      1     2     3       4        5      6
            //OPEN|TYPE|SYMBOL|PRICE|STOPLOSS|STOPGAIN|VOLUME

            _order = BookPlacer(StringToInteger(compArray[1]),
                                 compArray[2],
                                 StringToDouble(compArray[3]),
                                 StringToDouble(compArray[4]),
                                 StringToDouble(compArray[5]),
                                 StringToDouble(compArray[6]));


            Print("ORDER : ",_order);
            repSocket.send(_order, false);


        break;
        case 2:
            ret = "N/A";
            if(ArraySize(compArray) > 1)
                ret = GetCurrent(compArray[1]);

            repSocket.send(ret, false);

        break;
        case 3:

            //  0     1
            //CLOSE|TICKET
            _order = PosClose(StringToInteger(compArray[1]));
            Print("ORDER : ",_order);
            repSocket.send(_order, false);


        break;
        case 4:
            // Format: DATA|SYMBOL|TIMEFRAME|START_DATETIME|END_DATETIME
            ret = "";
            price_count = CopyRates(
                                    compArray[1],
                                    TFMigrate(StringToInteger(compArray[2])),
                                    StringToTime(compArray[3]),
                                    StringToTime(compArray[4]),
                                    rates
                                  );

            Print("TERMINAL_MAXBARS : "+ IntegerToString(TERMINAL_MAXBARS));
            Print("price_count : " + IntegerToString(price_count));

            if (price_count > 0){

                for(int i = 0; i < price_count; i++ ) {
                      ret = ret + "|" + StringFormat("%s,%.8f,%.8f,%.8f,%.8f,%d,%d",TimeToString(rates[i].time),
                                                                                    rates[i].open,
                                                                                    rates[i].low,
                                                                                    rates[i].high,
                                                                                    rates[i].close,
                                                                                    rates[i].tick_volume,
                                                                                    rates[i].real_volume);
                 }
            }

            Print("Sending: " + ret);
            repSocket.send(ret, false);
            break;
            case 6: // LAST

            // Format: LAST|SYMBOL|STARTPOSITION|COUNT
                ret = "";
                price_count = CopyRates(
                                        compArray[1],
                                        TFMigrate(StringToInteger(compArray[2])),
                                        StringToInteger(compArray[3]),
                                        StringToInteger(compArray[4]),
                                        rates
                                        );

                Print("TERMINAL_MAXBARS : "+ IntegerToString(TERMINAL_MAXBARS));
                Print("price_count : " + IntegerToString(price_count));

                if(price_count > 0){

                    for(int i = 0; i < price_count; i++){

                      ret = ret + "|" + StringFormat("%s,%.8f,%.8f,%.8f,%.8f,%d,%d",TimeToString(rates[i].time),
                                                                                    rates[i].open,
                                                                                    rates[i].low,
                                                                                    rates[i].high,
                                                                                    rates[i].close,
                                                                                    rates[i].tick_volume,
                                                                                    rates[i].real_volume);
                    }
                }

                Print("Sending: " + ret);
                repSocket.send(ret, false);
                break;

        default:
            break;
    }
}

void ParseZmqMessage(string& message, string& retArray[])
{
    Print("Parsing: " + message);
    string sep = "|";
    ushort u_sep = StringGetCharacter(sep,0);
    int splits = StringSplit(message, u_sep, retArray);
    for(int i = 0; i < splits; i++) {
        Print(IntegerToString(i) + ") " + retArray[i]);
    }
}

string GetVolume(string symbol, datetime start_time, datetime stop_time)
{
    long volume_array[1];
    CopyRealVolume(symbol, PERIOD_M1, start_time, stop_time, volume_array);

    return(StringFormat("%d", volume_array[0]));
}

string GetCurrent(string symbol)
{
    MqlTick Last_tick;
    MqlBookInfo bookArray[];

    SymbolInfoTick(symbol,Last_tick);

    double bid = Last_tick.bid;
    double ask = Last_tick.ask;

    bool getBook = MarketBookGet(symbol,bookArray);


    long buy_volume = 0;
    long sell_volume = 0;
    long buy_volume_market = 0;
    long sell_volume_market = 0;


    if (getBook) {
       for (int i =0; i < ArraySize(bookArray); i++ )
       {
            if (bookArray[i].type == BOOK_TYPE_SELL)
               sell_volume += bookArray[i].volume_real;
            else if (bookArray[i].type == BOOK_TYPE_BUY)
               buy_volume += bookArray[i].volume_real;
            else if (bookArray[i].type == BOOK_TYPE_BUY_MARKET)
               buy_volume_market += bookArray[i].volume_real;
            else
               sell_volume_market += bookArray[i].volume_real;
       }
    }

    long tick_volume = Last_tick.volume;
    long real_volume = Last_tick.volume_real;
    MarketBookAdd(symbol);

    string p;
    static datetime dTime = Last_tick.time;
    int size = ArraySize(bookArray);

    p = StringFormat(", %.8f, %.8f\n", bid, ask);

    //
    //for(int i = 0; i<size-1; i++){
    //  StringAdd(p, StringFormat("%d, %.2f, %f\n", bookArray[i].type, bookArray[i].price, bookArray[i].volume_real));
    //}

    return(p);
   // return(StringFormat("%.2f,%.2f,%d,%d,%d,%d,%d,%d", bid, ask, buy_volume, sell_volume, tick_volume, real_volume, buy_volume_market, sell_volume_market));
}
string GetBook(string symbol)
{
    MqlTick Last_tick;
    MqlBookInfo bookArray[];

    SymbolInfoTick(symbol,Last_tick);

    double bid = Last_tick.bid;
    double ask = Last_tick.ask;

    bool getBook = MarketBookGet(symbol,bookArray);


    long buy_volume = 0;
    long sell_volume = 0;
    long buy_volume_market = 0;
    long sell_volume_market = 0;


    if (getBook) {
       for (int i =0; i < ArraySize(bookArray); i++ )
       {
            if (bookArray[i].type == BOOK_TYPE_SELL)
               sell_volume += bookArray[i].volume_real;
            else if (bookArray[i].type == BOOK_TYPE_BUY)
               buy_volume += bookArray[i].volume_real;
            else if (bookArray[i].type == BOOK_TYPE_BUY_MARKET)
               buy_volume_market += bookArray[i].volume_real;
            else
               sell_volume_market += bookArray[i].volume_real;
       }
    }

    long tick_volume = Last_tick.volume;
    long real_volume = Last_tick.volume_real;
    MarketBookAdd(symbol);

    string p;
    static datetime dTime = Last_tick.time;
    int size = ArraySize(bookArray);

    p = StringFormat(", %.8f, %.8f\n", bid, ask);


    for(int i = 0; i<size-1; i++){
    StringAdd(p, StringFormat("%d, %.8f, %f\n", bookArray[i].type, bookArray[i].price, bookArray[i].volume_real));
    }

    return(StringFormat("%.8f,%.8f,%d,%d,%d,%d,%d,%d", bid, ask, buy_volume, sell_volume, tick_volume, real_volume, buy_volume_market, sell_volume_market));
}



string PosClose(ulong ticket){

   Print(ticket);

   MqlTradeResult trade_result;
   int __posclose = trade.PositionClose(ticket);

   trade.Result(trade_result);

   string _ret;

   _ret = StringFormat("%i, %f, %f, %f, %f",__posclose, trade_result.price, trade_result.ask, trade_result.bid, trade_result.volume);

   return _ret;

}

string OrderPlacer(int type,
                string symbol,
                double stoploss,
                double takeprofit,
                double volume)
   {


   stoploss = NormalizeDouble(stoploss, _Digits);
   takeprofit = NormalizeDouble(takeprofit, _Digits);

   string _ret;

   //buy
   if(type == 1){

   double ask = NormalizeDouble(SymbolInfoDouble(symbol, SYMBOL_ASK), _Digits);
   Print(symbol,ask);
   MqlTradeResult trade_result;

   trade.Buy(volume,
             symbol,
             ask,
             stoploss,
             takeprofit,
             NULL
             );

    trade.Result(trade_result);

   _ret = StringFormat("%i, %f, %f, %f, %f", trade.ResultOrder(), trade.RequestPrice(), trade_result.ask, trade_result.bid, trade_result.volume);
   Print("BUY : ",_ret);
   return(_ret);


   }
   //sell
   if(type == -1){

   double bid = NormalizeDouble(SymbolInfoDouble(symbol, SYMBOL_BID), _Digits);
   Print(symbol,bid);
   MqlTradeResult trade_result;

   trade.Sell(volume,
             symbol,
             bid,
             stoploss,
             takeprofit,
             NULL
             );

   trade.Result(trade_result);
   _ret = StringFormat("%i, %f, %f, %f, %f", trade.ResultOrder(), trade.RequestPrice(), trade_result.ask, trade_result.bid, trade_result.volume);
   Print("SELL : ",_ret);
   return(_ret);

   }

   return "NULL";

}

string BookPlacer(int type,
                string symbol,
                double price,
                double stoploss,
                double takeprofit,
                double volume)
   {


   stoploss = NormalizeDouble(stoploss, _Digits);
   takeprofit = NormalizeDouble(takeprofit, _Digits);

   string _ret;

   //buy
   if(type == 1){

   double ask = NormalizeDouble(SymbolInfoDouble(symbol, SYMBOL_ASK), _Digits);
   Print(symbol,ask);
   MqlTradeResult trade_result;

   trade.Buy(volume,
             symbol,
             price,
             stoploss,
             takeprofit,
             NULL
             );

    trade.Result(trade_result);

   _ret = StringFormat("%i, %f, %f, %f, %f", trade.ResultOrder(), trade.RequestPrice(), trade_result.ask, trade_result.bid, trade_result.volume);
   Print("BUY : ",_ret);
   return(_ret);


   }
   //sell
   if(type == -1){

   double bid = NormalizeDouble(SymbolInfoDouble(symbol, SYMBOL_BID), _Digits);
   Print(symbol,bid);
   MqlTradeResult trade_result;

   trade.Sell(volume,
             symbol,
             price,
             stoploss,
             takeprofit,
             NULL
             );

   trade.Result(trade_result);
   _ret = StringFormat("%i, %f, %f, %f, %f", trade.ResultOrder(), trade.RequestPrice(), trade_result.ask, trade_result.bid, trade_result.volume);
   Print("SELL : ",_ret);
   return(_ret);

   }

   return "NULL";

}
