@0x85d36655c630fbdf;

struct TradingSignal {
  timestamp @0 :UInt64;
  instrumentId @1 :Text;
  value @2 :Float64;
  metadata @3 :Text;
  
  enum Side {
    none @0;
    buy @1;
    sell @2;
  }
  
  side @4 :Side;
}

struct CustomMarketData {
  timestamp @0 :UInt64;
  price @1 :Float64;
  quantity @2 :Float64;
  venueOrderId @3 :Text;
}
