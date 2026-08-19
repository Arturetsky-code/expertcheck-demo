import core.pipeline as pipeline
from core.project_understanding import build_project_object_model, understanding_quality

def test_pipeline_has_project_understanding_symbols():
    assert pipeline.build_project_object_model is build_project_object_model
    assert pipeline.understanding_quality is understanding_quality

def test_project_understanding_empty_model_safe():
    model=build_project_object_model([],[])
    q=understanding_quality(model)
    assert model['objects']==[]
    assert q['objects']==0
    assert q['unresolved_properties']==0
