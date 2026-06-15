"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Activity, AlertTriangle, ShieldCheck, Clock } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [cases, setCases] = useState<any[]>([]);

  useEffect(() => {
    // Dynamically detect Codespace proxy URL to avoid Mixed Content HTTP/HTTPS errors
    const baseUrl = typeof window !== 'undefined' && window.location.hostname.includes('github.dev')
      ? window.location.origin.replace("-3001", "-8080")
      : "http://localhost:8080";
    
    const API_URL = `${baseUrl}/v1`;
    
    Promise.all([
      axios.get(`${API_URL}/analytics/summary`),
      axios.get(`${API_URL}/cases`)
    ]).then(([sumRes, caseRes]) => {
      setSummary(sumRes.data);
      setCases(caseRes.data);
    }).catch(err => console.error("API Error", err));
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      
      <div className="flex justify-between items-center mb-10 border-b border-gray-800 pb-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Investigator <span className="neon-text-blue">Dashboard</span></h1>
          <p className="text-gray-400 mt-2">Real-time meta-learner evaluation queues.</p>
        </div>
        <ShieldCheck className="w-12 h-12 text-blue-400 opacity-50" />
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard 
          title="Fraud Rate (Today)" 
          value={summary ? `${(summary.fraud_rate_today * 100).toFixed(2)}%` : "---"} 
          icon={<AlertTriangle className="text-orange-400" />} 
        />
        <MetricCard 
          title="Cases Resolved" 
          value={summary?.cases_resolved_today || "---"} 
          icon={<Activity className="text-blue-400" />} 
        />
        <MetricCard 
          title="Avg Review Time" 
          value={summary ? `${summary.avg_review_time_mins}m` : "---"} 
          icon={<Clock className="text-emerald-400" />} 
        />
        <MetricCard 
          title="Precision @ Thresh" 
          value={summary ? `${(summary.precision_at_current_threshold * 100).toFixed(1)}%` : "---"} 
          icon={<ShieldCheck className="text-purple-400" />} 
        />
      </div>

      {/* Case Queue */}
      <div className="glass-panel p-6 mt-12">
        <h2 className="text-2xl font-bold mb-6 flex items-center">
          <AlertTriangle className="mr-3 text-orange-500" />
          Active Review Queue
        </h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                <th className="pb-3 pl-4">Case ID</th>
                <th className="pb-3">Priority</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Risk Score</th>
                <th className="pb-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.case_id} className="border-b border-gray-800/50 hover:bg-gray-800/20 transition-colors">
                  <td className="py-4 pl-4 font-mono text-sm">{c.case_id.split('-')[0]}...</td>
                  <td className="py-4">
                    <span className="bg-red-900/40 text-red-400 border border-red-900 px-2 py-1 rounded text-xs font-bold">
                      P{c.priority}
                    </span>
                  </td>
                  <td className="py-4 text-orange-400">{c.status.toUpperCase()}</td>
                  <td className="py-4 font-mono neon-text-orange">{c.fraud_score}</td>
                  <td className="py-4">
                    <Link href={`/cases/${c.case_id}`} className="text-blue-400 hover:text-blue-300 underline text-sm">
                      Review Case
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon }: { title: string, value: string | number, icon: any }) {
  return (
    <div className="glass-panel p-6 flex flex-col justify-between">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-gray-400 text-sm uppercase tracking-wider font-semibold">{title}</h3>
        {icon}
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
