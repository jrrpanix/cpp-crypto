import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface StatusRow {
  id: number;
  bid_price: number;
  ask_price: number;
  timestamp_ns: number;
  consumer_id: string;
}

export default function StatusDashboard() {
  const [data, setData] = useState<StatusRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://localhost:8000/status/latest");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const json = await res.json();
        if (!Array.isArray(json)) throw new Error("Expected JSON array");

        setData(json);
        setError(null);
      } catch (err: any) {
        console.error("Error fetching status:", err);
        setError("Unable to fetch status data. Check the API or network connection.");
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (ns: number) => {
    const date = new Date(ns / 1_000_000);
    return date.toISOString().replace("T", " ").slice(0, -1);
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">📡 Live Market Data</h1>
      {error ? (
        <div className="text-red-600 font-medium mb-4">{error}</div>
      ) : null}
      <Card>
        <CardContent className="overflow-x-auto p-4">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th>Symbol</th>
                <th>Consumer</th>
                <th>Timestamp</th>
                <th>Bid</th>
                <th>Ask</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td>{row.id}</td>
                  <td>{row.consumer_id}</td>
                  <td>{formatTime(row.timestamp_ns)}</td>
                  <td>{row.bid_price.toFixed(2)}</td>
                  <td>{row.ask_price.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

