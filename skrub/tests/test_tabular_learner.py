import pytest
import sklearn
from sklearn import ensemble
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.utils.fixes import parse_version

from skrub import (
    GapEncoder,
    MinHashEncoder,
    TableVectorizer,
    ToCategorical,
    tabular_learner,
)


@pytest.mark.parametrize("learner_kind", ["regressor", "classifier"])
def test_default_pipeline(learner_kind):
    p = tabular_learner(learner_kind)
    tv, learner = [e for _, e in p.steps]
    assert isinstance(tv, TableVectorizer)
    assert isinstance(tv.high_cardinality_transformer, MinHashEncoder)
    if parse_version(sklearn.__version__) < parse_version("1.4"):
        assert isinstance(tv.low_cardinality_transformer, OrdinalEncoder)
    else:
        assert isinstance(tv.low_cardinality_transformer, ToCategorical)
        assert learner.categorical_features == "from_dtype"
    if learner_kind == "regressor":
        assert isinstance(learner, ensemble.HistGradientBoostingRegressor)
    else:
        assert isinstance(learner, ensemble.HistGradientBoostingClassifier)


def test_bad_learner():
    with pytest.raises(ValueError, match=".*should be 'regressor' or 'classifier'"):
        tabular_learner("bad")
    with pytest.raises(
        TypeError, match=".*Pass an instance of HistGradientBoostingRegressor"
    ):
        tabular_learner(ensemble.HistGradientBoostingRegressor)
    with pytest.raises(TypeError, match=".*expects a scikit-learn estimator"):
        tabular_learner(object())


def test_linear_learner():
    original_learner = Ridge()
    p = tabular_learner(original_learner)
    tv, imputer, learner = [e for _, e in p.steps]
    assert learner is original_learner
    assert isinstance(tv.high_cardinality_transformer, GapEncoder)
    assert isinstance(tv.low_cardinality_transformer, OneHotEncoder)
    assert isinstance(imputer, SimpleImputer)


def test_tree_learner():
    original_learner = ensemble.RandomForestClassifier()
    p = tabular_learner(original_learner)
    if parse_version(sklearn.__version__) < parse_version("1.4"):
        tv, impute, learner = [e for _, e in p.steps]
        assert isinstance(impute, SimpleImputer)
    else:
        tv, learner = [e for _, e in p.steps]
    assert learner is original_learner
    assert isinstance(tv.high_cardinality_transformer, MinHashEncoder)
    assert isinstance(tv.low_cardinality_transformer, OrdinalEncoder)


def test_from_dtype():
    p = tabular_learner(ensemble.HistGradientBoostingRegressor(categorical_features=()))
    assert isinstance(
        p.named_steps["tablevectorizer"].low_cardinality_transformer, OrdinalEncoder
    )
    if parse_version(sklearn.__version__) < parse_version("1.4"):
        return
    p = tabular_learner(
        ensemble.HistGradientBoostingRegressor(categorical_features="from_dtype")
    )
    assert isinstance(
        p.named_steps["tablevectorizer"].low_cardinality_transformer, ToCategorical
    )