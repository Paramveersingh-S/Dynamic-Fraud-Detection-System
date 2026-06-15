"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { useParams, useRouter } from "next/navigation";
import { ShieldAlert, ArrowLeft, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import Link from "next/link";

export default function CaseDetail() {
  const params = useParams();
  const router = useRouter();
  const [caseData, setCaseData] = useState<any>(null);
  const [decisionMode, setDecisionMode] = useState<"approve"|"decline"|null>(null);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    // In production, use env var
    axios.get(`http://localhost:8080/v1/cases/${params.id}`)
      .then(res => setCaseData(res.data))
      .catch(err => console.error(err));
  }, [params.id]);

  const submitDecision = async () => {
    if (!decisionMode) return;
    try {
      await axios.post(`http://localhost:8080/v1/cases/${params.id}/decision`, {
        decision: decisionMode,
        notes: notes
      });
      router.push("/");
    } catch (err) {
      console.error(err);
    }
  };

  if (!caseData) return <div className="p-8 text-center animate-pulse">Loading case data...</div>;

  // Format SHAP data for Recharts
  const shapData = Object.entries(caseData.shap_explanation).map(([name, value]) => ({
    name,
    value: Number(value),
    color: Number(value) > 0 ? "#FF5E00" : "#00F0FF"
  })).sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div>
          <Link href="/" className="text-blue-400 hover:text-blue-300 flex items-center mb-4 text-sm font-semibold">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Queue
          </Link>
          <h1 className="text-3xl font-bold flex items-center">
            <ShieldAlert className="mr-3 text-orange-500" />
            Case Investigation
          </h1>
          <p className="text-gray-400 mt-2 font-mono text-sm">ID: {caseData.case_id}</p>
        </div>
        
        {/* Quick Decision Actions */}
        <div className="flex gap-4">
          <button 
            onClick={() => setDecisionMode("approve")}
            className="neon-button-approve px-6 py-2 rounded font-bold flex items-center"
          >
            <CheckCircle className="w-5 h-5 mr-2" />
            Approve (Safe)
          </button>
          <button 
            onClick={() => setDecisionMode("decline")}
            className="neon-button-decline px-6 py-2 rounded font-bold flex items-center"
          >
            <XCircle className="w-5 h-5 mr-2" />
            Decline (Fraud)
          </button>
        </div>
      </div>

      {decisionMode && (
        <div className="glass-panel p-6 border-orange-500/30 mb-8 animate-in fade-in slide-in-from-top-4">
          <h3 className="text-xl font-bold mb-4 capitalize">Confirm {decisionMode}</h3>
          <textarea 
            className="w-full bg-gray-900 border border-gray-700 rounded p-4 text-white focus:outline-none focus:border-blue-500 transition-colors"
            rows={3}
            placeholder="Add investigation notes (optional)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="mt-4 flex gap-4">
            <button onClick={submitDecision} className={`px-6 py-2 rounded font-bold ${decisionMode === 'approve' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-red-600 hover:bg-red-500'}`}>
              Submit Final Decision
            </button>
            <button onClick={() => setDecisionMode(null)} className="px-6 py-2 text-gray-400 hover:text-white">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Col: Details */}
        <div className="space-y-8">
          <div className="glass-panel p-6">
            <h2 className="text-xl font-bold mb-4 border-b border-gray-800 pb-2">Transaction Info</h2>
            <div className="space-y-4">
              <div><p className="text-gray-500 text-sm">Amount</p><p className="text-2xl font-bold text-white">${caseData.transaction.amount}</p></div>
              <div><p className="text-gray-500 text-sm">Category</p><p className="text-lg text-blue-300 capitalize">{caseData.transaction.merchant_category}</p></div>
              <div><p className="text-gray-500 text-sm">International</p><p className="text-lg text-orange-300">{caseData.transaction.is_international ? "YES" : "NO"}</p></div>
            </div>
          </div>

          <div className="glass-panel p-6">
            <h2 className="text-xl font-bold mb-4 border-b border-gray-800 pb-2">ML Ensemble Scores</h2>
            <div className="space-y-4">
              <div><p className="text-gray-500 text-sm">XGBoost Probability</p><p className="text-xl neon-text-orange font-mono">{caseData.ml_scores.xgb}</p></div>
              <div><p className="text-gray-500 text-sm">Neural Network Probability</p><p className="text-xl neon-text-orange font-mono">{caseData.ml_scores.nn}</p></div>
              <div><p className="text-gray-500 text-sm">Isolation Forest Anomaly</p><p className="text-xl text-yellow-500 font-mono">{caseData.ml_scores.if}</p></div>
            </div>
          </div>
        </div>

        {/* Right Col: Explainability */}
        <div className="md:col-span-2 space-y-8">
          <div className="glass-panel p-6 h-96">
            <h2 className="text-xl font-bold mb-6">SHAP Values (Model Explainability)</h2>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={shapData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" horizontal={false} />
                <XAxis type="number" stroke="#888" />
                <YAxis dataKey="name" type="category" stroke="#888" width={120} />
                <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                <Bar dataKey="value">
                  {shapData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="glass-panel p-6 border border-red-900/50">
            <h2 className="text-xl font-bold mb-4 text-red-500 flex items-center">
              <AlertTriangle className="mr-2" /> Hard Rules Triggered
            </h2>
            <ul className="list-disc list-inside space-y-2 text-gray-300">
              {caseData.triggered_rules.map((rule: string) => (
                <li key={rule} className="font-mono text-sm">{rule}</li>
              ))}
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}
