# Final-v3 Confidence Revalidation

## 1. Purpose
Apply the existing 0.6 / 0.3 top-label probability policy to final-v3 without threshold tuning or calibration fitting.

## 2. Model and data
- Model role: `CURRENT_EXECUTABLE_BASELINE`
- Model: `modeling/03_word_char_tfidf/artifacts/best_word_char_model.joblib`
- Data: `out/event_features_integrated_v3.csv`
- Validation / Test: 1,338 / 1,042
- Feature reconstruction: stored Word transform + stored Character transform x 1.0

## 3. Confidence definition
`confidence = max(classifier.predict_proba(X))`. This is not the Day13 top1-top2 margin.

- HIGH: confidence >= 0.6
- MEDIUM: 0.3 <= confidence < 0.6
- LOW: confidence < 0.3

## 4. Validation results
| split | confidence_level | n | coverage | accuracy | mean_confidence | confidence_accuracy_gap | top3_hit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VALIDATION | HIGH | 178 | 0.133034 | 0.741573 | 0.725805 | -0.015768 | 0.915730 |
| VALIDATION | MEDIUM | 995 | 0.743647 | 0.469347 | 0.417361 | -0.051986 | 0.886432 |
| VALIDATION | LOW | 165 | 0.123318 | 0.400000 | 0.268152 | -0.131848 | 0.775758 |

## 5. Test results
| split | confidence_level | n | coverage | accuracy | mean_confidence | confidence_accuracy_gap | top3_hit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TEST | HIGH | 193 | 0.185221 | 0.761658 | 0.713186 | -0.048472 | 0.953368 |
| TEST | MEDIUM | 716 | 0.687140 | 0.472067 | 0.418613 | -0.053454 | 0.907821 |
| TEST | LOW | 133 | 0.127639 | 0.308271 | 0.265707 | -0.042564 | 0.774436 |

## 6. Coverage-Accuracy Trade-off
- Validation ordering HIGH > MEDIUM > LOW: **True**
- Test ordering HIGH > MEDIUM > LOW: **True**
- Overall confidence ordering: **PASS**
- HIGH coverage is reported descriptively; thresholds were not adjusted from Test results.
- LOW Test Top-3 Hit Rate: 0.774436

## 7. Calibration
- Test mean top-label confidence: 0.453657
- Test accuracy: 0.504798
- ECE (10 equal-width bins): 0.052235
- Top-label Brier: 0.232429; definition: `mean((top1_confidence - correct)^2)`
- Multiclass Brier: 0.628829; definition: `mean(sum_k((p_k - y_k)^2))`

| bin | lower_bound | upper_bound | n | coverage | mean_confidence | accuracy | calibration_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [0.0,0.1) | 0.000000 | 0.100000 | 0 | 0.000000 | NA | NA | NA |
| [0.1,0.2) | 0.100000 | 0.200000 | 3 | 0.002879 | 0.194896 | 0.333333 | -0.138437 |
| [0.2,0.3) | 0.200000 | 0.300000 | 130 | 0.124760 | 0.267341 | 0.307692 | -0.040352 |
| [0.3,0.4) | 0.300000 | 0.400000 | 342 | 0.328215 | 0.350713 | 0.438596 | -0.087883 |
| [0.4,0.5) | 0.400000 | 0.500000 | 241 | 0.231286 | 0.447009 | 0.460581 | -0.013572 |
| [0.5,0.6) | 0.500000 | 0.600000 | 133 | 0.127639 | 0.541757 | 0.578947 | -0.037191 |
| [0.6,0.7) | 0.600000 | 0.700000 | 97 | 0.093090 | 0.645179 | 0.659794 | -0.014614 |
| [0.7,0.8) | 0.700000 | 0.800000 | 61 | 0.058541 | 0.745785 | 0.885246 | -0.139461 |
| [0.8,0.9) | 0.800000 | 0.900000 | 35 | 0.033589 | 0.844844 | 0.828571 | 0.016272 |
| [0.9,1.0] | 0.900000 | 1.000000 | 0 | 0.000000 | NA | NA | NA |

## 8. Human Factor
The Test support is 27; results are descriptive only.

| root_cause | confidence_level | support | n | coverage | mean_confidence | top1_accuracy | top3_hit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 인적요인 | ALL | 27 | 27 | 1.000000 | 0.411831 | 0.074074 | 0.444444 |
| 인적요인 | HIGH | 27 | 4 | 0.148148 | 0.671939 | 0.000000 | 0.250000 |
| 인적요인 | MEDIUM | 27 | 16 | 0.592593 | 0.410732 | 0.062500 | 0.437500 |
| 인적요인 | LOW | 27 | 7 | 0.259259 | 0.265712 | 0.142857 | 0.571429 |

## 9. Historical results separation
Historical Synthetic policy reference:

| confidence_level | coverage | accuracy |
| --- | --- | --- |
| HIGH | 0.118000 | 0.790000 |
| MEDIUM | 0.650000 | 0.506000 |
| LOW | 0.232000 | 0.348000 |

Historical ECE: 0.094. It belongs to a different model/snapshot and is not used for direct better/worse comparison.

## 10. Operational interpretation
Confidence levels are treated as case-difficulty and QA-prioritization signals, not literal probabilities of correctness. Numeric confidence should not be emphasized as a calibrated correctness probability. No hard automation decision follows from these levels.

## 11. Conclusion
Status: **PROVISIONAL_VALIDATED**. Confidence ordering: **PASS**.

No model retraining, vectorizer fitting, threshold tuning, calibration model fitting, Test-based policy change, Retrieval execution, or Historical Synthetic result change was performed.
