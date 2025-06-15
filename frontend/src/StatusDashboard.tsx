import { useEffect, useState } from "react";

interface SymbolStatus {
  bid_price: number;
  ask_price: number;
  timestamp_ns: number;
  consumer_id: string;
}

const subs: Record<string, number> = {
  adausdt: 50,
  avaxusdt: 170,
  bnbusdt: 258,
  btcusdt: 290,
  dogeusdt: 388,
  ethfiusdt: 469,
  ethusdt: 476,
  hyperusdt: 604,
  linkusdt: 721,
  shibusdt: 1101,
  solusdt: 1132,
  solvusdt: 1136,
  suiusdt: 1178,
  trxusdt: 1258,
  usdcusdt: 1288,
  wbtcusdt: 1341,
  xlmusdt: 1380,
  xrpusdt: 1394,
};

export default function StatusDashboard() {
  const [symbolData, setSymbolData] = useState<Record<string, SymbolStatus>>({});

  // Initialize rows with config
  useEffect(() => {
    const initial: Record<string, SymbolStatus> = {};
    Object.keys(subs).forEach((symbol) => {
      initial[symbol] = {
        bid_price: 0,
        ask_price: 0,
        timestamp_ns: 0,
        consumer_id: "",
      };
    });
    setSymbolData(initial);
  }, []);

  // Fetch updates every second
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://localhost:8000/status/latest");
        const updates = await res.json();
        setSymbolData((prev) => {
          const next = { ...prev };
          for (const update of updates) {
            if (next[update.symbol]) {
              next[update.symbol] = {
                bid_price: update.bid_price,
                ask_price: update.ask_price,
                timestamp_ns: update.timestamp_ns,
                consumer_id: update.consumer_id,
              };
            }
          }
          return next;
        });
      } catch (err) {
        console.error("Error fetching status:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (ns: number) => {
    if (!ns) return "-";
    const date = new Date(ns / 1_000_000);
    return date.toISOString().replace("T", " ").slice(0, -5);
  };

return (
  <div className="min-h-screen bg-slate-200 flex items-center justify-center p-4">
    <div className="w-full max-w-6xl bg-slate-100 rounded-xl shadow-lg p-4">
      <h1 className="text-lg font-semibold mb-4 text-center text-gray-800">
        📡 Live Market Data
      </h1>
      <div className="overflow-x-auto max-h-[80vh] overflow-y-auto rounded border border-gray-300">
        <table className="text-xs text-gray-700 w-auto">
          <thead className="sticky top-0 bg-slate-300 text-left">
            <tr>
              <th className="p-2 border border-gray-300">Symbol</th>
              <th className="p-2 border border-gray-300">Consumer</th>
              <th className="p-2 border border-gray-300">Timestamp</th>
              <th className="p-2 text-right border border-gray-300">Bid</th>
              <th className="p-2 text-right border border-gray-300">Ask</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(subs).map((symbol) => {
              const row = symbolData[symbol];
              return (
                <tr key={symbol} className="hover:bg-slate-200">
                  <td className="p-2 border border-gray-300 font-mono uppercase">{symbol}</td>
                  <td className="p-2 border border-gray-300">{row?.consumer_id || "-"}</td>
                  <td className="p-2 border border-gray-300">{formatTime(row?.timestamp_ns)}</td>
                  <td className="p-2 border border-gray-300 text-right">
                    {row?.bid_price?.toFixed(4) || "-"}
                  </td>
                  <td className="p-2 border border-gray-300 text-right">
                    {row?.ask_price?.toFixed(4) || "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);


}

