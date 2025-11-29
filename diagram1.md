diagram 1

┌────────┐
│ Farmer │
└──┬─────┘
   │ Upload image
   ▼
┌────────────────────┐
│ Web App (Frontend) │
└──┬─────────────────┘
   │ POST /upload
   ▼
┌───────────────────────────────────────────────────────────────┐
│ Flask Backend                                                  │
│ ├─ Stage 1: YOLO COCO detection → forbidden zones              │
│ ├─ Stage 2: Bell pepper YOLO + shape/color/texture validation  │
│ ├─ Stage 3: CV quality analysis → ANFIS fallback               │
│ ├─ Stage 3C: Advanced AI (ripeness, shelf life, nutrition,     │
│ │          variety, market)                                    │
│ └─ Optional: Disease detection integration                     │
└──┬────────────────────────────────────────────────────────────┘
   │
   ├──────►┌────────────────────────┐
   │       │ SQLite Database        │
   │       │ AnalysisHistory,       │
   │       │ BellPepperDetection…   │
   │       └────────────────────────┘
   │
   ▼
┌──────────────────────────────┐
│ Annotated image + JSON reply │
└──┬───────────────────────────┘
   │ Display results
   ▼
┌────────┐
│ Farmer │
└────────┘


diagram 2

Farmer ──► Image Upload ──► Flask Upload Route
                                   │
                                   ▼
                    ┌───────────────────────────────────────────┐
                    │ Multi-Stage Detection & Analysis Pipeline │
                    │                                           │
                    │ 1. YOLO COCO Detection                    │
                    │    - Finds all objects                    │
                    │    - Marks forbidden zones                │
                    │                                           │
                    │ 2. Bell Pepper YOLO Detection             │
                    │    - Applies forbidden-zone filter        │
                    │    - Validates shape/color/texture        │
                    │                                           │
                    │ 3. Quality Analysis                       │
                    │    - CV Analyzer (color, size, surface,   │
                    │       ripeness)                           │
                    │    - ANFIS fallback                       │
                    │                                           │
                    │ 4. Advanced AI Analysis                   │
                    │    - Ripeness prediction                  │
                    │    - Shelf life estimation                │
                    │    - Nutritional analysis                 │
                    │    - Variety & market value               │
                    │                                           │
                    │ 5. Disease Detection (optional)           │
                    │    - Health score & recommendations       │
                    └───────────────────────────────────────────┘
                                   │
           ┌───────────────────────┼─────────────────────────┐
           │                       │                         │
           ▼                       ▼                         ▼
 SQLite Database            Annotated Result Image        JSON Response
 AnalysisHistory &          ──► Stored in results/        ──► Sent to frontend
 BellPepperDetection                                      (peppers, metrics,
 models                                                recommendations, stats)



 diagram 3

 Farmer ──► Upload Image ──► Flask Upload Route
                                   │
                                   ▼
                    ┌───────────────────────────────────────────┐
                    │ Detection & Analysis Pipeline             │
                    │  ├─ General YOLO (COCO) → forbidden zones │
                    │  ├─ Bell pepper YOLO + validation         │
                    │  ├─ Quality analysis (CV → ANFIS fallback)│
                    │  ├─ Advanced AI (ripeness, shelf, market) │
                    │  └─ Optional disease detection            │
                    └───────────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
 Annotated result image     SQLite database          JSON response
 (stored in results/)       (AnalysisHistory,        (detections, metrics,
                            BellPepperDetection…)    recommendations)