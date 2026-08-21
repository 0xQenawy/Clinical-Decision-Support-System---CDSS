import React, { useState } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  Stethoscope, 
  Syringe, 
  Pill, 
  ShieldAlert,
  Search,
  Loader2,
  Check
} from 'lucide-react';

export default function App() {
  // Form State
  const [tumorType, setTumorType] = useState('Non-Small Cell Lung Cancer');
  
  // Structured Biomarkers
  const commonMutations = ["EGFR (Exon 19/L858R)", "ALK fusion", "ROS1", "KRAS G12C", "BRAF V600E"];
  const [selectedMutations, setSelectedMutations] = useState([]);
  const [pdl1, setPdl1] = useState('Unknown');
  
  // ECOG Status
  const ecogOptions = [
    "0 - Fully active",
    "1 - Restricted in strenuous activity",
    "2 - Ambulatory, capable of self-care",
    "3 - Limited self-care, confined to bed/chair",
    "4 - Completely disabled"
  ];
  const [ecog, setEcog] = useState(ecogOptions[0]);

  // Vitals / Labs
  const [egfr, setEgfr] = useState(35);
  const [altAst, setAltAst] = useState(45);
  
  // Structured Comorbidities
  const commonComorbidities = ["Autoimmune Disease", "Interstitial Lung Disease (ILD)", "QTc Prolongation", "Hepatic Impairment"];
  const [selectedComorbidities, setSelectedComorbidities] = useState([]);
  const [hasOtherComorbidity, setHasOtherComorbidity] = useState(false);
  const [otherComorbidityText, setOtherComorbidityText] = useState('');

  // App State
  const [isGenerating, setIsGenerating] = useState(false);
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState(null);
  const [showRationale, setShowRationale] = useState(false);

  const toggleMutation = (mutation) => {
    setSelectedMutations(prev => 
      prev.includes(mutation) ? prev.filter(m => m !== mutation) : [...prev, mutation]
    );
  };

  const toggleComorbidity = (comorbidity) => {
    setSelectedComorbidities(prev => 
      prev.includes(comorbidity) ? prev.filter(c => c !== comorbidity) : [...prev, comorbidity]
    );
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setError(null);
    setAiData(null);
    setShowRationale(false);

    // Combine structured inputs into payload arrays
    const finalBiomarkers = [...selectedMutations];
    if (pdl1 !== 'Unknown') {
      finalBiomarkers.push(`PD-L1: ${pdl1}`);
    }

    const finalComorbidities = [...selectedComorbidities];
    if (hasOtherComorbidity && otherComorbidityText.trim()) {
      finalComorbidities.push(otherComorbidityText.trim());
    }

    // Prepare payload matching FastAPI Pydantic model
    const payload = {
      tumor_type: tumorType,
      biomarkers: finalBiomarkers,
      ecog_status: ecog,
      egfr: egfr ? parseInt(egfr) : null,
      alt_ast: altAst ? parseInt(altAst) : null,
      comorbidities: finalComorbidities
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/api/generate-protocol', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate protocol');
      }

      const data = await response.json();
      setAiData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Precision Oncology <span className="text-blue-600 font-medium">CDSS</span>
            </h1>
          </div>
          <div className="flex items-center space-x-2 text-sm text-slate-500 font-medium bg-slate-100 px-3 py-1.5 rounded-full">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span>API Connected</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT COLUMN: Patient Input Form */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <div className="flex items-center space-x-2 mb-6 border-b border-slate-100 pb-4">
                <Stethoscope className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-bold text-slate-900">Clinical Profile</h2>
              </div>

              <form onSubmit={handleGenerate} className="space-y-6">
                
                {/* Tumor Type */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Tumor Type</label>
                  <input 
                    type="text" 
                    required
                    value={tumorType}
                    onChange={(e) => setTumorType(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors outline-none text-sm"
                    placeholder="e.g. Non-Small Cell Lung Cancer"
                  />
                </div>

                {/* ECOG Status */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">ECOG Performance Status</label>
                  <select 
                    value={ecog}
                    onChange={(e) => setEcog(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors outline-none text-sm appearance-none cursor-pointer"
                  >
                    {ecogOptions.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>

                {/* Biomarkers */}
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <label className="block text-sm font-semibold text-slate-900 mb-3">Oncogenic Drivers & Biomarkers</label>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {commonMutations.map(mutation => (
                      <label key={mutation} className="flex items-start space-x-2 cursor-pointer group">
                        <div className="relative flex items-center justify-center w-5 h-5 border border-slate-300 rounded mt-0.5 bg-white group-hover:border-blue-500 transition-colors">
                          <input 
                            type="checkbox" 
                            className="sr-only"
                            checked={selectedMutations.includes(mutation)}
                            onChange={() => toggleMutation(mutation)}
                          />
                          {selectedMutations.includes(mutation) && <Check className="w-3.5 h-3.5 text-blue-600" strokeWidth={3} />}
                        </div>
                        <span className="text-sm text-slate-700 font-medium group-hover:text-slate-900">{mutation}</span>
                      </label>
                    ))}
                  </div>

                  <div className="pt-3 border-t border-slate-200">
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">PD-L1 Expression</label>
                    <select 
                      value={pdl1}
                      onChange={(e) => setPdl1(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors outline-none text-sm cursor-pointer"
                    >
                      <option value="Unknown">Unknown</option>
                      <option value="< 1%">&lt; 1%</option>
                      <option value="1% - 49%">1% - 49%</option>
                      <option value="≥ 50%">≥ 50%</option>
                    </select>
                  </div>
                </div>

                {/* Labs */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">eGFR <span className="text-slate-400 font-normal">(mL/min)</span></label>
                    <input 
                      type="number" 
                      value={egfr}
                      onChange={(e) => setEgfr(e.target.value)}
                      className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors outline-none text-sm"
                      placeholder="e.g. 60"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">ALT/AST <span className="text-slate-400 font-normal">(U/L)</span></label>
                    <input 
                      type="number" 
                      value={altAst}
                      onChange={(e) => setAltAst(e.target.value)}
                      className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors outline-none text-sm"
                      placeholder="e.g. 40"
                    />
                  </div>
                </div>

                {/* Comorbidities */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-3">Relevant Comorbidities</label>
                  <div className="flex flex-col space-y-2.5">
                    {commonComorbidities.map(comorbidity => (
                      <label key={comorbidity} className="flex items-center space-x-2.5 cursor-pointer group">
                         <div className="relative flex items-center justify-center w-5 h-5 border border-slate-300 rounded bg-white group-hover:border-blue-500 transition-colors">
                          <input 
                            type="checkbox" 
                            className="sr-only"
                            checked={selectedComorbidities.includes(comorbidity)}
                            onChange={() => toggleComorbidity(comorbidity)}
                          />
                          {selectedComorbidities.includes(comorbidity) && <Check className="w-3.5 h-3.5 text-blue-600" strokeWidth={3} />}
                        </div>
                        <span className="text-sm text-slate-700 font-medium">{comorbidity}</span>
                      </label>
                    ))}
                    
                    {/* Other Comorbidity */}
                    <div className="pt-1">
                      <label className="flex items-center space-x-2.5 cursor-pointer group">
                        <div className="relative flex items-center justify-center w-5 h-5 border border-slate-300 rounded bg-white group-hover:border-blue-500 transition-colors">
                          <input 
                            type="checkbox" 
                            className="sr-only"
                            checked={hasOtherComorbidity}
                            onChange={() => setHasOtherComorbidity(!hasOtherComorbidity)}
                          />
                          {hasOtherComorbidity && <Check className="w-3.5 h-3.5 text-blue-600" strokeWidth={3} />}
                        </div>
                        <span className="text-sm text-slate-700 font-medium">Other</span>
                      </label>
                      
                      {hasOtherComorbidity && (
                        <input 
                          type="text" 
                          value={otherComorbidityText}
                          onChange={(e) => setOtherComorbidityText(e.target.value)}
                          className="w-full mt-2 px-3 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors outline-none text-sm"
                          placeholder="Please specify..."
                        />
                      )}
                    </div>
                  </div>
                </div>

                <button 
                  type="submit"
                  disabled={isGenerating}
                  className="w-full mt-2 flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 px-4 rounded-xl transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed shadow-sm"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Synthesizing Protocol...</span>
                    </>
                  ) : (
                    <>
                      <Search className="h-5 w-5" />
                      <span>Generate Evidence-Based Protocol</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* RIGHT COLUMN: AI Output Area */}
          <div className="lg:col-span-7 flex flex-col h-full">
            
            {/* Empty State */}
            {!aiData && !isGenerating && !error && (
              <div className="flex-1 bg-white border border-slate-200 border-dashed rounded-2xl flex flex-col items-center justify-center p-12 text-center min-h-[500px]">
                <div className="bg-slate-50 p-4 rounded-full mb-4">
                  <Activity className="h-8 w-8 text-slate-400" />
                </div>
                <h3 className="text-xl font-bold text-slate-700 mb-2">Awaiting Clinical Profile</h3>
                <p className="text-slate-500 max-w-md text-sm leading-relaxed">
                  Select the patient's actionable mutations, PD-L1 expression, and comorbidities to synthesize an NCCN-aligned treatment recommendation.
                </p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-start space-x-3 mb-6">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-sm">Generation Failed</h4>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* Skeleton Loader */}
            {isGenerating && (
              <div className="space-y-4">
                <div className="h-40 bg-slate-200/50 rounded-2xl animate-pulse border border-slate-100"></div>
                <div className="h-28 bg-slate-200/50 rounded-2xl animate-pulse border border-slate-100"></div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="h-32 bg-slate-200/50 rounded-2xl animate-pulse border border-slate-100"></div>
                  <div className="h-32 bg-slate-200/50 rounded-2xl animate-pulse border border-slate-100"></div>
                </div>
              </div>
            )}

            {/* Results Display */}
            {aiData && !isGenerating && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                
                {/* 1. Targeted Therapy Protocol */}
                <div className="bg-white border-l-4 border-l-blue-600 border border-slate-200 rounded-r-2xl rounded-l-md p-6 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                    <Syringe className="w-32 h-32" />
                  </div>
                  <div className="flex items-center justify-between mb-4 relative">
                    <div className="flex items-center space-x-2 text-blue-700">
                      <div className="bg-blue-50 p-1.5 rounded-lg">
                        <Syringe className="h-5 w-5" />
                      </div>
                      <h3 className="font-bold text-lg">Recommended Regimen</h3>
                    </div>
                    <span className={`px-3 py-1.5 text-xs font-bold rounded-full uppercase tracking-wider shadow-sm
                      ${aiData.protocol?.confidence === 'high' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 
                        aiData.protocol?.confidence === 'medium' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                      {aiData.protocol?.confidence} Confidence
                    </span>
                  </div>
                  <p className="text-slate-800 font-medium text-lg mb-4 relative">
                    {aiData.protocol?.treatment}
                  </p>
                  <div className="bg-slate-50 p-3.5 rounded-xl text-sm text-slate-600 border border-slate-200 relative">
                    <div className="flex items-center space-x-1.5 mb-1 text-slate-800 font-semibold">
                      <Activity className="w-4 h-4" />
                      <span>Clinical Monitoring Parameters</span>
                    </div>
                    <p className="pl-5">{aiData.protocol?.monitoring}</p>
                  </div>
                </div>

                {/* 2. Critical Safety Adjustments */}
                <div className={`border-l-4 rounded-r-2xl rounded-l-md p-6 shadow-sm
                  ${aiData.safety_alerts?.severity === 'critical' ? 'bg-red-50/50 border-l-red-500 border-red-100' : 
                    aiData.safety_alerts?.severity === 'warning' ? 'bg-amber-50/50 border-l-amber-500 border-amber-100' : 'bg-slate-50 border-l-slate-400 border-slate-200'}`}>
                  <div className="flex items-center space-x-2 mb-3">
                    <div className={`p-1.5 rounded-lg 
                      ${aiData.safety_alerts?.severity === 'critical' ? 'bg-red-100 text-red-600' : 
                        aiData.safety_alerts?.severity === 'warning' ? 'bg-amber-100 text-amber-600' : 'bg-slate-200 text-slate-600'}`}>
                      <ShieldAlert className="h-5 w-5" />
                    </div>
                    <h3 className={`font-bold text-lg 
                      ${aiData.safety_alerts?.severity === 'critical' ? 'text-red-900' : 
                        aiData.safety_alerts?.severity === 'warning' ? 'text-amber-900' : 'text-slate-900'}`}>
                      Safety & Adjustments
                    </h3>
                  </div>
                  <p className={`text-sm leading-relaxed ${aiData.safety_alerts?.severity === 'critical' ? 'text-red-800 font-medium' : 'text-slate-700'}`}>
                    {aiData.safety_alerts?.alert_text}
                  </p>
                </div>

                {/* 3 & 4. Alternatives & Citations (Side by side) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-2 text-slate-700 mb-3">
                      <div className="bg-slate-100 p-1.5 rounded-lg text-slate-600">
                        <Pill className="h-5 w-5" />
                      </div>
                      <h3 className="font-bold">Alternatives</h3>
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {aiData.alternatives}
                    </p>
                  </div>
                  
                  <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-2 text-slate-700 mb-3">
                      <div className="bg-indigo-50 p-1.5 rounded-lg text-indigo-600">
                        <FileText className="h-5 w-5" />
                      </div>
                      <h3 className="font-bold">Guidelines Sourced</h3>
                    </div>
                    <div className="inline-flex bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-medium border border-indigo-100">
                      {aiData.citations}
                    </div>
                  </div>
                </div>

                {/* 5. Explainable AI Rationale (Expandable) */}
                <div className="mt-4 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden transition-all">
                  <button 
                    onClick={() => setShowRationale(!showRationale)}
                    className="w-full px-6 py-4 flex items-center justify-between bg-slate-50/50 hover:bg-slate-100/80 transition-colors"
                  >
                    <div className="flex items-center space-x-3 text-slate-700">
                      <div className="bg-slate-200/70 p-1.5 rounded-lg text-slate-700">
                        <Search className="h-5 w-5" />
                      </div>
                      <h3 className="font-bold text-slate-800">Explainable AI: Clinical Rationale</h3>
                    </div>
                    {showRationale ? <ChevronUp className="h-5 w-5 text-slate-500" /> : <ChevronDown className="h-5 w-5 text-slate-500" />}
                  </button>
                  
                  {showRationale && (
                    <div className="px-6 py-5 border-t border-slate-200 bg-white">
                      <div className="prose prose-slate prose-sm max-w-none">
                        <p className="text-slate-600 leading-relaxed whitespace-pre-line">
                          {aiData.clinical_rationale}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
