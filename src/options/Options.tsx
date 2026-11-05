/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import {
  Save,
  RotateCcw,
  Shield,
  Key,
  Sliders,
  Sparkles,
  CheckCircle,
  HelpCircle,
  Plus,
  Trash2,
} from 'lucide-react';
import { ExtensionSettings, DEFAULT_SETTINGS, LLMProvider } from '../shared/types.ts';
import { loadSettings, saveSettings } from '../shared/storage.ts';
import { DEFAULT_REVIEW_SYSTEM_PROMPT } from '../core/llm/reviewPrompt.ts';

interface OptionsProps {
  onBack?: () => void;
}

export const Options: React.FC<OptionsProps> = ({ onBack }) => {
  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS);
  const [newDisabledDomain, setNewDisabledDomain] = useState<string>('');
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'normalizer' | 'llm' | 'privacy'>('normalizer');

  useEffect(() => {
    loadSettings().then(setSettings);
  }, []);

  const handleSave = async () => {
    await saveSettings(settings);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2500);
  };

  const handleResetPrompt = () => {
    setSettings((prev) => ({
      ...prev,
      llm: {
        ...prev.llm,
        customReviewPrompt: DEFAULT_REVIEW_SYSTEM_PROMPT,
      },
    }));
  };

  const addDisabledDomain = () => {
    if (!newDisabledDomain.trim()) return;
    const clean = newDisabledDomain.trim().toLowerCase();
    if (!settings.disabledSites.includes(clean)) {
      setSettings((prev) => ({
        ...prev,
        disabledSites: [...prev.disabledSites, clean],
      }));
    }
    setNewDisabledDomain('');
  };

  const removeDisabledDomain = (domain: string) => {
    setSettings((prev) => ({
      ...prev,
      disabledSites: prev.disabledSites.filter((d) => d !== domain),
    }));
  };

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 font-sans text-slate-800" dir="rtl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md">
            ف
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">تنظیمات فارسی‌لینت</h1>
            <p className="text-xs text-slate-500">پیکربندی قوانین رسم‌الخط، هوش مصنوعی و حریم خصوصی</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onBack && (
            <button
              onClick={onBack}
              className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              بازگشت به ویراستار
            </button>
          )}

          <button
            onClick={handleSave}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold shadow-xs transition-all ${
              isSaved
                ? 'bg-emerald-600 text-white'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-98'
            }`}
          >
            {isSaved ? (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>ذخیره شد!</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>ذخیره تغییرات</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 my-6 border-b border-slate-200 text-xs font-medium">
        <button
          onClick={() => setActiveTab('normalizer')}
          className={`flex items-center gap-1.5 pb-2.5 px-2 border-b-2 transition-colors ${
            activeTab === 'normalizer'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>قوانین رسم‌الخط محلی</span>
        </button>

        <button
          onClick={() => setActiveTab('llm')}
          className={`flex items-center gap-1.5 pb-2.5 px-2 border-b-2 transition-colors ${
            activeTab === 'llm'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>تنظیمات مدل هوش مصنوعی</span>
        </button>

        <button
          onClick={() => setActiveTab('privacy')}
          className={`flex items-center gap-1.5 pb-2.5 px-2 border-b-2 transition-colors ${
            activeTab === 'privacy'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>حریم خصوصی و سایت‌ها</span>
        </button>
      </div>

      {/* Tab 1: Normalizer Rules */}
      {activeTab === 'normalizer' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b pb-2">
              قوانین رسم‌الخط و تایپوگرافی فارسی (آفلاین و بلادرنگ)
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Arabic chars */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.arabicChars}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, arabicChars: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">تبدیل حروف عربی (ي / ك)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    تبدیل «ي» و «ك» و «ى» عربی به «ی» و «ک» استاندارد فارسی
                  </div>
                </div>
              </label>

              {/* Digits */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.persianDigits}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, persianDigits: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">اعداد فارسی (۰ تا ۹)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    تبدیل ارقام انگلیسی و عربی به فارسی (کدها، آدرس‌ها و واژگان انگلیسی حفظ می‌شوند)
                  </div>
                </div>
              </label>

              {/* ZWNJ */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.zwnjAffixes}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, zwnjAffixes: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">نیم‌فاصله‌گذاری پیشوندها و پسوندها</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    می/نمی، ها/های، تر/ترین، و پسوندهای فعلی بعد از ه (رفته‌ام، دیده‌ای)
                  </div>
                </div>
              </label>

              {/* Redundant space & ZWNJ */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.cleanZwnjAndSpaces}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, cleanZwnjAndSpaces: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">پاکسازی فواصل و نیم‌فاصله‌های زائد</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    حذف نیم‌فاصله در کنار فاصله و تبدیل چندین فاصله متوالی به یک فاصله
                  </div>
                </div>
              </label>

              {/* Punctuation */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.punctuationMarks}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, punctuationMarks: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">نشانه‌گذاری فارسی (، ؛ ؟) و فاصله‌گذاری</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    تبدیل ویرگول و علامت سوال به فارسی و رعایت فاصله بعد از نشانه
                  </div>
                </div>
              </label>

              {/* Quotes & Brackets */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.quotesAndBrackets}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, quotesAndBrackets: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">گیومه فارسی و پرانتزها (« »)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    تبدیل نقل‌قول انگلیسی به گیومه فارسی و حذف فاصله داخل پرانتزها
                  </div>
                </div>
              </label>

              {/* Kashida & Ellipsis */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.kashidaAndEllipsis}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, kashidaAndEllipsis: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">حذف کشیدگی حروف و سه‌نقطه استاندارد</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    تبدیل ... به نشانه سه‌نقطه (…)، و حذف کشیدگی غیرضروری (ـ)
                  </div>
                </div>
              </label>

              {/* Ezafe Rule */}
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.normalizer.ezafeRule}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      normalizer: { ...prev.normalizer, ezafeRule: e.target.checked },
                    }))
                  }
                  className="mt-1 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-semibold text-xs text-slate-800">اصلاح کسره اضافه بعد از «ه»</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    اصلاح ترکیب‌هایی مانند «خانه ی من»
                  </div>
                </div>
              </label>
            </div>

            {/* Ezafe style selector */}
            {settings.normalizer.ezafeRule && (
              <div className="mt-4 p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="text-xs font-semibold text-slate-800 mb-2">شیوه نگارش کسره اضافه بعد از «ه»:</div>
                <div className="flex gap-6 text-xs">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="ezafeStyle"
                      value="hamza"
                      checked={settings.normalizer.ezafeStyle === 'hamza'}
                      onChange={() =>
                        setSettings((prev) => ({
                          ...prev,
                          normalizer: { ...prev.normalizer, ezafeStyle: 'hamza' },
                        }))
                      }
                      className="text-blue-600"
                    />
                    <span>همزه بر سر ه (مانند: خانهٔ بزرگ)</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="ezafeStyle"
                      value="ye"
                      checked={settings.normalizer.ezafeStyle === 'ye'}
                      onChange={() =>
                        setSettings((prev) => ({
                          ...prev,
                          normalizer: { ...prev.normalizer, ezafeStyle: 'ye' },
                        }))
                      }
                      className="text-blue-600"
                    />
                    <span>یای با نیم‌فاصله (مانند: خانه‌ی بزرگ)</span>
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: LLM Settings */}
      {activeTab === 'llm' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b pb-2 flex items-center gap-2">
              <Key className="w-4 h-4 text-blue-600" />
              <span>پیکربندی هوش مصنوعی برای بازبینی نگارش فارسی</span>
            </h2>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800">
              کلید اختصاصی شما فقط در حافظه محلی مرورگر (Local Storage) ذخیره می‌شود و هرگز به سرور دیگری ارسال نمی‌گردد.
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Provider Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  سرویس‌دهنده هوش مصنوعی:
                </label>
                <select
                  value={settings.llm.provider}
                  onChange={(e) => {
                    const prov = e.target.value as LLMProvider;
                    let defaultModel = 'gemini-2.5-flash';
                    if (prov === 'anthropic') defaultModel = 'claude-3-5-sonnet-20241022';
                    if (prov === 'openai') defaultModel = 'gpt-4o-mini';
                    if (prov === 'openrouter') defaultModel = 'anthropic/claude-3.5-sonnet';
                    if (prov === 'custom') defaultModel = 'llama3.3:70b';

                    setSettings((prev) => ({
                      ...prev,
                      llm: { ...prev.llm, provider: prov, model: defaultModel },
                    }));
                  }}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:border-blue-500"
                >
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                  <option value="anthropic">Anthropic Claude</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="custom">مدل محلی یا سازگار با OpenAI (Ollama / LM Studio)</option>
                </select>
              </div>

              {/* Model Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  نام مدل (Model Name):
                </label>
                <input
                  type="text"
                  value={settings.llm.model}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      llm: { ...prev.llm, model: e.target.value },
                    }))
                  }
                  placeholder="مثال: gpt-4o, claude-3-5-sonnet-20241022, gemini-2.5-flash"
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:border-blue-500 font-mono text-left"
                  dir="ltr"
                />
              </div>
            </div>

            {/* API Key */}
            {settings.llm.provider !== 'custom' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  کلید دسترسی (API Key):
                </label>
                <input
                  type="password"
                  value={settings.llm.apiKey}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      llm: { ...prev.llm, apiKey: e.target.value },
                    }))
                  }
                  placeholder="کلید API خود را وارد کنید..."
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:border-blue-500 font-mono text-left"
                  dir="ltr"
                />
              </div>
            )}

            {/* Custom Endpoint */}
            {settings.llm.provider === 'custom' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  آدرس سرور سازگار با OpenAI (Endpoint URL):
                </label>
                <input
                  type="text"
                  value={settings.llm.customEndpoint || ''}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      llm: { ...prev.llm, customEndpoint: e.target.value },
                    }))
                  }
                  placeholder="http://localhost:11434/v1/chat/completions"
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:border-blue-500 font-mono text-left"
                  dir="ltr"
                />
              </div>
            )}

            {/* Review System Prompt Editor */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  پرامپت سیستمی بازبینی (System Prompt):
                </label>
                <button
                  onClick={handleResetPrompt}
                  className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>بازنشانی به پیش‌فرض</span>
                </button>
              </div>
              <textarea
                value={settings.llm.customReviewPrompt || DEFAULT_REVIEW_SYSTEM_PROMPT}
                onChange={(e) =>
                  setSettings((prev) => ({
                    ...prev,
                    llm: { ...prev.llm, customReviewPrompt: e.target.value },
                  }))
                }
                rows={7}
                className="w-full text-xs p-2.5 bg-slate-900 text-slate-100 rounded-xl font-mono text-left focus:outline-hidden"
                dir="ltr"
              />
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Privacy & Site Blacklist */}
      {activeTab === 'privacy' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b pb-2 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-600" />
              <span>تنظیمات حریم خصوصی و فهرست غیرفعال‌سازی</span>
            </h2>

            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autoUnderline}
                  onChange={(e) =>
                    setSettings((prev) => ({ ...prev, autoUnderline: e.target.checked }))
                  }
                  className="rounded text-blue-600"
                />
                <span className="text-xs text-slate-700 font-medium">
                  نمایش خطوط موج‌دار قرمز/نارنجی/آبی در فیلدهای متنی صفحات وب (بدون ارسال به اینترنت)
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.floatingButton}
                  onChange={(e) =>
                    setSettings((prev) => ({ ...prev, floatingButton: e.target.checked }))
                  }
                  className="rounded text-blue-600"
                />
                <span className="text-xs text-slate-700 font-medium">
                  نمایش دکمه شناور بازبینی در فیلدهایی با بیش از ۳۰٪ نویسه فارسی
                </span>
              </label>
            </div>

            {/* Blacklist */}
            <div className="pt-4 border-t border-slate-100">
              <div className="text-xs font-semibold text-slate-800 mb-1">
                سایت‌ها و دامنه‌های غیرفعال (Disabled Sites):
              </div>
              <p className="text-[11px] text-slate-500 mb-3">
                افزونه در فیلدهای رمز عبور و بانکی به طور خودکار غیرفعال است. می‌توانید دامنه‌های مورد نظر خود را نیز اضافه کنید:
              </p>

              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={newDisabledDomain}
                  onChange={(e) => setNewDisabledDomain(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addDisabledDomain()}
                  placeholder="مثال: bank.com یا myportal"
                  className="flex-1 text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg text-left font-mono"
                  dir="ltr"
                />
                <button
                  onClick={addDisabledDomain}
                  className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium flex items-center gap-1 hover:bg-slate-800"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>افزودن</span>
                </button>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {settings.disabledSites.map((domain) => (
                  <span
                    key={domain}
                    className="flex items-center gap-1.5 bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded-full border border-slate-200 font-mono"
                  >
                    <span>{domain}</span>
                    <button
                      onClick={() => removeDisabledDomain(domain)}
                      className="text-slate-400 hover:text-rose-600"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
