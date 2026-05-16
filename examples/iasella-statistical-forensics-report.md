# Iasella 2003 Ridge Preservation: Statistical Forensics

This is a compact example output for the `dental-statistical-forensics` and `dental-evidence-report-artifact` workflow.

## Verdict

The paper supports a favorable average effect for ridge preservation, but the SDs, ranges, small sample, and missing histology data make claims of predictable esthetic-zone maintenance too strong.

## Key Numerical Flags

| Finding | Interpretation |
|---|---|
| RP horizontal change: -1.2 +/- 0.9 mm | Average benefit with moderate residual variability. |
| EXT horizontal change: -2.6 +/- 2.3 mm | Extraction alone varied widely. |
| RP mid-buccal vertical change: +1.3 +/- 2.0 mm | SD exceeds mean gain; individual predictability is limited. |
| RP mid-buccal range: -2.0 to +4.5 mm | Some preserved sites still lost buccal height. |
| Approx horizontal CI: about -0.1 to +2.9 mm | Horizontal effect estimate is imprecise. |

## Clinical Interpretation

Ridge preservation appears to reduce average collapse, but it should be interpreted as risk reduction rather than guaranteed preservation. In esthetic-zone planning, the paper does not remove the need for patient-specific augmentation planning.

## Artifact Workflow

The example JSON at `examples/iasella-statistical-forensics-report-data.json` can be rendered with:

```bash
python dental-evidence-report-artifact/scripts/render_evidence_report.py \
  --input examples/iasella-statistical-forensics-report-data.json \
  --output examples/iasella-statistical-forensics-report.html
```
