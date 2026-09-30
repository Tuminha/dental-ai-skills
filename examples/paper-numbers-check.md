# Paper Numbers Check

Start with the existing offline calculator, not a new service. No API key is needed.
From the repository root:

```bash
python3 dental-statistical-forensics/scripts/stats_forensics_calculator.py continuous \
  --mean-a 2 --sd-a 1 --n-a 20 --mean-b 1 --sd-b 1 --n-b 20
```

This invented example has a mean difference of 1 unit. The approximate interval
describes uncertainty around a group difference; it does not show how predictable
the response is for an individual. These are independent groups. Do not apply this
calculation unchanged to paired teeth, split-mouth designs or clustered implants.

Provide the JSON output and the paper to `dental-statistical-forensics` to check
the design assumptions and whether the paper's claim follows. Read the helper's
limitations before interpreting its calculations. A clinical threshold must come
from the relevant clinical context, not be invented to make a result look important.

Next product step: test this workflow with the journal-club volunteers. Build a
separate web interface only if repeated use demonstrates that copying numbers into
the command is the actual obstacle.
