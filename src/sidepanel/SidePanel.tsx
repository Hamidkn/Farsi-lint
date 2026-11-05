/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Check,
  X,
  Edit2,
  Copy,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Settings,
  Layers,
  Wand2,
  RotateCcw,
} from 'lucide-react';
import { Issue, LLMSettings } from '../shared/types.ts';
import { normalizePersianText } from '../core/normalizer/index.ts';
import { reviewPersianTextWithLLM } from '../core/llm/index.ts';
import { applyIssues, detectConflicts } from '../core/diff/index.ts';
import { loadSettings } from '../shared/storage.ts';

interface SidePanelProps {
  initialText?: string;
  onOpenOptions?: () => void;
  onApplyFixToPage?: (issue: Issue) => void;
}

export const SidePanel: React.FC<SidePanelProps> = ({
  initialText = '',
  onOpenOptions,
}) => {
  const [text, setText] = useState<string>(initialText);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [acceptedIssueIds, setAcceptedIssueIds] = useState<Set<string>>(new Set());
  const [rejectedIssueIds, setRejectedIssueIds] = useState<Set<string>>(new Set());
  const [editingIssueId, setEditingIssueId] = useState<string | null>(null);
  const [customSuggestions, setCustomSuggestions] = useState<Record<string, string>>({});

  const [activeCategoryFilter, setActiveCategoryFilter] = useState<string>('all');
  const [activeLayerFilter, setActiveLayerFilter] = useState<'all' | 'local' | 'llm'>('all');

  // LLM State
  const [isLLMLoading, setIsLLMLoading] = useState<boolean>(false);
  const [llmSummary, setLlmSummary] = useState<string>('');
  const [aiLikelihoodNote, setAiLikelihoodNote] = useState<string>('');
  const [llmError, setLlmError] = useState<string>('');
  const [hasApiKey, setHasApiKey] = useState<boolean>(false);
  const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null);

  const [copied, setCopied] = useState<boolean>(false);

  // Check storage on mount
  useEffect(() => {
    loadSettings().then((s) => {
      setLlmSettings(s.llm);
      setHasApiKey(Boolean(s.llm.apiKey) || s.llm.provider === 'custom');
    });
  }, []);

  // Update text when initialText prop changes
  useEffect(() => {
    if (initialText) {
      setText(initialText);
      runLocalNormalizer(initialText);
    }
  }, [initialText]);

  // Run local normalizer on text change
  const runLocalNormalizer = async (inputText: string) => {
    if (!inputText || inputText.trim().length === 0) {
      setIssues([]);
      return;
    }
    const settings = await loadSettings();
    const localIssues = normalizePersianText(inputText, settings.normalizer);
    setIssues((prev) => {
      // Keep any existing LLM issues, replace local ones
      const currentLlmIssues = prev.filter((i) => i.layer === 'llm');
      const resolved = detectConflicts([...localIssues, ...currentLlmIssues]);
      return resolved;
    });
  };

  const handleTextChange = (newVal: string) => {
    setText(newVal);
    setAcceptedIssueIds(new Set());
    setRejectedIssueIds(new Set());
    runLocalNormalizer(newVal);
  };

  // Run LLM Review
  const handleTriggerLLMReview = async () => {
    if (!text.trim()) return;

    const settings = await loadSettings();
    if (!settings.llm.apiKey && settings.llm.provider !== 'custom') {
      setLlmError('کلید دسترسی (API Key) وارد نشده است. لطفاً به بخش تنظیمات بروید.');
      return;
    }

    setIsLLMLoading(true);
    setLlmError('');

    try {
      const result = await reviewPersianTextWithLLM(text, settings.llm);
      setLlmSummary(result.summaryFa);
      setAiLikelihoodNote(result.aiLikelihoodNoteFa);

      setIssues((prev) => {
        // Keep existing local issues, replace LLM ones
        const currentLocal = prev.filter((i) => i.layer === 'local');
        const resolved = detectConflicts([...currentLocal, ...result.issues]);
        return resolved;
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setLlmError(msg);
    } finally {
      setIsLLMLoading(false);
    }
  };

  // Issue Actions
  const handleAcceptIssue = (issueId: string) => {
    setAcceptedIssueIds((prev) => {
      const next = new Set(prev);
      next.add(issueId);
      return next;
    });
    setRejectedIssueIds((prev) => {
      const next = new Set(prev);
      next.delete(issueId);
      return next;
    });
  };

  const handleRejectIssue = (issueId: string) => {
    setRejectedIssueIds((prev) => {
      const next = new Set(prev);
      next.add(issueId);
      return next;
    });
    setAcceptedIssueIds((prev) => {
      const next = new Set(prev);
      next.delete(issueId);
      return next;
    });
  };

  // Bulk accept for local layer only! (Never bulk accept for LLM)
  const handleAcceptAllLocal = () => {
    const localIssues = issues.filter((i) => i.layer === 'local' && !i.conflict);
    setAcceptedIssueIds((prev) => {
      const next = new Set(prev);
      localIssues.forEach((i) => next.add(i.id));
      return next;
    });
  };

  const handleResetDecisions = () => {
    setAcceptedIssueIds(new Set());
    setRejectedIssueIds(new Set());
  };

  // Calculate corrected text based on accepted issues
  const correctedText = useMemo(() => {
    const issuesToApply = issues
      .filter((i) => acceptedIssueIds.has(i.id))
      .map((i) => {
        if (customSuggestions[i.id]) {
          return { ...i, suggestion: customSuggestions[i.id] };
        }
        return i;
      });

    return applyIssues(text, issuesToApply);
  }, [text, issues, acceptedIssueIds, customSuggestions]);

  const handleCopyCorrected = () => {
    navigator.clipboard.writeText(correctedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter and group issues
  const categories = useMemo(() => {
    const cats: Record<string, number> = {};
    for (const issue of issues) {
      cats[issue.category] = (cats[issue.category] || 0) + 1;
    }
    return cats;
  }, [issues]);

  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      if (activeLayerFilter !== 'all' && issue.layer !== activeLayerFilter) return false;
      if (activeCategoryFilter !== 'all' && issue.category !== activeCategoryFilter) return false;
      return true;
    });
  }, [issues, activeLayerFilter, activeCategoryFilter]);

  const localCount = issues.filter((i) => i.layer === 'local').length;
  const llmCount = issues.filter((i) => i.layer === 'llm').length;

  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-800 font-sans text-sm select-text" dir="rtl">
      {/* Header */}
      <header className="px-4 py-3 bg-white border-b border-slate-200 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
            ف
          </div>
          <div>
            <h1 className="font-bold text-slate-900 leading-tight">فارسی‌لینت</h1>
            <p className="text-[11px] text-slate-500">ویراستار هوشمند زبان فارسی</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {onOpenOptions && (
            <button
              onClick={onOpenOptions}
              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
              title="تنظیمات افزونه"
            >
              <Settings className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Editor Box */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-slate-600">متن برای بررسی:</span>
            <span className="text-[11px] text-slate-400 font-mono">
              {text.length} نویسه • {text.trim() ? text.trim().split(/\s+/).length : 0} واژه
            </span>
          </div>

          <textarea
            value={text}
            onChange={(e) => handleTextChange(e.target.value)}
            placeholder="متن فارسی خود را اینجا بنویسید یا الصاق کنید..."
            rows={4}
            dir="auto"
            className="w-full text-slate-900 text-sm leading-relaxed border-none focus:outline-hidden focus:ring-0 resize-y placeholder:text-slate-400 bg-transparent"
          />
        </div>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={handleTriggerLLMReview}
              disabled={isLLMLoading || !text.trim()}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-xs transition-all ${
                isLLMLoading
                  ? 'bg-blue-100 text-blue-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-98'
              }`}
            >
              {isLLMLoading ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                  <span>در حال بررسی با هوش مصنوعی...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>بازبینی عمیق با هوش مصنوعی</span>
                </>
              )}
            </button>

            {localCount > 0 && (
              <button
                onClick={handleAcceptAllLocal}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                title="فقط خطاهای لایه محلی رسم‌الخط را تأیید می‌کند (پیشنهادات هوش مصنوعی به صورت خودکار اعمال نمی‌شوند)"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>تأیید همه رسم‌الخط</span>
              </button>
            )}
          </div>

          {acceptedIssueIds.size > 0 && (
            <button
              onClick={handleResetDecisions}
              className="text-xs text-slate-500 hover:text-slate-700 underline"
            >
              بازنشانی انتخاب‌ها
            </button>
          )}
        </div>

        {/* API Key Warning if not configured */}
        {!hasApiKey && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">کلید دسترسی (API Key) وارد نشده است.</p>
              <p className="text-[11px] text-amber-700 mt-0.5">
                لایه محلی رسم‌الخط کاملاً رایگان و آفلاین فعال است. برای فعال‌سازی بازبینی ترجمه و نگارش هوش مصنوعی، لطفاً در صفحه تنظیمات کلید خود را تنظیم کنید.
              </p>
            </div>
          </div>
        )}

        {/* LLM Error Banner */}
        {llmError && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">خطا در ارتباط با هوش مصنوعی</p>
              <p className="text-[11px] text-rose-700 mt-0.5">{llmError}</p>
            </div>
          </div>
        )}

        {/* AI Summary Card */}
        {llmSummary && (
          <div className="p-3.5 bg-indigo-50/70 border border-indigo-100 rounded-xl space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-900">
              <Wand2 className="w-4 h-4 text-indigo-600" />
              <span>ارزیابی کلی ویراستار هوش مصنوعی</span>
            </div>
            <p className="text-xs text-indigo-950 leading-relaxed">{llmSummary}</p>
            {aiLikelihoodNote && (
              <div className="text-[11px] text-indigo-800 bg-white/70 px-2.5 py-1.5 rounded-lg border border-indigo-100/50">
                <strong>نشانه‌های احتمالی ترجمه ماشینی:</strong> {aiLikelihoodNote}
              </div>
            )}
          </div>
        )}

        {/* Filters and Stats */}
        <div className="space-y-2">
          {/* Layer Filter Tabs */}
          <div className="flex gap-1.5 border-b border-slate-200 pb-2 text-xs">
            <button
              onClick={() => setActiveLayerFilter('all')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                activeLayerFilter === 'all'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              همه ({issues.length})
            </button>
            <button
              onClick={() => setActiveLayerFilter('local')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                activeLayerFilter === 'local'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              رسم‌الخط محلی ({localCount})
            </button>
            <button
              onClick={() => setActiveLayerFilter('llm')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                activeLayerFilter === 'llm'
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              نگارش هوش مصنوعی ({llmCount})
            </button>
          </div>

          {/* Category Chips */}
          {Object.keys(categories).length > 1 && (
            <div className="flex flex-wrap gap-1 text-[11px]">
              <button
                onClick={() => setActiveCategoryFilter('all')}
                className={`px-2 py-0.5 rounded-full transition-colors ${
                  activeCategoryFilter === 'all'
                    ? 'bg-slate-700 text-white font-medium'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                تمام دسته‌ها
              </button>
              {Object.entries(categories).map(([cat, count]) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategoryFilter(cat)}
                  className={`px-2 py-0.5 rounded-full transition-colors ${
                    activeCategoryFilter === cat
                      ? 'bg-blue-600 text-white font-medium'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {cat} ({count})
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Issues List */}
        <div className="space-y-2.5">
          {filteredIssues.length === 0 ? (
            <div className="text-center py-8 text-slate-400 bg-white rounded-xl border border-dashed border-slate-200">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
              <p className="font-medium text-slate-700 text-xs">
                {issues.length === 0 ? 'هیچ ایرادی یافت نشد (متن پاکیزه است).' : 'موردی با این فیلتر یافت نشد.'}
              </p>
            </div>
          ) : (
            filteredIssues.map((issue) => {
              const isAccepted = acceptedIssueIds.has(issue.id);
              const isRejected = rejectedIssueIds.has(issue.id);
              const isEditing = editingIssueId === issue.id;
              const currentSuggestion = customSuggestions[issue.id] ?? issue.suggestion;

              return (
                <div
                  key={issue.id}
                  className={`p-3 bg-white rounded-xl border transition-all ${
                    isAccepted
                      ? 'border-emerald-300 ring-1 ring-emerald-300/40 bg-emerald-50/20'
                      : isRejected
                      ? 'border-slate-200 opacity-60 bg-slate-50'
                      : issue.conflict
                      ? 'border-amber-200 bg-amber-50/30'
                      : 'border-slate-200 shadow-xs hover:border-slate-300'
                  }`}
                >
                  {/* Top info row */}
                  <div className="flex items-center justify-between text-[11px] mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          issue.severity === 'error'
                            ? 'bg-rose-500'
                            : issue.severity === 'warning'
                            ? 'bg-amber-500'
                            : 'bg-blue-500'
                        }`}
                      />
                      <span className="font-medium text-slate-700">{issue.category}</span>
                      <span className="text-[10px] text-slate-400">
                        ({issue.layer === 'local' ? 'محلی' : 'هوش مصنوعی'})
                      </span>
                    </div>

                    {issue.conflict && (
                      <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-medium">
                        تداخل با اصلاح مهم‌تر
                      </span>
                    )}

                    {isAccepted && (
                      <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-100 px-1.5 py-0.5 rounded">
                        تأیید شد
                      </span>
                    )}

                    {isRejected && (
                      <span className="text-[10px] text-slate-500 font-medium bg-slate-200 px-1.5 py-0.5 rounded">
                        رد شد
                      </span>
                    )}
                  </div>

                  {/* Diff representation */}
                  <div className="flex items-center gap-2 font-mono text-xs my-2 bg-slate-50 p-2 rounded-lg border border-slate-100">
                    <span className="line-through text-rose-600 bg-rose-50 px-1 rounded">
                      {issue.original || '(فاصله)'}
                    </span>
                    <span className="text-slate-400 font-sans">←</span>
                    {isEditing ? (
                      <input
                        type="text"
                        value={currentSuggestion}
                        onChange={(e) =>
                          setCustomSuggestions((prev) => ({
                            ...prev,
                            [issue.id]: e.target.value,
                          }))
                        }
                        className="bg-white px-1.5 py-0.5 border border-blue-400 rounded text-blue-700 text-xs focus:outline-hidden"
                        dir="auto"
                      />
                    ) : (
                      <span className="text-emerald-700 bg-emerald-50 px-1 rounded font-semibold">
                        {currentSuggestion || '(حذف)'}
                      </span>
                    )}
                  </div>

                  {/* Explanation */}
                  <p className="text-xs text-slate-600 leading-relaxed mb-2.5">
                    {issue.explanation}
                  </p>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                    <button
                      onClick={() =>
                        setEditingIssueId(isEditing ? null : issue.id)
                      }
                      className="text-[11px] text-slate-500 hover:text-slate-700 flex items-center gap-1"
                    >
                      <Edit2 className="w-3 h-3" />
                      <span>{isEditing ? 'تأیید ویرایش' : 'ویرایش پیشنهاد'}</span>
                    </button>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleRejectIssue(issue.id)}
                        className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                          isRejected
                            ? 'bg-slate-300 text-slate-800 font-semibold'
                            : 'text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>رد</span>
                      </button>

                      <button
                        onClick={() => handleAcceptIssue(issue.id)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs transition-colors ${
                          isAccepted
                            ? 'bg-emerald-600 text-white font-semibold'
                            : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>تأیید</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Footer / Copy Corrected Text */}
      <footer className="p-3 bg-white border-t border-slate-200 flex items-center justify-between sticky bottom-0 z-20">
        <div className="text-xs text-slate-500">
          <span>{acceptedIssueIds.size} مورد اعمال شده</span>
        </div>

        <button
          onClick={handleCopyCorrected}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            copied
              ? 'bg-emerald-600 text-white'
              : 'bg-slate-900 text-white hover:bg-slate-800 active:scale-98'
          }`}
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>کپی شد!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>کپی متن ویرایش‌شده</span>
            </>
          )}
        </button>
      </footer>
    </div>
  );
};
