\# Sprint 02 Planning: Flutter Mobile \& Edge Biomechanics Integration



\- \*\*Sprint Goal:\*\* اجرای اپلیکیشن فلاتر روی موبایل، دریافت استریم زنده دوربین (۳۰+ فریم)، رسم اسکلت بدن و اعمال فیلتر زمانی برای رساندن دقت به ۱۰۰٪.

\- \*\*Duration:\*\* ۲ هفته (سپتامبر تا اکتبر ۲۰۲۶)



\---



\## 1. Team Backlog \& Ownership



| Task ID | Component | Owner | Deliverable | Acceptance Criteria (DoD) |

| :--- | :--- | :--- | :--- | :--- |

| \*\*TSK-201\*\* | Mobile Base | آرش | `mobile/lib/` | استریم روان دوربین با نرخ ۳۰ FPS بدون افت فریم |

| \*\*TSK-202\*\* | Kinematics Smoothing | کامران | `src/biomechanics/` | افزودن فیلتر زمانی ۳ فریمی جهت رفع فالس‌پازیتیو `valid\_04` و `valid\_05` |

| \*\*TSK-203\*\* | Bridge / FFI | دانی | `src/bridge/` | پاس دادن فریم‌های دوربین فلاتر به هسته استخراج لندمارک |

| \*\*TSK-204\*\* | UI / Audio Cues | حسام | `mobile/ui/` | رندر باکس خطا و پخش صدای بیپ/پیام اصلاحی هنگام رخ دادن `HIP\_SAG` |

| \*\*TSK-205\*\* | QA Benchmarking | محمد و مهرناز | `tests/benchmarks/` | ضبط و تست ۱۰ کلیپ در شرایط نوری ضعیف و زوایای مایل (۴۵ درجه) |

