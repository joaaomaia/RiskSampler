#!/bin/bash
mkdir -p tests/test_results

pytest -vv --tb=long tests/unit/test_risksampler.py                     > tests/test_results/test_risksampler.txt
#pytest -vv --tb=long src/vassoura/tests/test_report.py             > src/vassoura/tests/test_results/test_report.txt
#pytest -vv --tb=long src/vassoura/tests/test_sampler.py            > src/vassoura/tests/test_results/test_sampler.txt


# pytest -vv --tb=long src/vassoura/tests/test_audit.py              > src/vassoura/tests/test_results/test_audit.txt
# pytest -vv --tb=long src/vassoura/tests/test_audit_extra.py        > src/vassoura/tests/test_results/test_audit_extra.txt
# pytest -vv --tb=long src/vassoura/tests/test_encoders_pipeline.py  > src/vassoura/tests/test_results/test_encoders_pipeline.txt
# pytest -vv --tb=long src/vassoura/tests/test_encoders_unit.py      > src/vassoura/tests/test_results/test_encoders_unit.txt
# pytest -vv --tb=long src/vassoura/tests/test_importance.py         > src/vassoura/tests/test_results/test_importance.txt
# pytest -vv --tb=long src/vassoura/tests/test_metrics.py            > src/vassoura/tests/test_results/test_metrics.txt
# pytest -vv --tb=long src/vassoura/tests/test_models.py             > src/vassoura/tests/test_results/test_models.txt
# pytest -vv --tb=long src/vassoura/tests/test_sampler_property.py   > src/vassoura/tests/test_results/test_sampler_property.txt
# pytest -vv --tb=long src/vassoura/tests/test_scaler.py             > src/vassoura/tests/test_results/test_scaler.txt
# pytest -vv --tb=long src/vassoura/tests/test_scaler_property.py    > src/vassoura/tests/test_results/test_scaler_property.txt
# pytest -vv --tb=long src/vassoura/tests/test_validation.py         > src/vassoura/tests/test_results/test_validation.txt

